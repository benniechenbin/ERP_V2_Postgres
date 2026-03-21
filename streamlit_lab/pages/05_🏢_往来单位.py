# 文件位置: pages/05_🏢_往来单位.py
import sys
from pathlib import Path
import json
from datetime import datetime

# ==========================================
# 🟢 寻路魔法与依赖
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from backend.database import crud, schema
from backend.database.db_engine import get_connection, sql_engine, execute_raw_sql
from backend.config import config_manager as cfg
from sidebar_manager import render_sidebar
import debug_kit
import components as ui

# --- 页面基础配置 ---
st.set_page_config(layout="wide", page_title="往来单位库")
render_sidebar()

# ==================== 2. 核心弹窗逻辑 (极简 CRUD) ====================
@st.dialog("🏢 单位信息维护", width="large")
def render_enterprise_form(mode="edit", initial_data=None, model_name="enterprise", target_table=None):
    
    # 1. 标题与基础数据准备
    form_title = "🆕 新增往来单位" if mode == "add" else f"✏️ 编辑单位信息: {initial_data.get('biz_code', '')}"
    current_data = initial_data if mode == "edit" else {'biz_code': crud.generate_biz_code(target_table, prefix_char="ENT")}
    
    # 2. 🟢 统一常量控制网关：定义隐藏和只读字段
    # 彻底隐藏系统底层字段以及给 AI 预留的 extra_props，保持前端纯净
    FORM_HIDDEN_FIELDS = ['id', 'deleted_at', 'source_file', 'sheet_name', 'extra_props', 'created_at', 'updated_at']
    # 如果是编辑模式，锁死业务编号防篡改
    FORM_READONLY_FIELDS = ['biz_code'] if mode == "edit" else []

    # 3. 🟢 直接呼叫偷懒神器画表单！
    result = ui.render_dynamic_form(
        model_name=model_name,
        form_title=form_title,
        existing_data=current_data,
        hidden_fields=FORM_HIDDEN_FIELDS,
        readonly_fields=FORM_READONLY_FIELDS
    )
    
    # 4. 接管保存逻辑
    if result:
        # 补全 biz_code 防止意外丢失
        if not result.get('biz_code'):
            result['biz_code'] = current_data.get('biz_code')
            
        target_id = int(initial_data.get('id')) if mode == "edit" and initial_data else None
        
        # 调用后端通用写入引擎
        success, msg = crud.upsert_dynamic_record(
            model_name=model_name, 
            data_dict=result, 
            record_id=target_id
        )
        
        if success:
            ui.show_toast_success("单位信息保存成功！")
            st.rerun()
        else:
            ui.show_toast_error(f"保存失败: {msg}")

# ==================== 2.5 时光机弹窗 (新增) ====================
@st.dialog("🕰️ 时光机：数据变更轨迹", width="large")
def show_audit_log_dialog(biz_code, model_name):
    ui.render_audit_timeline(biz_code, model_name)

# =========================================================
# 3. 主页面显示逻辑
# =========================================================
st.title("🏢 往来单位库管理")
st.caption("集中管理所有甲方、分包商及供应商的基础资信信息。")

# 🟢 自动寻址与初始化选项
all_models = cfg.load_data_rules().get("models", {})
model_options = [m for m, config in all_models.items() if "project" not in m.lower()]

if not model_options:
    st.warning("⚠️ 暂未在 app_config.json 中找到非项目的业务模型 (如 enterprise)。请先配置。")
    st.stop()

default_idx = model_options.index("enterprise") if "enterprise" in model_options else 0

# --- 搜索与工具栏 ---
selected_model = st.selectbox("选择库类型", model_options, index=default_idx)
target_table = all_models[selected_model].get("table_name", "biz_enterprises")
c_search, c_add = st.columns([3, 1])
   
with c_search:
    
    keyword = st.text_input("快速搜索", placeholder="输入名称或税号...", label_visibility="collapsed")
    show_deleted = st.checkbox("🗑️ 查看回收站 (已删除单位)") 
with c_add:
    if st.button("➕ 新增单位", type="primary", width="stretch"):
        render_enterprise_form(mode="add", model_name=selected_model, target_table=target_table)

st.divider()

# --- 🟢 V2.0 查询逻辑 (去重版) ---
try:
    delete_condition = "deleted_at IS NOT NULL" if show_deleted else "deleted_at IS NULL"
    
    if keyword:
        # 🟢 修复：将公司名称 (company_name)、信用代码 (uscc)、联系人等关键字段都加入模糊搜索
        query = f"""
            SELECT * FROM "{target_table}" 
            WHERE {delete_condition} 
            AND (
                biz_code LIKE %s OR 
                company_name LIKE %s OR 
                uscc LIKE %s OR
                contact_person LIKE %s OR
                extra_props::text LIKE %s
            )
            ORDER BY updated_at DESC
        """
        # 有 5 个 %s，所以 params 里要传 5 个 keyword
        search_term = f"%{keyword}%"
        df_result = pd.read_sql_query(query, sql_engine, params=(search_term, search_term, search_term, search_term, search_term))
    else:
        query = f'SELECT * FROM "{target_table}" WHERE {delete_condition} ORDER BY updated_at DESC LIMIT 100'
        df_result = pd.read_sql_query(query, sql_engine)
except Exception as e:
    st.error(f"查询失败: {e}")
    df_result = pd.DataFrame()

# --- 结果展示 ---
st.subheader(f"📋 检索结果 ({len(df_result)} 条记录)")

if not df_result.empty:
    drop_cols = ['id', 'deleted_at', 'source_file', 'sheet_name', 'extra_props']
    display_df = df_result.drop(columns=[c for c in drop_cols if c in df_result.columns])
    rules = cfg.load_data_rules()
    field_meta = rules.get("models", {}).get(selected_model, {}).get("field_meta", {})
    
    # 自动生成类似 {"company_name": "单位名称", "uscc": "统一信用代码"} 的翻译字典
    rename_map = {col: meta.get("label", col) for col, meta in field_meta.items()}
    rename_map.update({
        "biz_code": "单位编号",
        "created_at": "创建时间",
        "updated_at": "最近修改",
        "status": "当前状态"
    })
    display_df = display_df.rename(columns=rename_map)
    event = st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        on_select="rerun", 
        selection_mode="single-row"
    )
    
    # --- 底部智能操作栏 ---
    if len(event.selection.rows) > 0:
        selected_index = event.selection.rows[0]
        selected_row = df_result.iloc[selected_index]
        current_biz_code = selected_row.get('biz_code', '未命名')
        
        st.info(f"📍 当前选中: **{current_biz_code}**")
        
        # 🟢 回收站模式
        if show_deleted:
            if st.button("♻️ 恢复此单位 (撤销删除)", type="primary", width="stretch"):
                sql = f'UPDATE "{target_table}" SET deleted_at = NULL WHERE id = %s'
                success, msg = execute_raw_sql(sql, (int(selected_row['id']),))
                if success:
                    st.success(f"✅ [{current_biz_code}] 已成功恢复！")
                    st.rerun()
                else:
                    st.error(f"恢复失败: {msg}")
                    
        # 🟢 正常模式
        else:
            ac1, ac2, ac3 = st.columns([1, 1, 1]) 
            with ac1:
                if st.button("📝 修改信息", type="primary", width="stretch"):
                    render_enterprise_form(mode="edit", initial_data=selected_row, model_name=selected_model, target_table=target_table)
            with ac2:
                if st.button("🕰️ 查看操作历史", width="stretch"):
                    show_audit_log_dialog(current_biz_code, selected_model)
            with ac3:
                if st.button("🗑️ 删除此单位 (软删除)", type="secondary", width="stretch"):
                    sql = f'UPDATE "{target_table}" SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s'
                    success, msg = execute_raw_sql(sql, (int(selected_row['id']),))
                    if success:
                        st.success("✅ 数据已移入回收站。")
                        st.rerun()
                    else:
                        st.error(f"删除失败: {msg}")
else:
    st.info("数据为空，或未找到匹配项。")

# 调试工具
debug_kit.execute_debug_logic()