from werkzeug.security import generate_password_hash
from backend.database.db_engine import get_connection, execute_raw_sql

def create_system_user(username: str, password: str, role: str) -> tuple[bool, str]:
    """
    [核心业务逻辑] 创建系统用户（包含防重校验与密码哈希加密）
    """
    if not username or not password:
        return False, "账号和密码不能为空"
        
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. 校验重名 (业务规则)
            cur.execute("SELECT id FROM sys_users WHERE username = %s", (username,))
            if cur.fetchone():
                return False, "该账号已存在，请换一个名称"
                
            # 2. 密码加密 (安全防线)
            hashed_pwd = generate_password_hash(password)
            
            # 3. 执行写入
            cur.execute(
                "INSERT INTO sys_users (username, password_hash, role, status) VALUES (%s, %s, %s, 'active')",
                (username, hashed_pwd, role)
            )
        conn.commit()
        return True, "账号创建成功"
    except Exception as e:
        conn.rollback()
        return False, f"创建失败: {str(e)}"
    finally:
        conn.close()

def reset_user_password(username: str, new_password: str) -> tuple[bool, str]:
    """重置密码"""
    if not new_password:
        return False, "新密码不能为空"
        
    hashed_pwd = generate_password_hash(new_password)
    success, msg = execute_raw_sql(
        "UPDATE sys_users SET password_hash = %s WHERE username = %s", 
        (hashed_pwd, username)
    )
    return success, msg