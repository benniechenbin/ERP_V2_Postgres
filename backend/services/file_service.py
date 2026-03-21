from pathlib import Path
from backend.database.db_engine import get_connection, UPLOAD_DIR

def save_attachment(biz_code, uploaded_file, source_table, file_category="unknown"):
    """
    [Service 层] 负责附件的物理落地、安全校验，并持久化到系统附件库
    """
    conn = None
    try:
        # 1. 物理层：动态建立合同专属文件夹并写入磁盘
        target_dir = UPLOAD_DIR / str(biz_code)
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / uploaded_file.name

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 2. 逻辑层：提取文件元数据 (后缀名等)
        file_extension = Path(uploaded_file.name).suffix.lower().lstrip('.')
        # 预留扩展位：可以在这里调用 os.path.getsize(file_path) 获取文件大小并存入 file_size_kb

        # 3. 持久层：写入数据库 (sys_attachments)
        conn = get_connection()
        sql = """
            INSERT INTO sys_attachments (biz_code, source_table, file_category, file_name, file_path, file_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        conn.execute(sql, (biz_code, source_table, file_category, uploaded_file.name, str(file_path), file_extension))
        conn.commit()
        
        # 🚀 预留钩子：如果是合同文本，且配置了 AI 自动解析，未来在这里向消息队列发送 AI 解析任务！
        
        return True, "附件归档成功"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()