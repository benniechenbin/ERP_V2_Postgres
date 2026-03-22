from datetime import datetime
import pandas as pd

from backend.config import config_manager as cfg
from backend.database.db_engine import get_connection
from backend.database.schema import get_all_data_tables, has_column
from backend.database.crud_base import upsert_dynamic_record  # 🟢 内部调用基础引擎
from backend.core.finance_engine import validate_sub_payment_risk
from backend.utils.logger import sys_logger


# ==========================================
# 🛡️ 业财风控拦截网关
# ==========================================
def check_main_contract_clearance(main_contract_code: str) -> tuple[bool, str]:
    """
    [V2.6 强制类型适配版] 
    解决 PostgreSQL 中 VARCHAR 与 NUMERIC 的运算冲突
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 🟢 修正点：使用 CAST 或 ::numeric 将字符类型的 sub_amount 转换为数值
            # 🟢 修正点：book_main_code 同样进行类型对齐
            sql = """
                SELECT 
                    s.biz_code, 
                    s.sub_company_name, 
                    COALESCE(NULLIF(s.sub_amount, '')::numeric, 0) as sub_amt,
                    COALESCE(p.paid_sum, 0) as paid_sum
                FROM biz_sub_contracts s
                LEFT JOIN (
                    SELECT sub_contract_code, SUM(payment_amount) as paid_sum 
                    FROM biz_outbound_payments 
                    WHERE deleted_at IS NULL 
                    GROUP BY sub_contract_code
                ) p ON s.biz_code = p.sub_contract_code
                WHERE s.book_main_code = %s 
                  AND s.deleted_at IS NULL
                  AND (COALESCE(NULLIF(s.sub_amount, '')::numeric, 0) - COALESCE(p.paid_sum, 0)) > 0.01
            """
            cursor.execute(sql, (str(main_contract_code),))
            uncleared_subs = cursor.fetchall()
            
            if uncleared_subs:
                error_details = []
                for sub in uncleared_subs:
                    # sub[2] 是转换后的金额, sub[3] 是已付金额
                    diff = float(sub[2] or 0) - float(sub[3] or 0)
                    error_details.append(f"[{sub[0]}] {sub[1]} (差额: ¥{diff:,.2f})")
                return False, f"操作拦截：名下有分包未结清：\n" + "\n".join(error_details)
                
            return True, "检查通过"
    except Exception as e:
        return False, f"业财校验引擎异常: {e}"
    finally:
        if conn: conn.close()


# ==========================================
# 💼 财务核心业务流转
# ==========================================
def mark_project_as_accrued(model_name: str, biz_code: str):
    """
    [V2.0 适配版] 将项目标记为已计提，并精准打上时间戳
    注意：参数已从 table_name 升级为 model_name (如 'project')
    """
    # 🚨 1. 第一道防线：呼叫计提风控依赖检查！
    passed, msg = check_main_contract_clearance(biz_code)
    if not passed:
        return False, msg # 🟢 直接打回，不允许执行计提
        
    # 2. 瞬间生成时间戳与状态字典
    patch_dict = {
        "is_provisioned": "是",
        "provision_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 🟢 补齐计提时间！
    }
    
    model_config = cfg.get_model_config(model_name)
    table_name = model_config.get("table_name")
    if not table_name: 
        return False, "未找到模型配置"
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 3. 通过 biz_code 查出底层真实的物理 id
        cursor.execute(f'SELECT id FROM "{table_name}" WHERE biz_code = %s', (biz_code,))
        row = cursor.fetchone()
        
        if not row:
            return False, f"找不到编号为 {biz_code} 的记录"
            
        record_id = row[0]
        
        # 4. 🟢 呼叫智能引擎安全保存！
        return upsert_dynamic_record(model_name=model_name, data_dict=patch_dict, record_id=record_id)
        
    except Exception as e:
        return False, f"计提操作失败: {e}"
    finally:
        if conn: conn.close()


def execute_yearly_accrual_archive():
    """执行年度结转 (PG JSONB 语法兼容适配)"""
    conn = None
    try:
        conn = get_connection()
        tables = get_all_data_tables()
        archived_count = 0
        
        for tbl in tables:
            if not has_column(tbl, "is_provisioned"):
                continue
            # 🟢 PG 中对 JSONB 的模糊查询通常用 ::text 转换
            sql = f"""
                UPDATE "{tbl}"
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE is_provisioned = '是'
            """
            cur = conn.cursor()
            cur.execute(sql)
            archived_count += cur.rowcount
            
        conn.commit()
        return True, f"年度结转完成！共将 {archived_count} 个已计提项目移入回收站。"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()


def submit_sub_payment(sub_biz_code: str, payment_amount: float, operator: str, payment_date: str, remarks: str = ""):
    """
    [V2.0 业财安全支付网关] 前端点击“确认付款”时调用的唯一接口
    """
    conn = None
    try:
        conn = get_connection()
        
        # 1. 🚨 把当前连接传给风控引擎，锁定该行！
        passed, msg = validate_sub_payment_risk(sub_biz_code, payment_amount, conn=conn)
        if not passed:
            conn.rollback() # 风控不通过，释放锁
            sys_logger.warning(f"⛔ 付款被风控拦截 [{sub_biz_code}]: {msg}")
            return False, msg  
            
        # 2. 风控通过，安全落库
        cursor = conn.cursor()
        sql = """
            INSERT INTO biz_outbound_payments 
            (biz_code, sub_contract_code, payment_amount, payment_date, operator, remarks)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        pay_flow_code = f"PAY-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S%f')}"
        cursor.execute(sql, (pay_flow_code, sub_biz_code, payment_amount, payment_date, operator, remarks))
        
        # 3. 统一提交事务！
        conn.commit()
        sys_logger.info(f"✅ 分包付款成功落库 [{pay_flow_code}] 金额: {payment_amount}")
        return True, "✅ 支付记录已安全入库！"
        
    except Exception as e:
        if conn: conn.rollback()
        sys_logger.error(f"🚨 付款落库失败 [{sub_biz_code}]: {e}", exc_info=True)
        return False, f"落库失败: {e}"
    finally:
        if conn: conn.close()

def sync_main_contract_finance(main_contract_code: str):
    """
    [V2.7 穿透核算引擎] 
    直接从收款/发票表抓取数据，强制同步到主合同的统计字段中。
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 1. 实时计算：累计到账 (来自 biz_collections)
            cursor.execute("""
                SELECT COALESCE(SUM(collected_amount), 0) 
                FROM biz_collections 
                WHERE main_contract_code = %s AND deleted_at IS NULL
            """, (main_contract_code,))
            total_collected = float(cursor.fetchone()[0] or 0)

            # 2. 实时计算：累计开票 (来自 biz_invoices)
            cursor.execute("""
                SELECT COALESCE(SUM(invoice_amount), 0) 
                FROM biz_invoices 
                WHERE main_contract_code = %s AND deleted_at IS NULL
            """, (main_contract_code,))
            total_invoiced = float(cursor.fetchone()[0] or 0)

            # 3. 获取合同总额用于计算进度 (注意类型转换)
            # 这里的表名从配置获取，或者直接用 biz_main_contracts
            cursor.execute("""
                SELECT COALESCE(NULLIF(contract_amount, '')::numeric, 0) 
                FROM biz_main_contracts 
                WHERE biz_code = %s
            """, (main_contract_code,))
            contract_amount = float(cursor.fetchone()[0] or 0)

            # 4. 计算进度与欠款
            progress = round((total_collected / contract_amount * 100), 2) if contract_amount > 0 else 0
            uncollected = contract_amount - total_collected

            # 5. 执行更新 (更新到动态属性字段)
            update_sql = """
                UPDATE biz_main_contracts 
                SET total_collected = %s, 
                    total_invoiced = %s,
                    collection_progress = %s,
                    uncollected_contract_amount = %s
                WHERE biz_code = %s
            """
            cursor.execute(update_sql, (total_collected, total_invoiced, progress, uncollected, main_contract_code))
            
        conn.commit()
        return True, "财务数据同步完成"
    except Exception as e:
        if conn: conn.rollback()
        return False, f"同步失败: {e}"
    finally:
        if conn: conn.close()

def void_financial_record(record_code, record_type, operator):
    """
    [V2.0 通用财务作废引擎] 执行财务流水的软删除与审计留痕
    """
    # 动态映射表名
    table_map = {
        "collections": "biz_collections",
        "invoices": "biz_invoices",
        "sub_payments": "biz_outbound_payments" # 预留给明天的分包付款
    }
    table_name = table_map.get(record_type)
    if not table_name:
        return False, f"未知的记录类型: {record_type}"

    sql = f"""
        UPDATE {table_name} 
        SET deleted_at = CURRENT_TIMESTAMP,
            remarks = CONCAT(COALESCE(remarks, ''), ' [🔴 已由 ', %s, ' 作废]')
        WHERE biz_code = %s AND deleted_at IS NULL
    """
    # 直接调用你 db_engine 里的工具函数
    from .db_engine import execute_raw_sql
    success, msg = execute_raw_sql(sql, (operator, record_code))
    
    return success, "作废成功" if success else f"作废失败: {msg}"