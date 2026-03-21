import sys
from pathlib import Path

# ==========================================
# 🟢 寻路魔法：向上 3 级找到 ERP_V2_PRO 根目录
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from datetime import datetime
import json

# 接入新底座
from backend import database as db
from backend.config import config_manager as cfg
from backend.utils import formatters as ut

# 接入同级的前端组件
import sidebar_manager
import debug_kit 
import components as ui
try:
    from backend.services import AIService  
except ImportError:
    pass


st.set_page_config(layout="wide", page_title="项目看板")

# =========================================================
# 🟢 AI 弹窗逻辑 (放在最前面定义，方便调用)
# =========================================================
@st.dialog("🤖 AI 智能项目分析", width="large")
def show_ai_search_dialog(keyword, initial_df):
    """
    keyword: 当前搜索词
    initial_df: 当前已筛选出的 DataFrame (避免重复查询数据库)
    """
    # 1. 初始化服务
    ai_svc = AIService()
    
    if not ai_svc.is_available:
        st.error("❌ 本地 AI 服务未启动 (Ollama)。请先运行 `ollama serve`。")
        st.info("💡 提示：这是一个离线功能，您的数据不会上传到互联网。")
        return

    # 2. 获取模型
    models = ai_svc.get_available_models()
    if not models:
        st.warning("⚠️ 未检测到模型，请先运行 `ollama pull deepseek-r1`")
        return
    
    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(f"当前分析范围：基于搜索词 `{keyword}` 命中的 {len(initial_df)} 个项目")
    with c2:
        selected_model = st.selectbox("🧠 选择模型", models, index=0, label_visibility="collapsed")

    if initial_df.empty:
        st.warning("当前搜索结果为空，无法分析。")
        return

    # 3. 数据清洗与压缩 (Token 优化)
    # 只提取 AI 需要的核心字段，减少无关干扰
    clean_data = []
    
    # 限制分析条数 (防止 Context Window 爆炸)
    max_items = st.slider("📊 分析样本量 (按更新时间倒序)", 10, 100, 30)
    target_archives = initial_df.head(max_items)
    
    for _, row in target_archives.iterrows():
        # 安全获取字段 (兼容中英文列名)
        p_name = row.get('project_name') or row.get('项目名称')
        manager = row.get('manager') or row.get('项目经理') or row.get('负责人')
          
        c_amount = ut.safe_float(row.get('contract_amount') or row.get('当年合同额') or 0)
        collection = ut.safe_float(row.get('total_collection') or row.get('实收款') or 0)
        
        # 只有有金额的项目才值得分析
        if c_amount > 0 or collection > 0:
            clean_data.append({
                "项目": p_name,
                "负责人": manager,
                "合同额": f"{c_amount/10000:.2f}万", # 换算成万，节省 Token
                "回款率": f"{(collection/c_amount*100):.1f}%" if c_amount > 0 else "0%",
                "欠款": f"{(c_amount - collection)/10000:.2f}万"
            })
    
    # 预览数据摘要
    with st.expander(f"查看投喂给 AI 的数据摘要 ({len(clean_data)} 条)", expanded=False):
        st.json(clean_data[:3])
        st.caption("...等更多数据")

    # 4. 提问交互
    st.divider()
    q = st.text_area("🗣️ 对这批项目下达分析指令：", value="分析这些项目的回款风险，找出回款率低于30%的重点项目，并给出催款建议。", height=100)
    
    if st.button("🚀 开始 AI 分析", type="primary", width="stretch"):
        if not clean_data:
            st.error("有效数据不足（金额均为0），无法分析。")
            return
            
        st.write("### 💡 AI 分析报告")
        container = st.empty()
        full_text = ""
        
        # ✨ 流式输出
        try:
            for chunk in ai_svc.analyze_stream(selected_model, clean_data, q):
                full_text += chunk
                container.markdown(full_text + "▌")
            container.markdown(full_text) # 最后移除光标
        except Exception as e:
            st.error(f"分析中断: {e}")

# =========================================================
# 1. 基础页面框架
# =========================================================
sidebar_manager.render_sidebar()

# 标题区
col_title, col_toggle = st.columns([4, 1])
with col_title:
    st.title("📊 项目全景看板")

# 获取所有表
all_tables = db.get_all_data_tables()
if not all_tables:
    st.info(f"当前账套为空，请先导入数据。")
    st.stop()

# 选择表 (极简模式)
selected_table = st.selectbox(
    "选择数据表", 
    all_tables,
    format_func=ui.remove_prefix_formatter("data_"),
    label_visibility="collapsed"
)

# 3. 获取全量数据 (Base Data)
df_base = db.get_all_projects(table_name=selected_table)

if df_base.empty:
    st.info("暂无数据。")
    st.stop()

# =========================================================
# 🟢 新增：搜索与筛选区域
# =========================================================
st.markdown("---") # 分割线

# 搜索状态初始化
if "main_search_key" not in st.session_state:
    st.session_state["main_search_key"] = ""

with st.container():
    c_scope, c_input, c_btn, c_ai = st.columns([1.5, 3, 0.8, 1])
    
    with c_scope:
        search_scope = st.radio(
            "搜索范围", 
            ["全局模糊", "项目名称", "负责人"],
            index=0, 
            horizontal=True,
            label_visibility="collapsed"
        )
        
    with c_input:
        search_key = st.text_input(
            "搜索", 
            value=st.session_state["main_search_key"],
            placeholder=f"在 {len(df_base)} 条数据中搜索...", 
            label_visibility="collapsed"
        )

    with c_btn:
        if st.button("🔍", width="stretch", type="primary"):
            st.session_state["main_search_key"] = search_key
            st.rerun()
with st.expander("📅 按合同签订日期筛选 (Time Range)", expanded=False):
    # 1. 自动寻找日期列
    date_col = None
    target_key = [k for k,v in cfg.STANDARD_FIELDS.items() if "sign_date" in k]
    if target_key and target_key[0] in df_base.columns:
        date_col = target_key[0]
    else:
        possible = [c for c in df_base.columns if "日期" in str(c) or "date" in str(c).lower()]
        if possible: date_col = possible[0]

    # 初始化筛选开关状态
    is_time_filter_active = False
    start_date_input = None
    end_date_input = None

    if date_col:
        # 数据清洗
        df_base[date_col] = pd.to_datetime(df_base[date_col], errors='coerce')
        min_d, max_d = df_base[date_col].min(), df_base[date_col].max()
        
        if pd.notnull(min_d) and pd.notnull(max_d):
            # 🟢 核心改动 1：增加启用开关，默认 False (解决进页面空表问题)
            is_time_filter_active = st.checkbox("启用时间筛选", value=False, key="chk_enable_time_filter")
            
            st.caption(f"数据跨度: {min_d.date()} ~ {max_d.date()}")
            
            # 🟢 核心改动 2：拆分为两个独立的输入框 (解决手输报错问题)
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                start_date_input = st.date_input(
                    "开始日期", 
                    value=min_d, 
                    min_value=min_d, 
                    max_value=max_d,
                    disabled=not is_time_filter_active # 未启用时置灰
                )
            with d_col2:
                end_date_input = st.date_input(
                    "结束日期", 
                    value=max_d, 
                    min_value=min_d, 
                    max_value=max_d,
                    disabled=not is_time_filter_active
                )
        else:
            st.warning("⚠️ 日期列全是空值，无法筛选")
    else:
        st.info("未识别到日期列")

# 执行过滤逻辑
df_filtered = df_base.copy()
keyword = st.session_state["main_search_key"].strip()
if keyword:
    try:
        if search_scope == "项目名称":
            mask = df_filtered['project_name'].astype(str).str.contains(keyword, case=False, na=False)
        elif search_scope == "负责人":
            mask = df_filtered['manager'].astype(str).str.contains(keyword, case=False, na=False)
        else:
            exclude_cols = [
                    'id', 'created_at', 'updated_at', 'source_row', 
                    'is_deleted', 'is_active', 'sheet_name'
            ]
            
            # 2. 动态获取所有参与搜索的业务列
            search_target_cols = [c for c in df_filtered.columns if c not in exclude_cols]
            
            # 3. 执行全表搜索
            # 逻辑：将这些列转为字符串 -> 检查是否包含关键字 -> 只要有一列包含(any)就算命中
            mask = df_filtered[search_target_cols].apply(
                lambda x: x.astype(str).str.contains(keyword, case=False, na=False)
            ).any(axis=1)

        df_filtered = df_filtered[mask]
    except Exception as e:
        st.error(f"搜索发生错误: {e}")

# 日期范围过滤
if date_col and is_time_filter_active and start_date_input and end_date_input:
    # 转换为 Timestamp
    s_ts = pd.Timestamp(start_date_input)
    # 结束日期加一天减一秒，覆盖当天全天 (比如选了20号，要包含20号 23:59:59)
    e_ts = pd.Timestamp(end_date_input) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    mask_date = (df_filtered[date_col] >= s_ts) & (df_filtered[date_col] <= e_ts)
    df_filtered = df_filtered[mask_date]
    
    if len(df_filtered) < len(df_base):
        st.toast(f"📅 时间过滤生效: {start_date_input} -> {end_date_input}")

# 过滤后再提供 AI 分析按钮
with c_ai:
    ai_disabled = df_filtered.empty
    if st.button("✨ AI 分析", width="stretch", disabled=ai_disabled, help="让 AI 分析当前搜索出来的项目"):
        show_ai_search_dialog(keyword, df_filtered)

# =========================================================
# 4. 顶部开关 (放在右上角)
# =========================================================
with col_toggle:
    st.write("")
    st.write("")
    show_all = st.toggle("🕵️‍♂️ 显示全量/空列", value=False)

# =========================================================
# 🟢 核心逻辑：智能视图裁剪 (基于 df_filtered)
# =========================================================
# 注意：这里使用的是 df_filtered 而不是 df_base

# A. 定义黑名单
SYSTEM_COLS = [
    'id', 'source_file', 'sheet_name', 'created_at', 'updated_at', 
    'is_deleted', 'source_row'
]
df_view = df_filtered.drop(columns=[c for c in SYSTEM_COLS if c in df_filtered.columns])

# B. 核心列过滤
if not show_all:
    standard_keys = set(cfg.STANDARD_FIELDS.keys())
    df_view = df_view[[c for c in df_view.columns if c in standard_keys]]

# C. 智能隐藏空列
if not show_all:
    df_view = df_view.replace(r'^\s*$', pd.NA, regex=True)
    df_view = df_view.dropna(axis=1, how='all')

# =========================================================
# 🟢 视觉优化：汉化与格式
# =========================================================

# A. 构建汉化字典
rename_map = {}
for k, v in cfg.STANDARD_FIELDS.items():
    parts = v.split(" ")
    clean_name = parts[1] if len(parts) > 1 else v
    rename_map[k] = clean_name

df_display = df_view.rename(columns=rename_map)

# B. 数据类型适配（确保与列类型兼容）
# 日期列：转为 datetime64[ns]
for c in df_display.columns:
    if ("日期" in c) or ("时间" in c):
        try:
            df_display[c] = pd.to_datetime(df_display[c], errors='coerce')
        except Exception:
            pass
# 金额类：转为数值
for c in df_display.columns:
    if any(k in c for k in ["金额", "额", "价", "费", "收"]):
        try:
            df_display[c] = pd.to_numeric(df_display[c], errors='coerce')
        except Exception:
            pass

# C. 智能格式配置
column_configs = {}
for col_name in df_display.columns:
    if "日期" in col_name or "时间" in col_name:
        column_configs[col_name] = st.column_config.DateColumn(col_name, format="YYYY-MM-DD")
    elif any(k in col_name for k in ["金额", "额", "价", "费", "收","合同保有量"]):
        column_configs[col_name] = st.column_config.NumberColumn(col_name, format="¥ %.2f")
    elif "比例" in col_name or "进度" in col_name:
        column_configs[col_name] = st.column_config.ProgressColumn(col_name, format="%.0f%%", min_value=0, max_value=100)

# =========================================================
# 5. 展示表格
# =========================================================
# 动态显示当前筛选状态
if keyword:
    st.caption(f"🔍 搜索结果: **{len(df_filtered)}** 项 (总计: {len(df_base)}) | 关键词: `{keyword}`")
else:
    st.caption(f"👀 显示全部: **{len(df_filtered)}** 项")

# 动态计算表格高度
height = min((len(df_display) + 1) * 35 + 3, 600)

st.data_editor(
    df_display,
    width='stretch', 
    height=height,   
    hide_index=True,
    disabled=True, 
    column_config=column_configs, 
    key="dashboard_table" 
)

# =========================================================
# 6. 底部高级管理 (表结构维护)
# =========================================================
with st.expander("🛠️ 高级管理 (表结构维护)", expanded=False):
    st.caption("⚠️ 高危操作区域：请谨慎修改表名或删除数据表。")
    
    c_rename, c_delete = st.columns([1, 1])
    
    # --- A. 重命名当前表 ---
    with c_rename:
        st.subheader("📝 重命名工作表")
        # 提取当前的简单名称 (去掉 data_ 前缀)
        curr_simple_name = selected_table.replace("data_", "")
        
        new_name_input = st.text_input(
            "请输入新表名", 
            value=curr_simple_name,
            key="input_rename_table_name",
            help="只允许中文、字母、数字"
        )
        
        if st.button("确认重命名", key="btn_exec_rename"):
            if not new_name_input.strip():
                st.error("名称不能为空")
            elif new_name_input.strip() == curr_simple_name:
                st.info("名称未发生变化")
            else:
                # 调用 db_manager 进行改名
                success, msg = db.rename_data_table(selected_table, new_name_input)
                if success:
                    st.success(f"✅ {msg}")
                    # 强制刷新页面以更新左上角的选择框
                    st.rerun()
                else:
                    st.error(f"❌ 重命名失败: {msg}")

    # --- B. 删除当前表 ---
    with c_delete:
        st.subheader("🗑️ 删除当前表")
        st.markdown(f"当前操作对象：**:red[{selected_table}]**")
        st.warning("🚨 警告：此操作将永久删除该表内的所有项目、流水记录及附件关联，不可恢复！")
        
        # 双重保险：必须勾选才能点按钮
        confirm_check = st.checkbox("我已知晓风险，确认删除", key="chk_confirm_del")
        
        if st.button("💣 彻底删除该表", type="primary", disabled=not confirm_check, key="btn_exec_del"):
            success, msg = db.delete_data_table(selected_table)
            if success:
                st.toast(f"✅ {msg}")
                # 稍微延迟一下让用户看到提示
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ 删除失败: {msg}")

debug_kit.execute_debug_logic()