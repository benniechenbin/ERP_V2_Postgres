# 文件位置: streamlit_lab/pages/07_⚙️_系统管理.py
import sys
from pathlib import Path
import json

# 🟢 寻路魔法
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from werkzeug.security import generate_password_hash

# 接入新底座
from backend.database.db_engine import get_connection, execute_raw_sql
from backend.config import config_manager as cfg
from sidebar_manager import render_sidebar
import debug_kit
import components as ui

st.set_page_config(page_title="系统管理控制台", page_icon="⚙️", layout="wide")
render_sidebar()

st.title("⚙️ 系统管理控制台")
st.caption("Admin Console：全局用户、回收站与系统级日志调度中心。")

# =========================================================
# 🛠️ 弹窗：新建员工账号
# =========================================================
@st.dialog("🆕 新增系统账号", width="small")
def create_user_dialog():
    with st.form("new_user_form"):
        username = st.text_input("登录账号 (用户名) *", placeholder="例如: zhangsan")
        password = st.text_input("初始密码 *", type="password", placeholder="建议包含字母和数字")
        role = st.selectbox("系统角色", ["普通员工", "部门经理", "财务专员", "系统管理员"])
        
        if st.form_submit_button("💾 保存账号", width="stretch", type="primary"):
            if not username or not password:
                st.error("账号和密码不能为空！")
                st.stop()
                
            # 🟢 1. 检查账号是否重复
            check_sql = "SELECT id FROM sys_users WHERE username = %s"
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(check_sql, (username,))
                if cur.fetchone():
                    st.error("该账号已存在，请换一个名称。")
                    conn.close()
                    st.stop()
            
            # 🟢 2. 密码单向哈希加密 (绝对不能存明文！)
            hashed_pwd = generate_password_hash(password)
            
            # 🟢 3. 安全入库
            insert_sql = """
                INSERT INTO sys_users (username, password_hash, role, status)
                VALUES (%s, %s, %s, 'active')
            """
            try:
                with conn.cursor() as cur:
                    cur.execute(insert_sql, (username, hashed_pwd, role))
                conn.commit()
                st.toast("✅ 账号创建成功！")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"创建失败: {e}")
            finally:
                conn.close()

# =========================================================
# 页面布局：四大管理模块
# =========================================================
tab_users, tab_trash, tab_audit, tab_job = st.tabs([
    "👥 员工账号管理", 
    "🗑️ 全局回收站", 
    "🕵️ 操作审计日志 (Audit)", 
    "⚙️ 后台任务日志 (Jobs)"
])

# ---------------------------------------------------------
# 模块 1：👥 员工账号管理
# ---------------------------------------------------------
with tab_users:
    c_title, c_btn = st.columns([8, 2])
    with c_title:
        st.subheader("账号与权限分配")
    with c_btn:
        if st.button("➕ 新增账号", type="primary", width="stretch"):
            create_user_dialog()
            
    # 获取用户列表
    success, df_users = execute_raw_sql("SELECT id, username, role, status, last_login_at, created_at FROM sys_users ORDER BY id ASC")
    
    if success and not df_users.empty:
        # 添加布尔控制列
        df_users['is_active'] = df_users['status'].apply(lambda x: True if x == 'active' else False)
        df_users.insert(0, '☑️ 选中', False)
        
        edited_users = st.data_editor(
            df_users,
            width="stretch",
            hide_index=True,
            disabled=["id", "username", "created_at", "last_login_at", "status"],
            column_config={
                "☑️ 选中": st.column_config.CheckboxColumn("选择操作", default=False),
                "is_active": st.column_config.CheckboxColumn("允许登录 (活跃状态)"),
                "role": st.column_config.SelectboxColumn("角色", options=["普通员工", "部门经理", "财务专员", "系统管理员"]),
                "last_login_at": st.column_config.DatetimeColumn("最后登录", format="YYYY-MM-DD HH:mm"),
            }
        )
        
        # 侦测状态或角色变化
        if not edited_users.equals(df_users):
            conn = get_connection()
            try:
                for i in range(len(df_users)):
                    old_active = df_users.iloc[i]['is_active']
                    new_active = edited_users.iloc[i]['is_active']
                    old_role = df_users.iloc[i]['role']
                    new_role = edited_users.iloc[i]['role']
                    uid = int(df_users.iloc[i]['id'])
                    uname = df_users.iloc[i]['username']
                    
                    # 防止超级管理员被禁用
                    if not new_active and uname == 'admin':
                        st.error("⛔ 保护机制：系统默认超级管理员 'admin' 无法被禁用！")
                        continue
                        
                    if old_active != new_active or old_role != new_role:
                        new_status = 'active' if new_active else 'disabled'
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE sys_users SET status = %s, role = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                                (new_status, new_role, uid)
                            )
                conn.commit()
                st.toast("✅ 账号状态已更新")
                st.rerun()
            except Exception as e:
                st.error(f"更新失败: {e}")
            finally:
                conn.close()
                
        # 密码重置区
        selected_users = edited_users[edited_users['☑️ 选中'] == True]
        if not selected_users.empty:
            target_username = selected_users.iloc[0]['username']
            st.warning(f"⚠️ 即将重置账号 **{target_username}** 的密码：")
            c_newpwd, c_reset = st.columns([3, 1])
            with c_newpwd:
                new_pwd = st.text_input("输入新密码", type="password", key="reset_pwd_input")
            with c_reset:
                st.write("") # 占位对齐
                if st.button("🔄 强制重置", type="primary", width="stretch"):
                    if new_pwd:
                        hashed_pwd = generate_password_hash(new_pwd)
                        execute_raw_sql("UPDATE sys_users SET password_hash = %s WHERE username = %s", (hashed_pwd, target_username))
                        st.success(f"已将 {target_username} 的密码重置为新密码！")
                    else:
                        st.error("新密码不能为空")
    else:
        st.info("系统暂无账号，请点击右上角新增。")

# ---------------------------------------------------------
# 模块 2：🗑️ 全局回收站
# ---------------------------------------------------------
with tab_trash:
    st.subheader("全局回收站")
    st.caption("所有被软删除的业务数据均在此处。支持一键还原。")
    
    # 动态扫描所有业务表中的删除数据
    config_models = cfg.load_data_rules().get("models", {})
    trash_data = []
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for m_name, m_cfg in config_models.items():
                t_name = m_cfg.get("table_name")
                if not t_name: continue
                
                # 尝试查询已删除的数据
                try:
                    # 动态判断有没有项目名称等易读字段
                    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t_name}'")
                    cols = {row[0] for row in cur.fetchall()}
                    
                    name_col = "project_name" if "project_name" in cols else ("sub_company_name" if "sub_company_name" in cols else "biz_code")
                    
                    cur.execute(f"""
                        SELECT id, biz_code, "{name_col}" as display_name, deleted_at, deleted_by 
                        FROM "{t_name}" 
                        WHERE deleted_at IS NOT NULL
                    """)
                    for row in cur.fetchall():
                        trash_data.append({
                            "模型": m_name,
                            "物理表": t_name,
                            "ID": row[0],
                            "业务编号": row[1],
                            "名称/摘要": row[2],
                            "删除时间": row[3].strftime("%Y-%m-%d %H:%M") if row[3] else "未知",
                            "操作人": row[4] or "未知"
                        })
                except Exception as e:
                    pass # 表可能不存在，跳过
    finally:
        conn.close()
        
    if trash_data:
        df_trash = pd.DataFrame(trash_data)
        df_trash.insert(0, '☑️ 选中', False)
        
        edited_trash = st.data_editor(
            df_trash,
            width="stretch",
            hide_index=True,
            disabled=["模型", "物理表", "ID", "业务编号", "名称/摘要", "删除时间", "操作人"]
        )
        
        selected_trash = edited_trash[edited_trash['☑️ 选中'] == True]
        if not selected_trash.empty:
            if st.button("♻️ 还原选中数据", type="primary"):
                conn = get_connection()
                try:
                    for _, row in selected_trash.iterrows():
                        t_name = row['物理表']
                        r_id = row['ID']
                        with conn.cursor() as cur:
                            cur.execute(f'UPDATE "{t_name}" SET deleted_at = NULL, deleted_by = NULL WHERE id = %s', (r_id,))
                    conn.commit()
                    st.success("✅ 数据已成功还原，并重返业务列表！")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"还原失败: {e}")
                finally:
                    conn.close()
    else:
        st.success("🎉 回收站目前空空如也。")

# ---------------------------------------------------------
# 模块 3：🕵️ 操作审计日志 (Audit Logs)
# ---------------------------------------------------------
with tab_audit:
    st.subheader("全局操作审计总站")
    st.caption("系统内所有的增、删、改痕迹均在此留底（防篡改）。仅显示最新 200 条。")
    
    success, df_audit = execute_raw_sql("""
        SELECT id, created_at, operator_name, action, model_name, biz_code, diff_data 
        FROM sys_audit_logs 
        ORDER BY created_at DESC LIMIT 200
    """)
    
    if success and not df_audit.empty:
        # 优化显示格式
        df_audit['created_at'] = pd.to_datetime(df_audit['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        # 提取 diff_data 摘要
        df_audit['变更字段数'] = df_audit['diff_data'].apply(lambda x: len(json.loads(x)) if isinstance(x, str) else 0)
        
        st.dataframe(
            df_audit[['created_at', 'operator_name', 'action', 'model_name', 'biz_code', '变更字段数']],
            width="stretch",
            hide_index=True,
            column_config={
                "created_at": "操作时间",
                "operator_name": "操作人",
                "action": "动作",
                "model_name": "模块",
                "biz_code": "业务编号"
            }
        )
        
        st.markdown("##### 🔍 穿透查看底层差异 JSON")
        biz_sel = st.selectbox("选择要查看差异细节的业务编号", df_audit['biz_code'].unique().tolist())
        detail_json = df_audit[df_audit['biz_code'] == biz_sel].iloc[0]['diff_data']
        try:
            st.json(json.loads(detail_json))
        except:
            st.write(detail_json)
    else:
        st.info("暂无审计日志。")

# ---------------------------------------------------------
# 模块 4：⚙️ 后台任务日志 (Job Logs)
# ---------------------------------------------------------
with tab_job:
    st.subheader("后台任务监控中心")
    st.caption("Excel 批量导入、财务年度结转等耗时任务的执行结果。")
    
    success, df_jobs = execute_raw_sql("""
        SELECT id, created_at, operator, job_type, target_model, source_name, status, total_count, success_count, fail_count, error_details
        FROM sys_job_logs
        ORDER BY created_at DESC LIMIT 100
    """)
    
    if success and not df_jobs.empty:
        df_jobs['created_at'] = pd.to_datetime(df_jobs['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        def status_emoji(s):
            if s == 'success': return "✅ 成功"
            if s == 'failed': return "❌ 失败"
            if s == 'partial_fail': return "⚠️ 部分失败"
            return "⏳ 处理中"
            
        df_jobs['执行状态'] = df_jobs['status'].apply(status_emoji)
        
        st.dataframe(
            df_jobs[['created_at', 'job_type', 'target_model', 'source_name', '执行状态', 'total_count', 'success_count', 'fail_count', 'operator']],
            width="stretch",
            hide_index=True,
            column_config={
                "created_at": "执行时间",
                "job_type": "任务类型",
                "target_model": "目标模块",
                "source_name": "来源/文件",
                "total_count": "总条数",
                "success_count": "成功条数",
                "fail_count": "失败条数",
                "operator": "触发人"
            }
        )
        
        # 报错详情诊断
        failed_jobs = df_jobs[df_jobs['fail_count'] > 0]
        if not failed_jobs.empty:
            st.markdown("##### 🚨 失败任务诊断 (Traceback)")
            err_sel = st.selectbox("选择出现失败的任务流水号 (ID)", failed_jobs['id'].tolist())
            err_json = failed_jobs[failed_jobs['id'] == err_sel].iloc[0]['error_details']
            try:
                st.json(json.loads(err_json))
            except:
                st.write(err_json)
    else:
        st.info("暂无后台任务执行记录。")

debug_kit.execute_debug_logic()