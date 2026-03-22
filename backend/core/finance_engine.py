import pandas as pd
import psycopg2.extras
from backend.database.db_engine import get_connection
from backend.utils.logger import sys_logger # 顺手注入 logger


# ==========================================
# ⚙️ 引擎一：主合同水池核算 (已修复 Decimal 与重名问题)
# ==========================================
def enrich_main_contract_stats(df_main: pd.DataFrame) -> pd.DataFrame:
    if df_main.empty or 'biz_code' not in df_main.columns:
        return df_main
        
    conn = get_connection()
    try:
        # 🟢 1. 清洗主表编号：防止空格导致 merge 失败产生 None
        df_main['biz_code'] = df_main['biz_code'].astype(str).str.strip()
        biz_codes = df_main['biz_code'].tolist()
        params = tuple(biz_codes)
        placeholders = ', '.join(['%s'] * len(biz_codes))

        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 2. 抓取发票池
        sql_inv = f"""
            SELECT main_contract_code as biz_code, SUM(invoice_amount) as total_invoiced
            FROM biz_invoices 
            WHERE main_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY main_contract_code
        """
        cur.execute(sql_inv, params)
        df_inv = pd.DataFrame(cur.fetchall())
        if not df_inv.empty:
            # 🟢 2a. 强转 float 并清洗编号，解决 Decimal 无法计算问题
            df_inv['total_invoiced'] = df_inv['total_invoiced'].astype(float)
            df_inv['biz_code'] = df_inv['biz_code'].astype(str).str.strip()

        # 3. 抓取资金池
        sql_coll = f"""
            SELECT main_contract_code as biz_code, SUM(collected_amount) as total_collected
            FROM biz_collections
            WHERE main_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY main_contract_code
        """
        cur.execute(sql_coll, params)
        df_coll = pd.DataFrame(cur.fetchall())
        if not df_coll.empty:
            # 🟢 3a. 强转 float 并清洗编号
            df_coll['total_collected'] = df_coll['total_collected'].astype(float)
            df_coll['biz_code'] = df_coll['biz_code'].astype(str).str.strip()

        # 🟢 4. 关键：清理主表已存在的重名虚拟列，防止 merge 产生后缀导致公式找不到变量
        v_cols = ['total_invoiced', 'total_collected']
        df_main = df_main.drop(columns=[c for c in v_cols if c in df_main.columns])

        # 5. 执行合并
        if not df_inv.empty:
            df_main = df_main.merge(df_inv, on='biz_code', how='left')
        else:
            df_main['total_invoiced'] = 0.0

        if not df_coll.empty:
            df_main = df_main.merge(df_coll, on='biz_code', how='left')
        else:
            df_main['total_collected'] = 0.0

        return df_main.fillna({'total_invoiced': 0.0, 'total_collected': 0.0})
    finally:
        if conn: conn.close()

# ==========================================
# ⚙️ 引擎二：分包合同核算 (增加关联主合同数据抓取)
# ==========================================
def enrich_sub_contract_stats(df_sub: pd.DataFrame) -> pd.DataFrame:
    if df_sub.empty or 'biz_code' not in df_sub.columns:
        return df_sub

    conn = get_connection()
    try:
       # 1. 清洗分包表编号
        df_sub['biz_code'] = df_sub['biz_code'].astype(str).str.strip()
        df_sub['actual_main_code'] = df_sub['actual_main_code'].astype(str).str.strip()
        sub_codes = df_sub['biz_code'].tolist()
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        placeholders = ', '.join(['%s'] * len(sub_codes))
        params = tuple(sub_codes)

        # 2. 抓取分包已付 (从 biz_outbound_payments)
        sql_pay = f"""
            SELECT sub_contract_code as biz_code, 
                   SUM(payment_amount) as total_paid,
                   MAX(payment_date) as last_payment_date
            FROM biz_outbound_payments
            WHERE sub_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY sub_contract_code
        """
        cur.execute(sql_pay, params)
        df_pay = pd.DataFrame(cur.fetchall())
        if not df_pay.empty:
            df_pay['total_paid'] = df_pay['total_paid'].astype(float)
            df_pay['biz_code'] = df_pay['biz_code'].astype(str).str.strip()

        # 🟢 2.5 抓取分包已收票 (从全新的 biz_sub_invoices 表)
        sql_inv = f"""
            SELECT sub_contract_code as biz_code, 
                   SUM(invoice_amount) as total_invoiced_from_sub
            FROM biz_sub_invoices
            WHERE sub_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY sub_contract_code
        """
        cur.execute(sql_inv, params)
        df_inv = pd.DataFrame(cur.fetchall())
        if not df_inv.empty:
            df_inv['total_invoiced_from_sub'] = df_inv['total_invoiced_from_sub'].astype(float)
            df_inv['biz_code'] = df_inv['biz_code'].astype(str).str.strip()

        # 3. 核心补充：抓取关联主合同的金额 (用于 sub_ratio 比例计算公式)
        main_codes = [c for c in df_sub['actual_main_code'].unique().tolist() if c and str(c) != 'nan']
        df_main_data = pd.DataFrame()
        if main_codes:
            m_placeholders = ', '.join(['%s'] * len(main_codes))
            sql_main = f"""
                SELECT m.biz_code as actual_main_code, m.contract_amount as main_contract_amount, 
                       COALESCE(SUM(c.collected_amount), 0) as main_total_collected
                FROM biz_main_contracts m
                LEFT JOIN biz_collections c ON m.biz_code = c.main_contract_code AND c.deleted_at IS NULL
                WHERE m.biz_code IN ({m_placeholders}) AND m.deleted_at IS NULL
                GROUP BY m.biz_code, m.contract_amount
            """
            cur.execute(sql_main, tuple(main_codes))
            df_main_data = pd.DataFrame(cur.fetchall())
            if not df_main_data.empty:
                df_main_data[['main_contract_amount', 'main_total_collected']] = df_main_data[['main_contract_amount', 'main_total_collected']].astype(float)
                df_main_data['actual_main_code'] = df_main_data['actual_main_code'].astype(str).str.strip()

        # 4. 清理主表中的虚拟列，防止重名
        v_cols = ['total_paid', 'total_invoiced_from_sub', 'main_contract_amount', 'main_total_collected']
        df_sub = df_sub.drop(columns=[c for c in v_cols if c in df_sub.columns])

        # 5. 合并 (增加 df_inv 的合并)
        if not df_pay.empty:
            df_sub = df_sub.merge(df_pay, on='biz_code', how='left')
        if not df_inv.empty:
            df_sub = df_sub.merge(df_inv, on='biz_code', how='left')
        if not df_main_data.empty:
            df_sub = df_sub.merge(df_main_data, on='actual_main_code', how='left')

        # 🟢 新增兜底逻辑：如果该分包没有关联实际主合同，导致 merge 没带过来主合同的金额列，强制赋 0
        for c in v_cols:
            if c not in df_sub.columns:
                df_sub[c] = 0.0

        return df_sub.fillna({c: 0.0 for c in v_cols})
    finally:
        if conn: conn.close()

# ==========================================
# ⚙️ 引擎三：名义关联 (EBM) 资金红线拦截器 (升级版)
# ==========================================
# 文件位置: backend/core/finance_engine.py

def validate_sub_payment_risk(sub_biz_code: str, apply_amount: float) -> tuple[bool, str]:
    """[支付前置风控] 全景透视版：打印每一步的查库结果"""
    sys_logger.info(f"🛡️ --- 风控雷达启动: 目标分包 [{sub_biz_code}] ---")
    is_external_conn = conn is not None
    if not is_external_conn:
        conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. 查分包底层数据 (全量查出，看有没有漏掉什么字段)
        cur.execute("SELECT * FROM biz_sub_contracts WHERE biz_code = %s AND deleted_at IS NULL FOR UPDATE", (sub_biz_code,))
        sub_raw = cur.fetchone()
        sys_logger.info(f"  [账本] 该分包总额: {sub_total}...")
        
        if not sub_raw:
            return True, "数据库查无此分包，系统放行"
            
        # 兼容读取 (自动在物理列和 JSONB 溢出列中寻找)
        ebm_code = sub_raw.get('book_main_code')
        if not ebm_code and sub_raw.get('extra_props'):
            if isinstance(sub_raw['extra_props'], dict):
                ebm_code = sub_raw['extra_props'].get('book_main_code')
            elif isinstance(sub_raw['extra_props'], str):
                import json
                try: ebm_code = json.loads(sub_raw['extra_props']).get('book_main_code')
                except: pass
        
        sys_logger.info(f"  [解析] 提取到归属主合同(EBM): {ebm_code}")
        
        if not ebm_code:
            return True, "无 EBM 关联，不在风控管辖内，放行"
            
        ebm_code = ebm_code.strip()
        sub_total = float(sub_raw.get('sub_amount') or 0)
        
        # 2. 查该分包历史已付金额
        cur.execute('SELECT SUM(payment_amount) as paid FROM biz_outbound_payments WHERE sub_contract_code = %s AND deleted_at IS NULL', (sub_biz_code,))
        already_paid = float(cur.fetchone()['paid'] or 0)
        future_ratio = (already_paid + float(apply_amount)) / sub_total if sub_total > 0 else 0
        
        sys_logger.info(f"  [账本] 该分包总额: {sub_total}, 历史已付: {already_paid}, 本次申请: {apply_amount}")
        sys_logger.info(f"  [测算] 支付后该分包进度将达到: {future_ratio:.2%}")
        
        # 3. 查主合同数据
        cur.execute("SELECT * FROM biz_main_contracts WHERE biz_code = %s AND deleted_at IS NULL", (ebm_code,))
        main_raw = cur.fetchone()
        
        if not main_raw:
            sys_logger.info(f"  [警告] 找不到关联的账面主合同 [{ebm_code}]！")
            return True, "归属的账面主合同不存在，强制放行"
            
        main_total = float(main_raw.get('contract_amount') or 0)
        
        cur.execute('SELECT SUM(collected_amount) as coll FROM biz_collections WHERE main_contract_code = %s AND deleted_at IS NULL', (ebm_code,))
        main_coll = float(cur.fetchone()['coll'] or 0)
        main_ratio = main_coll / main_total if main_total > 0 else 0
        
        sys_logger.info(f"  [账本] 挂靠主合同总额: {main_total}, 已收款: {main_coll}")
        sys_logger.info(f"  [测算] 挂靠主合同回款进度: {main_ratio:.2%}")
        
        # 4. 决断 (增加 0.1% 的浮点数容错率)
        if future_ratio > (main_ratio + 0.001):
            return False, f"主合同回款率仅 {main_ratio:.1%}，本次支付将使分包进度达 {future_ratio:.1%}，打破红线！"
            
        return True, "风控测算通过，允许付款"
        
    except Exception as e:
        sys_logger.error(f"  [异常] 风控引擎崩溃: {e}", exc_info=True)
        return False, f"风控异常: {e}"
    finally:
        if not is_external_conn and conn: 
            conn.close()