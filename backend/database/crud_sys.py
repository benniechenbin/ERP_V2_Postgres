import pandas as pd
from backend.database.db_engine import get_connection, sql_engine, UPLOAD_DIR

def update_biz_code_cascade(old_code, new_code, table_name):
    """
    🟢 终极级联更新：当修改合同编号时，同步修改所有流水、附件表，以及重命名物理文件夹！
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:  # 🟢 必须创建游标
            # 1. 改主表
            cur.execute(f'UPDATE "{table_name}" SET biz_code = %s WHERE biz_code = %s', (new_code, old_code))
            
            # 2. 改周边所有的子表
            cur.execute('UPDATE biz_payment_plans SET main_contract_code = %s WHERE main_contract_code = %s', (new_code, old_code))
            cur.execute('UPDATE biz_invoices SET main_contract_code = %s WHERE main_contract_code = %s', (new_code, old_code))
            cur.execute('UPDATE biz_collections SET main_contract_code = %s WHERE main_contract_code = %s', (new_code, old_code))
            cur.execute('UPDATE sys_attachments SET biz_code = %s WHERE biz_code = %s', (new_code, old_code))
        
        conn.commit()

        # 3. 🟢 物理世界大挪移：重命名硬盘里的文件夹
        old_dir = UPLOAD_DIR / str(old_code)
        new_dir = UPLOAD_DIR / str(new_code)
        if old_dir.exists() and not new_dir.exists():
            old_dir.rename(new_dir) # 彻底解决“孤儿附件”问题

        return True, f"业务编号已全盘迁移至 {new_code}"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def get_attachment_counts():
    """获取所有项目的附件数量统计 (biz_code 版)"""
    conn = None
    try:
        conn = get_connection()
        # 🟢 替换为 biz_code
        sql = "SELECT biz_code, source_table, COUNT(id) as file_count FROM sys_attachments GROUP BY biz_code, source_table"
        return pd.read_sql_query(sql, conn)
    except Exception as e:
        print(f"附件统计查询失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

def soft_delete_project(project_id, table_name, operator_name="System"):
    """软删除：移入回收站 (记录删除人)"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:  # 🟢 依然使用游标防崩溃
            # 🟢 同时更新时间和操作人
            cur.execute(
                f'UPDATE "{table_name}" SET deleted_at = CURRENT_TIMESTAMP, deleted_by = %s WHERE id = %s', 
                (operator_name, project_id)
            )
        conn.commit()
        return True, "已移入回收站"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def restore_project(project_id, table_name):
    """恢复项目：移出回收站 (同步清除删除痕迹)"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # 🟢 恢复时，把时间和操作人统统清空
            cur.execute(
                f'UPDATE "{table_name}" SET deleted_at = NULL, deleted_by = NULL WHERE id = %s', 
                (project_id,)
            )
        conn.commit()
        return True, "项目已恢复"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def get_deleted_projects(tables):
    """获取所有被软删除的项目列表"""
    conn = None
    deleted_list = []
    try:
        conn = get_connection()
        for tbl in tables:
            try:
                # 🟢 替换为 biz_code
                sql = f'SELECT id, biz_code, project_name, manager, "{tbl}" as origin_table FROM "{tbl}" WHERE deleted_at IS NOT NULL'
                df_del = pd.read_sql_query(sql, sql_engine)
                if not df_del.empty:
                    deleted_list.extend(df_del.to_dict('records'))
            except:
                continue
        return deleted_list
    finally:
        if conn: conn.close()

def log_job_operation(operator: str, file_name: str, import_type: str, success_count: int, fail_count: int = 0, error_details: dict = None):
    """
    🟢 V3.0 导入日志写入 (向后兼容的适配器)
    外观依然是旧的 import_operation，但底层已经接入了全新的 sys_job_logs。
    """
    import json
    from backend.database.db_engine import get_connection
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 智能推导状态机
            total_count = success_count + fail_count
            status = 'success' if fail_count == 0 else ('failed' if success_count == 0 else 'partial_fail')
            error_json = json.dumps(error_details, ensure_ascii=False) if error_details else None
            
            # 映射到新的 sys_job_logs 表
            sql = """
                INSERT INTO sys_job_logs 
                (operator, job_type, target_model, source_name, status, total_count, success_count, fail_count, error_details)
                VALUES (%s, 'excel_import', %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                operator, 
                import_type,   # 旧的 import_type 映射为 target_model
                file_name,     # 旧的 file_name 映射为 source_name
                status, 
                total_count, 
                success_count, 
                fail_count, 
                error_json
            ))
        conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 写入批量任务日志失败: {e}")
        return False
    finally:
        if conn: conn.close()     