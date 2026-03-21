import os
from datetime import datetime

# 🟢 从统一入口导入
from backend.database import get_connection, UPLOAD_DIR

# =========================================================
# 模块：基础文件存储服务 (PostgreSQL 适配版)
# =========================================================

def save_contract_file(biz_code, file_name, file_bytes, table_name=None, file_type="unknown"):
    """
    [通用文件上传] 将任何格式的文件字节流存入物理硬盘，并记录到 PostgreSQL 数据库。
    """
    conn = None
    try:
        # 1. 兜底表名逻辑
        if table_name is None:
            table_name = "unknown_source"
            
        # 2. 物理存储逻辑：确保以项目编号为目录 (使用 UPLOAD_DIR 绝对路径)
        target_dir = os.path.join(UPLOAD_DIR, str(biz_code))
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        path = os.path.join(target_dir, file_name)
        
        # 写入字节流
        with open(path, "wb") as f:
            f.write(file_bytes)
        
        # 3. 数据库记录逻辑 (PostgreSQL 适配)
        conn = get_connection()
        cur = conn.cursor()
        
        # 🟢 关键修改：? 替换为 %s，补齐字段
        sql = """
            INSERT INTO sys_contract_files 
            (biz_code, source_table, file_name, file_path, file_type, upload_time) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql, (
            biz_code, 
            table_name, 
            file_name, 
            path, 
            file_type, 
            datetime.now()
        ))
        
        conn.commit()
        return True, "上传成功"
        
    except Exception as e:
        if conn: 
            conn.rollback()
        return False, f"文件保存失败: {str(e)}"
    finally:
        if conn: 
            conn.close()