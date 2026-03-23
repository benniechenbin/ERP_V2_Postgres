import re
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database.db_engine import get_connection, execute_raw_sql

# 🟢 安全防线 1：角色白名单 (防抓包越权篡改)
# 未来换新系统，只需修改这个列表即可
ALLOWED_ROLES = ["普通员工", "部门经理", "财务专员", "系统管理员"]

def _validate_username(username: str) -> tuple[bool, str]:
    """内部校验：账号只能是字母、数字、下划线，且长度 3-20"""
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        return False, "账号只能包含字母、数字和下划线，且长度在 3-20 位之间"
    return True, ""

def _validate_password_strength(password: str) -> tuple[bool, str]:
    """内部校验：极简密码强度控制"""
    if len(password) < 6:
        return False, "密码长度至少需要 6 位"
    if password.strip() != password:
        return False, "密码首尾不能包含空格"
    return True, ""

def create_system_user(username: str, password: str, role: str) -> tuple[bool, str]:
    """
    [核心业务逻辑] 创建系统用户（包含强校验、防重与哈希加密）
    """
    if not username or not password:
        return False, "账号和密码不能为空"
        
    # 🟢 安全防线 2：后端强校验输入格式
    is_valid_u, u_msg = _validate_username(username)
    if not is_valid_u: return False, u_msg
    
    is_valid_p, p_msg = _validate_password_strength(password)
    if not is_valid_p: return False, p_msg
        
    if role not in ALLOWED_ROLES:
        return False, f"非法角色分配。允许的角色有: {', '.join(ALLOWED_ROLES)}"
        
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 校验重名
            cur.execute("SELECT id FROM sys_users WHERE username = %s", (username,))
            if cur.fetchone():
                return False, "该账号已存在，请换一个名称"
                
            # 密码加密
            hashed_pwd = generate_password_hash(password)
            
            # 执行写入
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
    """重置密码 (带强度校验)"""
    if not new_password:
        return False, "新密码不能为空"
        
    is_valid_p, p_msg = _validate_password_strength(new_password)
    if not is_valid_p: return False, p_msg
        
    hashed_pwd = generate_password_hash(new_password)
    success, msg = execute_raw_sql(
        "UPDATE sys_users SET password_hash = %s WHERE username = %s", 
        (hashed_pwd, username)
    )
    return success, "密码重置成功" if success else msg

# ==========================================
# 🟢 新增：未来极其核心的 2 个通用接口
# ==========================================

def verify_user_login(username: str, password: str) -> tuple[bool, str, dict]:
    """
    [核心防线 3] 验证用户登录
    返回: (是否成功, 提示信息, 用户基础信息字典)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, password_hash, role, status FROM sys_users WHERE username = %s", (username,))
            user = cur.fetchone()
            
            if not user:
                return False, "账号不存在", {}
                
            # user 是元组，对应: id(0), username(1), password_hash(2), role(3), status(4)
            if user[4] != 'active':
                return False, "该账号已被禁用，请联系管理员", {}
                
            # 核心比对魔法！
            if check_password_hash(user[2], password):
                # 登录成功，顺手更新最后登录时间
                cur.execute("UPDATE sys_users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s", (user[0],))
                conn.commit()
                
                user_info = {"id": user[0], "username": user[1], "role": user[3]}
                return True, "登录成功", user_info
            else:
                return False, "密码错误", {}
    except Exception as e:
        return False, f"验证过程出错: {str(e)}", {}
    finally:
        if conn: conn.close()

def toggle_user_status(username: str, is_active: bool) -> tuple[bool, str]:
    """
    [核心防线 4] 启停账号 (软禁用)
    用于员工离职或违规封号
    """
    if username == 'admin' and not is_active:
        return False, "系统超级管理员(admin)不允许被禁用"
        
    new_status = 'active' if is_active else 'disabled'
    success, msg = execute_raw_sql(
        "UPDATE sys_users SET status = %s WHERE username = %s",
        (new_status, username)
    )
    action = "启用" if is_active else "禁用"
    return success, f"账号 {username} 已{action}" if success else msg