# 文件位置: backend/services/flow_service.py
import pandas as pd
from datetime import datetime
# 🟢 接入数据库大本营
from backend.database import get_connection

def recalculate_project_total(biz_code, source_table):
    """
    [内部逻辑 - 影子卫士] 重新计算该项目的总回款，并回写到底座中。
    """
    if not source_table:
        return False, "未指定源表"
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 🟢 修正：? 替换为 %s
        cursor.execute(
            "SELECT SUM(amount) FROM sys_project_flows WHERE biz_code = %s AND source_table = %s", 
            (biz_code, source_table)
        )
        result = cursor.fetchone()
        total_val = result[0] if result and result[0] is not None else 0.0
        
        # 🟢 修正：? 替换为 %s
        sql_update = f'UPDATE "{source_table}" SET total_collection = %s WHERE biz_code = %s'
        cursor.execute(sql_update, (total_val, biz_code))
        
        conn.commit()
        return True, total_val
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def add_flow_record(biz_code, source_table, amount, flow_date=None, stage="收款", remark=""):
    """
    [流水服务] 新增记录后，自动触发重算
    """
    if not flow_date:
        flow_date = datetime.now().strftime("%Y-%m-%d")
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor() # 🟢 修正：PostgreSQL 必须生成游标执行
        
        # 🟢 修正：? 替换为 %s
        sql = """
            INSERT INTO sys_project_flows (biz_code, source_table, flow_date, amount, stage, remark) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        # 🟢 致命错误修复：严格对齐上方 SQL 的字段顺序！
        cursor.execute(sql, (biz_code, source_table, flow_date, amount, stage, remark))
        conn.commit()
        
        # 自动执行数据同步，保持汇总层与明细层一致
        recalculate_project_total(biz_code, source_table)
        
        return True, "流水记录已添加并更新汇总"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def get_project_flows(biz_code, source_table):
    """
    [流水服务] 获取指定项目的历史流水清单
    """
    conn = None
    try:
        conn = get_connection()
        # 🟢 修正：? 替换为 %s
        query = """
            SELECT id, flow_date, amount, stage, remark 
            FROM sys_project_flows 
            WHERE biz_code = %s AND source_table = %s
            ORDER BY flow_date DESC
        """
        df = pd.read_sql_query(query, conn, params=(biz_code, source_table))
        return df
    except Exception as e:
        print(f"查询流水失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

def delete_flow_record(flow_id, biz_code, source_table):
    """
    [流水服务] 删除记录后，自动触发重算
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor() # 🟢 修正：PostgreSQL 必须生成游标执行
        
        cursor.execute("DELETE FROM sys_project_flows WHERE id = %s", (flow_id,))
        conn.commit()
        
        # 自动同步
        recalculate_project_total(biz_code, source_table)
        
        return True, "记录已删除并更新汇总"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()