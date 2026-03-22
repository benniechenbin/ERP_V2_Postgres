import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 🟢 寻路魔法：向上 2 级找到根目录
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# 接入新底座
from backend.database import crud_base
from backend.database.db_engine import get_connection
from backend.config import config_manager as cfg
import sidebar_manager
import debug_kit

try:
    from backend.services.ai_service import AIService  
except ImportError:
    pass

st.set_page_config(layout="wide", page_title="项目全局看板", page_icon="🏠")

# =========================================================
# 🤖 AI 弹窗逻辑 (保留原有的核心竞争力)
# =========================================================
@st.dialog("🤖 AI 智能项目分析", width="large")
def show_ai_search_dialog(keyword, initial_df):
    try:
        ai_svc = AIService()
    except Exception:
        st.error("AI 模块未加载")
        return
        
    if not ai_svc.is_available:
        st.error("❌ 本地 AI 服务未启动 (Ollama)。请先运行 `ollama serve`。")
        return

    models = ai_svc.get_available_models()
    if not models:
        st.warning("⚠️ 未检测到模型，请先运行 `ollama pull deepseek-r1`")
        return
    
    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(f"当前分析范围：基于筛选条件命中的 {len(initial_df)} 个项目")
    with c2:
        selected_model = st.selectbox("🧠 选择模型", models, index=0, label_visibility="collapsed")

    if initial_df.empty:
        st.warning("当前搜索结果为空，无法分析。")
        return

    # 数据清洗与压缩 (Token 优化)
    clean_data = []
    max_items = st.slider("📊 分析样本量 (防止 Token 爆炸)", 10, 100, 30)
    target_archives = initial_df.head(max_items)
    
    for _, row in target_archives.iterrows():
        c_amount = float(row.get('contract_amount') or 0)
        collection = float(row.get('total_collected') or 0)
        
        if c_amount > 0 or collection > 0:
            clean_data.append({
                "项目": row.get('project_name', '未知'),
                "负责人": row.get('manager', '未知'),
                "合同额": f"{c_amount/10000:.2f}万",
                "回款率": f"{(collection/c_amount*100):.1f}%" if c_amount > 0 else "0%",
                "欠款": f"{(c_amount - collection)/10000:.2f}万"
            })
            
    with st.expander(f"查看投喂给 AI 的数据摘要 ({len(clean_data)} 条)"):
        st.json(clean_data[:3])
        st.caption("...等更多数据")

    st.divider()
    q = st.text_area("🗣️ 设定 AI 分析指令：", value="分析这些项目的回款风险，找出回款率低于30%的重点项目，并给出催款建议。", height=100)
    
    if st.button("🚀 开始 AI 分析", type="primary", width="stretch"):
        if not clean_data:
            st.error("有效数据不足（金额均为0），无法分析。")
            return
            
        st.write("### 💡 AI 诊断报告")
        container = st.empty()
        full_text = ""
        try:
            for chunk in ai_svc.analyze_stream(selected_model, clean_data, q):
                full_text += chunk
                container.markdown(full_text + "▌")
            container.markdown(full_text)
        except Exception as e:
            st.error(f"分析中断: {e}")

# =========================================================
# 🚨 独立风控查询：30 天内待收款预警
# =========================================================
@st.cache_data(ttl=60)
def load_urgent_receivables():
    """直接使用 SQL 跨表联查，抓取近期需催收的款项"""
    conn = get_connection()
    try:
        sql = """
            SELECT 
                m.project_name AS "项目名称", 
                m.manager AS "负责人",
                p.milestone_name AS "收款节点", 
                p.planned_amount AS "计划金额", 
                p.planned_date AS "预计日期"
            FROM biz_payment_plans p
            JOIN biz_main_contracts m ON p.main_contract_code = m.biz_code
            WHERE p.deleted_at IS NULL AND m.deleted_at IS NULL
              AND p.planned_amount > 0
              AND p.planned_date <= CURRENT_DATE + INTERVAL '30 days'
            ORDER BY p.planned_date ASC
        """
        df = pd.read_sql_query(sql, conn)
        return df
    except Exception as e:
        print(f"获取预警失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

# =========================================================
# 1. 页面基础框架
# =========================================================
sidebar_manager.render_sidebar()

col_title, col_ai = st.columns([4, 1])
with col_title:
    st.title("🏠 项目全局指挥中心")
    st.caption("PMO 视角：全生命周期健康度监控与资金透视。")

# 🟢 加载 V2.0 主合同数据
df_main = crud_base.fetch_dynamic_records('main_contract')

if df_main.empty:
    st.info("📦 当前系统暂无项目数据，请前往【主合同管理】或【数据导入】录入。")
    st.stop()

# 数据类型强转兜底
df_main['contract_amount'] = pd.to_numeric(df_main['contract_amount'], errors='coerce').fillna(0.0)
df_main['total_collected'] = pd.to_numeric(df_main.get('total_collected', 0), errors='coerce').fillna(0.0)

# =========================================================
# 2. 预警雷达 (30天内到期资金)
# ==========================================
df_urgent = load_urgent_receivables()
if not df_urgent.empty:
    total_urgent = df_urgent['计划金额'].sum()
    st.error(f"🚨 **资金红绿灯**：未来 30 天内共有 **{len(df_urgent)}** 笔款项即将到期/已逾期，涉及总金额 **¥ {total_urgent:,.2f}**，请重点督办！")
    
    with st.expander("👀 查看重点催收清单"):
        st.dataframe(
            df_urgent, 
            hide_index=True, 
            width="stretch",
            column_config={
                "预计日期": st.column_config.DateColumn("预计日期", format="YYYY-MM-DD"),
                "计划金额": st.column_config.NumberColumn("计划金额 (元)", format="¥ %.2f")
            }
        )

# =========================================================
# 3. 仿 v0 数据过滤区 (Data Filter)
# =========================================================
st.markdown("---")

c_search, c_stage, c_manager = st.columns([2, 1, 1])

with c_search:
    search_kw = st.text_input("🔍 搜索项目名称/编号...", placeholder="例如：上海大厦...")

with c_stage:
    # 提取存在的状态
    stages = ["全部"] + [s for s in df_main['project_stage'].unique().tolist() if str(s) != 'nan']
    sel_stage = st.selectbox("📌 项目阶段", stages)

with c_manager:
    managers = ["全部"] + [m for m in df_main['manager'].unique().tolist() if str(m) != 'nan']
    sel_manager = st.selectbox("👤 负责人", managers)

# 执行内存级过滤
df_view = df_main.copy()

if search_kw:
    mask = df_view['project_name'].astype(str).str.contains(search_kw, case=False) | \
           df_view['biz_code'].astype(str).str.contains(search_kw, case=False)
    df_view = df_view[mask]

if sel_stage != "全部":
    df_view = df_view[df_view['project_stage'] == sel_stage]

if sel_manager != "全部":
    df_view = df_view[df_view['manager'] == sel_manager]

with col_ai:
    st.write("") # 占位
    if st.button("✨ 唤醒 AI 诊断", type="primary", width="stretch", disabled=df_view.empty):
        show_ai_search_dialog(search_kw or "当前全盘", df_view)

# =========================================================
# 4. 仿 v0 高级数据表格 (Data Table)
# =========================================================
st.caption(f"为您检索到 **{len(df_view)}** 个项目记录。")

# 准备展示列
display_cols = {
    'biz_code': '合同编号',
    'project_name': '项目名称',
    'manager': '负责人',
    'project_stage': '状态', 
    'contract_amount': '合同额',
    'total_collected': '已回款'
}

df_display = df_view[list(display_cols.keys())].rename(columns=display_cols).copy()
df_display['欠款金额'] = df_display['合同额'] - df_display['已回款']
df_display['回款进度'] = (df_display['已回款'] / df_display['合同额']) * 100
df_display['回款进度'] = df_display['回款进度'].fillna(0)

# 定义动态高度
height = min((len(df_display) + 1) * 35 + 3, 650)

st.dataframe(
    df_display,
    width="stretch",
    height=height,
    hide_index=True,
    column_config={
        "合同编号": st.column_config.TextColumn("合同编号", width="small"),
        "项目名称": st.column_config.TextColumn("项目名称", width="medium"),
        "状态": st.column_config.TextColumn("阶段/状态", width="small"),
        "合同额": st.column_config.NumberColumn("合同额 (元)", format="¥ %.2f"),
        "已回款": st.column_config.NumberColumn("已回款 (元)", format="¥ %.2f"),
        "欠款金额": st.column_config.NumberColumn("🔴 欠款金额 (元)", format="¥ %.2f"),
        "回款进度": st.column_config.ProgressColumn("回款进度", format="%.1f%%", min_value=0, max_value=100)
    }
)

debug_kit.execute_debug_logic()