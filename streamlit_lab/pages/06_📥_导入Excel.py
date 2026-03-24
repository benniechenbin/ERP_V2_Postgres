# 文件位置: pages/04_📥_导入Excel.py
import sys
from pathlib import Path

# ==========================================
# 🟢 寻路魔法
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from backend import database as db
from backend.config import config_manager as cfg
from backend import services as svc
from backend.database import schema
from sidebar_manager import render_sidebar
import debug_kit
import components as ui

st.set_page_config(layout="wide", page_title="数据导入中心")
render_sidebar()

# 标题区
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.title("📥 智能导入与映射中心")
    st.caption("V2.0 增强版：全自动关联 Schema + 智能表头匹配")

st.divider() 
# ==========================================
# 🟢 模块 1：文件上传与模型选定
# ==========================================
uploaded_file = st.file_uploader("📂 第一步：上传 Excel 文件", type=["xlsx", "xls"])

if uploaded_file:
    if st.session_state.get('last_uploaded_filename') != uploaded_file.name:
        st.session_state['header_overrides'] = {}
        st.session_state['last_uploaded_filename'] = uploaded_file.name
    if 'header_overrides' not in st.session_state:
        st.session_state['header_overrides'] = {}
        
    overrides = st.session_state.get('header_overrides', {})
    with st.spinner("解析中(应用智能启发式算法)..."):
        cleaned_sheets = svc.clean_excel(uploaded_file, header_overrides=overrides)
    
    if not cleaned_sheets:
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        # 1. 选择工作表
        all_sheets = [s['sheet_name'] for s in cleaned_sheets]
        target_sheet = st.selectbox("1. 选择工作表", all_sheets)
        
        target_df = next(s['df'] for s in cleaned_sheets if s['sheet_name'] == target_sheet)
        headers = target_df.columns.tolist()
       
    with c2:
        # 🟢 升级 1：获取完整配置，使用 format_func 显示优雅的中文别名
        config_models = cfg.load_data_rules().get("models", {})
        all_models = list(config_models.keys())
        
        model_name = st.selectbox(
            "2. 映射到业务模型", 
            all_models,
            format_func=lambda m: f"📦 {config_models[m].get('model_label', m)}"
        )

    # ==========================================
    # 🟢 模块 2：核心映射区 (自动化优先 + 人工纠偏)
    # ==========================================
    st.divider()
    with st.container(border=True):
        st.markdown("### 🛠️ 字段映射确认")
        with st.expander("🛠️ 高级：表头识别错误？手动指定行号", expanded=False):
            st.caption("启发式算法若跳过了真正的表头，请在此处强制指定。")
            current_idx = overrides.get(target_sheet, -1)
            ui_val = current_idx + 1 if current_idx >= 0 else 0
            
            new_val = st.number_input(
                f"[{target_sheet}] 表头所在行号", 
                min_value=0, 
                max_value=50, 
                value=ui_val, 
                step=1, 
                help="0 = 自动识别。如果表头在 Excel 第 3 行，请填入 3。"
            )
            
            if new_val != ui_val:
                if new_val > 0:
                    st.session_state['header_overrides'][target_sheet] = int(new_val) - 1
                else:
                    if target_sheet in st.session_state['header_overrides']:
                        del st.session_state['header_overrides'][target_sheet]
                st.rerun()
                
        mapping = cfg.get_column_mapping(model_name)
        default_sel = [
            h for h in headers 
            if any(h in aliases for aliases in mapping.values()) or svc.smart_classify_header(h)
        ]
        
        chosen_cols = st.multiselect(
            "1. 勾选要导入的列", options=headers, default=default_sel, key="multi_select_cols"
        )
        
        user_final_mapping = {} 
        
        if chosen_cols:
            st.markdown("##### 2. 确认目标字段 (已为您自动匹配，如有误请手动修改)")
            
            standard_opts = cfg.get_standard_options(model_name)
            IGNORE_OPT = "📦 [附加属性] 存入 JSONB"
            all_opts = standard_opts + [IGNORE_OPT]
            
            ui_cols = st.columns(3)
            for i, col_original in enumerate(chosen_cols):
                auto_key = None
                for db_key, excel_aliases in mapping.items():
                    if col_original in excel_aliases:
                        auto_key = db_key
                        break
                if not auto_key:
                    auto_key = svc.smart_classify_header(col_original)
                
                default_idx = all_opts.index(IGNORE_OPT) 
                if auto_key:
                    for idx, opt in enumerate(all_opts):
                        if opt.startswith(f"{auto_key} |"):
                            default_idx = idx
                            break
                
                with ui_cols[i % 3]:
                    is_important = any(k in col_original.lower() for k in ['名称', '编号', 'name', 'code'])
                    display_label = f"原列: **{col_original}** ⭐️" if is_important else f"原列: **{col_original}**"
                    selected_opt = st.selectbox(
                        display_label,               
                        options=all_opts, 
                        index=default_idx, 
                        key=f"map_{col_original}"
                    )
                    
                    
                    if selected_opt == IGNORE_OPT:
                        # 🟢 明确告诉后端：这列我要放进 JSONB！
                        user_final_mapping[col_original] = "INTO_JSONB" 
                    else:
                        user_final_mapping[col_original] = selected_opt.split(" |")[0].strip()
                        
    # ==========================================
    # 🟢 模块 3：执行导入 (极简版)
    # ==========================================
    st.divider()
    # 🟢 升级 2：彻底切除历史遗留的主副表物理绑定 UI
    import_mode = st.radio("处理模式", ["追加导入", "覆盖导入"], horizontal=True)

    if st.button("🚀 开始执行导入", type="primary", width="stretch"):
        total_rows = len(target_df)
        msg = f"正在逐行校验并安全入库 {total_rows} 条数据，大文件可能需要等待 1-2 分钟，请勿刷新页面..."
        with st.spinner(msg):

            current_user = st.session_state.get('user_name', 'System')
            success, msg = svc.run_import_process(
                uploaded_file=uploaded_file, 
                target_sheet_name=target_sheet, 
                model_name=model_name,
                import_mode="overwrite" if "覆盖" in import_mode else "append",
                manual_mapping=user_final_mapping, 
                header_overrides=overrides,
                operator=current_user        
            )
            if success:
                st.success(msg)
                st.balloons()
            else:
                st.error(msg)

debug_kit.execute_debug_logic()