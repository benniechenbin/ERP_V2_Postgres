# 🟢 体验架构之美：直接通过 Facade (门面) 拿连接和工具，干干净净
from backend.database import get_connection, get_all_data_tables

def mark_project_as_accrued(biz_code, table_name):
    """
    [核心业务 - 单条标记] 将指定项目的 '是否计提' 标记为 '是'，并记录计提时间
    """
    conn = None
    try:
        # 🟢 升级：使用统一连接池，为未来 PG 升级铺路
        conn = get_connection()
        cursor = conn.cursor()
        
        # 魔法修改：同时更新状态和时间 (localtime 保证是北京时间)
        sql = f"""
            UPDATE "{table_name}"
            SET is_provisioned = '是',
                accrued_at = datetime('now', 'localtime')
            WHERE biz_code = ?
        """
        cursor.execute(sql, (biz_code,))
        
        if cursor.rowcount > 0:
            conn.commit()
            return True, f"项目 {biz_code} 已成功标记为计提！(已记录时间)"
        else:
            return False, f"未找到项目 {biz_code}，请检查编号。"
            
    except Exception as e:
        if conn: conn.rollback()
        return False, f"标记失败: {e}"
    finally:
        if conn:
            conn.close()


def execute_yearly_accrual_archive():
    """
    [核心业务 - 年度归档] 跨年一键清理引擎 (物理列疾速版)
    遍历所有数据表，将物理列 is_provisioned 为 '是' 的项目，移入回收站 (is_active = 0)
    """
    conn = None
    total_archived = 0
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        tables = get_all_data_tables()
        
        for table in tables:
            # 核心修复：直接瞄准物理列 is_provisioned 查询
            sql = f"""
                UPDATE "{table}" 
                SET is_active = 0 
                WHERE is_provisioned = '是' 
                AND is_active = 1
            """
            cursor.execute(sql)
            total_archived += cursor.rowcount  
            
        conn.commit()
        return True, f"🎉 年度归档完成！共将 {total_archived} 个已计提项目安全移入回收站。"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"归档失败: {e}"
    finally:
        if conn:
            conn.close()