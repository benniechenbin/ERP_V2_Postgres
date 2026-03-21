import os
import shutil
# 🟢 引入新架构的底层引擎
from backend.database.db_engine import get_connection, UPLOAD_DIR

def update_biz_code_cascade(old_code, new_code, table_name):
    """
    [项目服务] 级联更新项目编号
    统筹协调数据库级的联动修改与物理附件文件夹的重命名。
    """
    if not old_code or not new_code:
        return False, "编号不能为空"
    if old_code == new_code:
        return False, "新旧编号一致"
    
    # 🟢 兼容 pathlib 路径
    old_dir = os.path.join(str(UPLOAD_DIR), str(old_code))
    new_dir = os.path.join(str(UPLOAD_DIR), str(new_code))
    
    conn = None
    try:
        # 🟢 调用新引擎获取连接
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. 检查冲突
        cursor.execute(f'SELECT 1 FROM "{table_name}" WHERE biz_code = %s', (new_code,))
        if cursor.fetchone():
            raise ValueError(f"新编号 [{new_code}] 已存在，无法修改！")
        
        # 2. 修改主表
        cursor.execute(f'UPDATE "{table_name}" SET biz_code = %s WHERE biz_code = %s', (new_code, old_code))
        if cursor.rowcount == 0:
            raise ValueError("在主表中未找到原项目，修改失败")
        
        # 3. 修改关联表
        cursor.execute("UPDATE sys_project_flows SET biz_code = %s WHERE biz_code = %s AND source_table = %s", (new_code, old_code, table_name))
        cursor.execute("UPDATE sys_attachments SET biz_code = %s WHERE biz_code = %s AND source_table = %s", (new_code, old_code, table_name))   
        
        # 4. 迁移物理文件
        renamed_folder = False
        if os.path.exists(old_dir):
            if os.path.exists(new_dir):
                for item in os.listdir(old_dir):
                    s = os.path.join(old_dir, item)
                    d = os.path.join(new_dir, item)
                    if not os.path.exists(d):
                        shutil.move(s, d)
                os.rmdir(old_dir)
                renamed_folder = True
            else:
                os.rename(old_dir, new_dir)
                renamed_folder = True
        
        conn.commit()
        msg = "变更成功"
        if renamed_folder:
            msg += " | 文件夹已重命名"
        return True, msg
        
    except Exception as e:
        if conn: conn.rollback()
        return False, f"修改失败: {str(e)}"
    finally:
        if conn:
            conn.close()