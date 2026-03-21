import pandas as pd
from backend.database.db_engine import get_connection, sql_engine, UPLOAD_DIR

def save_contract_file(biz_code, uploaded_file, source_table, file_category="主合同文本"):
    """
    保存附件到本地，并写入数据库 (为 AI 解析打好标签)
    """
    conn = None
    try:
        # 🟢 动态建立合同专属文件夹
        target_dir = UPLOAD_DIR / str(biz_code)
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / uploaded_file.name

        # 写入物理磁盘
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        conn = get_connection()
        # 🟢 存入 sys_contract_files，并将 file_category 作为 AI 识别的凭证
        sql = """
            INSERT INTO sys_contract_files (biz_code, source_table, file_name, file_path, file_type)
            VALUES (%s, %s, %s, %s, %s)
        """
        conn.execute(sql, (biz_code, source_table, uploaded_file.name, str(file_path), file_category))
        conn.commit()
        return True, "附件归档成功"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()
def update_biz_code_cascade(old_code, new_code, table_name):
    """
    🟢 终极级联更新：当修改合同编号时，同步修改所有流水、附件表，以及重命名物理文件夹！
    """
    conn = None
    try:
        conn = get_connection()
        # 1. 改主表
        conn.execute(f'UPDATE "{table_name}" SET biz_code = %s WHERE biz_code = %s', (new_code, old_code))
        
        # 2. 改周边所有的子表
        conn.execute('UPDATE biz_payment_plans SET main_contract_code = %s WHERE main_contract_code = %s', (new_code, old_code))
        conn.execute('UPDATE biz_invoices SET main_contract_code = %s WHERE main_contract_code = %s', (new_code, old_code))
        conn.execute('UPDATE biz_collections SET main_contract_code = %s WHERE main_contract_code = %s', (new_code, old_code))
        conn.execute('UPDATE sys_contract_files SET biz_code = %s WHERE biz_code = %s', (new_code, old_code))
        
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
        sql = "SELECT biz_code, source_table, COUNT(id) as file_count FROM contract_files GROUP BY biz_code, source_table"
        return pd.read_sql_query(sql, conn)
    except Exception as e:
        print(f"附件统计查询失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

def save_contract_file(biz_code, uploaded_file, source_table, file_category="主合同文本"):
    """
    保存附件到本地，并写入数据库 (为 AI 解析打好标签)
    """
    conn = None
    try:
        # 🟢 动态建立合同专属文件夹
        target_dir = UPLOAD_DIR / str(biz_code)
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / uploaded_file.name

        # 写入物理磁盘
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        conn = get_connection()
        # 🟢 存入 sys_contract_files，并将 file_category 作为 AI 识别的凭证
        sql = """
            INSERT INTO sys_contract_files (biz_code, source_table, file_name, file_path, file_type)
            VALUES (%s, %s, %s, %s, %s)
        """
        conn.execute(sql, (biz_code, source_table, uploaded_file.name, str(file_path), file_category))
        conn.commit()
        return True, "附件归档成功"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def soft_delete_project(project_id, table_name):
    """软删除：移入回收站"""
    conn = None
    try:
        conn = get_connection()
        conn.execute(f'UPDATE "{table_name}" SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s', (project_id,))
        conn.commit()
        return True, "已移入回收站"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def restore_project(project_id, table_name):
    """恢复项目：移出回收站"""
    conn = None
    try:
        conn = get_connection()
        conn.execute(f'UPDATE "{table_name}" SET deleted_at = NULL WHERE id = %s', (project_id,))
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

def log_import_operation(operator: str, file_name: str, import_type: str, success_count: int):
    """🟢 V2.0 导入行为审计日志写入"""
    conn = None
    try:
        
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO sys_import_logs (operator, file_name, import_type, success_count)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (operator, file_name, import_type, success_count))
        conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 写入导入日志失败: {e}")
        return False
    finally:
        if conn: conn.close()       