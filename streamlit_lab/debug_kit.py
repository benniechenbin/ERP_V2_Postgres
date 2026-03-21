import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import os
import json
from backend import database as db
from backend.config import config_manager

def is_debug_mode():
    return st.session_state.get('debug_mode', False)

def render_debug_sidebar():
    st.sidebar.markdown("---")
    if 'debug_mode' not in st.session_state:
        st.session_state['debug_mode'] = False
    
    mode = st.sidebar.toggle("🐞 开发者模式 (Debug)", value=st.session_state['debug_mode'])
    st.session_state['debug_mode'] = mode
    if mode:
        if st.sidebar.button("🚀 进入实验室 (Sandbox)", width="stretch"):
            st.switch_page("pages/99_🧪_实验室.py")

def execute_debug_logic(current_db_path=None):
    if not is_debug_mode(): return

    actual_db_path = current_db_path
    if actual_db_path is None:
        actual_db_path = db.get_connection()
    
    st.markdown("---")
    st.markdown("### 🐞 开发者控制台 (Pro)")
    
    tabs = st.tabs(["⚙️ 系统全量配置","💾 SQL终端", "🧠 内存/Session","🔥 危险区"])
    # =========================================================
    # Tab 1: 核心模型配置 (应急修改区)
    # =========================================================
    with tabs[0]:
        st.subheader("🛠️ 系统全量配置 (App Config JSON)")
        st.caption("⚠️ 警告：此区域用于紧急修改表结构与映射规则。修改后保存，系统底层的引擎会自动将 label 对齐到 column_mapping 中。")
        
        # 获取最新的配置数据
        current_config = config_manager.load_data_rules()
        # 我们只把 models 部分暴露出来（不包含公式等其他信息），防止用户改乱
        models_data = current_config.get("models", {})
        
        # 纯净的大文本框
        models_input = st.text_area(
            "Models JSON (包含各表的 field_meta 与 column_mapping)",
            value=json.dumps(models_data, indent=4, ensure_ascii=False),
            height=600,
            key="json_models_emergency"
        )
        
        if st.button("💾 强制覆写模型配置", type="primary", width="stretch"):
            try:
                # 解析输入的纯文本 JSON
                new_models = json.loads(models_input)
                
                # 将改动合并回原配置 (保留公式等其他节点不被破坏)
                current_config["models"] = new_models
                
                # 🟢 调用 config_manager 的保存方法，它会在内部自动触发 _auto_sync_labels
                if config_manager.save_data_rules(current_config):
                    st.success("🎉 模型配置覆写成功！")
                    
                    # --- 🟢 新增逻辑：强制触发数据库底座的“热更新” ---
                    try:
                        from backend.database import schema
                        schema.sync_database_schema() # 立即对比并增加缺少的列
                        st.cache_resource.clear()     # 清理 app.py 的启动缓存，防止状态不一致
                        st.success("✅ 数据库底层物理表已同步扩容！")
                    except Exception as e:
                        st.error(f"⚠️ 数据库同步失败，请检查终端日志: {e}")
                    # ------------------------------------------------
                    
                    st.rerun() # 刷新页面重新加载内存
                else:
                    st.error("❌ 文件写入失败。")
            except json.JSONDecodeError as je:
                st.error(f"❌ JSON 格式严重错误，请检查标点符号或括号匹配：{je}")

    # =========================================================
    # Tab 2: SQL 终端 (修复版)
    # =========================================================
    with tabs[1]:
        st.write(f"连接库：`{current_db_path}`")
        st.subheader("💻 SQL 执行终端")
        
        # 1. 获取当前所有表名
        all_tables = db.get_all_data_tables()
        default_table = all_tables[0] if all_tables else "data_Project2026"

        # 2. 定义常用 SQL 模板
        SQL_TEMPLATES = {
            "--- 请选择预设模板 (可选) ---": "",
            "🔍 查看所有表名": "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
            "👀 查看前 10 条数据": f"SELECT * FROM \"{default_table}\" LIMIT 10;",
            "📑 查看表结构 (列定义)": f"PRAGMA table_info(\"{default_table}\");",
            "➕ [热修] 增加一个小数列 (用于金额/系数)": f"ALTER TABLE \"{default_table}\" ADD COLUMN new_column_name REAL DEFAULT 0.0;",
            "➕ [热修] 增加一个开关列 (用于状态标记)": f"ALTER TABLE \"{default_table}\" ADD COLUMN is_flag INTEGER DEFAULT 0;",
            "➕ [热修] 增加一个文本列 (用于备注)": f"ALTER TABLE \"{default_table}\" ADD COLUMN new_text_col TEXT;",
            "🧹 [清理] 删除项目编号为空的行": f"DELETE FROM \"{default_table}\" WHERE biz_code IS NULL OR biz_code = '';",
            "🔥 [危险] 删除整个表": f"DROP TABLE \"{default_table}\";"
        }

        # --- 🟢 核心修复：定义回调函数 ---
        def on_template_change():
            # 获取下拉框当前选中的 key
            selected_key = st.session_state['sql_template_selector']
            # 强制更新输入框的 Session State
            st.session_state['sql_input_area'] = SQL_TEMPLATES.get(selected_key, "")

        # 3. 模板选择器 (添加 on_change)
        c_temp, c_tip = st.columns([3, 1])
        with c_temp:
            st.selectbox(
                "⚡ 快速填充 SQL 模板", 
                options=list(SQL_TEMPLATES.keys()),
                index=0,
                key="sql_template_selector",
                on_change=on_template_change  # <--- 🟢 绑定回调
            )
        with c_tip:
            st.info(f"当前默认表: `{default_table}`")

        # 4. SQL 编辑区
        # 注意：这里不再需要 value 参数来动态绑定，因为 state 已经由回调函数控制了
        # 但为了第一次渲染不报错，可以保留 value作为初始值，或者确保 key 在 session_state 中初始化
        if "sql_input_area" not in st.session_state:
             st.session_state["sql_input_area"] = ""

        sql_input = st.text_area(
            "SQL 语句 (支持多行)", 
            height=150,
            help="输入标准 SQLite 语法。如需操作特定表，请确保表名加双引号。",
            key="sql_input_area" # <--- 这里的 key 与回调函数里的一致
        )
        
        # 5. 执行按钮
        col_run, col_helper = st.columns([1, 4])
        with col_run:
            run_btn = st.button("🚀 执行 SQL", type="primary")
        
        if run_btn and sql_input.strip():
            # 🟢 拆弹 2：不再使用 sqlite3.connect，直接调用底层的 execute_raw_sql
            success, result = db.execute_raw_sql(sql_input)
            if success:
                if isinstance(result, pd.DataFrame):
                    st.success(f"✅ 查询成功，返回 {len(result)} 行")
                    st.dataframe(result, width="stretch")
                else:
                    st.success(f"✅ {result}")
            else:
                st.error(f"❌ 执行失败: {result}")
    with tabs[2]:
        st.write("当前 Session State 所有变量：")
        st.json(dict(st.session_state))
       
    with tabs[3]:
        if st.button("🔥 重置所有配置为默认值"):
            if os.path.exists(config_manager.CONFIG_FILE):
                os.remove(config_manager.CONFIG_FILE)
            st.success("已重置，请刷新页面。")
            st.rerun()