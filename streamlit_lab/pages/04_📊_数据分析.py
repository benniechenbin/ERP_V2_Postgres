import sys
from pathlib import Path
from backend.database.db_engine import get_connection

# ==========================================
# 🟢 寻路魔法
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import plotly.express as px

# 接入新底座
from backend import database as db
from backend.config import config_manager as cfg
from backend.utils import formatters as ut

import sidebar_manager
import debug_kit
import components as ui

try:
    from ai_service import AIService  
except ModuleNotFoundError:
    pass

st.set_page_config(page_title="经营分析", page_icon="📊", layout="wide")
sidebar_manager.render_sidebar()

# =========================================================
# 🛠️ 工具函数：数据清洗与加载
# =========================================================


@st.cache_data(ttl=2) 
def load_analysis_data():
    """加载全量项目数据（绕过 db_manager 的拦截，直接查物理表）"""
    conn = db.get_connection()
    try:
        all_tables = db.get_all_data_tables()
        if not all_tables:
            return pd.DataFrame(), "未找到数据表"

        df_list = []
        for tbl in all_tables:
            # 🟢 修正 1：V2.0 架构中，有效数据不再用 is_active，而是用 deleted_at IS NULL
            query = f'SELECT * FROM "{tbl}" WHERE deleted_at IS NULL'
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    # 🟢 修正 2：把报错的 engine 换成原生的 conn！
                    tmp_df = pd.read_sql_query(query, conn) 
                
                if not tmp_df.empty:
                    tmp_df['origin_table'] = tbl 
                    df_list.append(tmp_df)
            except Exception as e:
                print(f"读取表 {tbl} 失败: {e}")
                
        if not df_list:
            return pd.DataFrame(), "所有表均无有效数据"
            
            
        df = pd.concat(df_list, ignore_index=True)

        # ==========================================
        # 🟢 终极修复：强制中英文字段映射！
        # ==========================================
        rules = cfg.load_data_rules()
        mapping = rules.get("column_mapping", {})
        
        # 构建反向映射字典
        reverse_mapping = {}
        for eng_key, ch_list in mapping.items():
            for ch_key in ch_list:
                reverse_mapping[ch_key] = eng_key
                
        # 强行把所有中文列翻译成英文标准列
        df.rename(columns=reverse_mapping, inplace=True)
        # ==========================================

        # 保底检查
        if 'sign_date' not in df.columns or 'contract_amount' not in df.columns:
            return pd.DataFrame(), f"关键列缺失。当前列: {df.columns.tolist()}"

        # 1. 强转日期
        df['dt_sign'] = pd.to_datetime(df['sign_date'], errors='coerce')
        df['sign_year'] = df['dt_sign'].dt.year.fillna(datetime.now().year).astype(int) 
        
        # 2. 强转金额 (使用你神级的 ut.safe_float)
        df['val_contract'] = df['contract_amount'].apply(ut.safe_float)
        df['val_collection'] = df['total_collection'].apply(ut.safe_float) if 'total_collection' in df.columns else 0.0
        
        # 3. 计提逻辑
        if 'contract_retention' in df.columns:
            df['val_uncollected'] = df['contract_retention'].apply(ut.safe_float)
        else:
            df['val_uncollected'] = df['val_contract'] - df['val_collection']
        
        df['project_name_safe'] = df['project_name'].fillna('未知项目') if 'project_name' in df.columns else '未知项目'
        df['manager_safe'] = df['manager'].fillna('未知') if 'manager' in df.columns else '未知'
        
        return df, "OK"
    finally:
        # 极度规范：用完数据库连接必须关闭
        conn.close()

# =========================================================
# 🟢 页面逻辑
# =========================================================

st.title("📊 年度经营与债权分析 (Pro)")
ui.style_metric_card()
st.caption("全生命周期视角：基于 Plotly 交互式引擎的深度资金盘点。")

df_all, msg = load_analysis_data()

if df_all.empty:
    st.error(f"⚠️ 无法加载数据: {msg}")
    st.stop()

current_year = datetime.now().year

st.markdown("##### ⏳ 分析周期设定")
with st.container(border=True):
    c_start, c_end, _ = st.columns([1, 1, 2])
    with c_start:
        start_date = st.date_input("📅 起始时间", value=datetime(current_year, 1, 1).date())
    with c_end:
        end_date = st.date_input("📅 截止时间", value=datetime.now().date())

st.divider()

# =========================================================
# 🟢 全局数据切片 (基于真实时间轴过滤)
# =========================================================
start_ts = pd.to_datetime(start_date)
end_ts = pd.to_datetime(end_date)
# 1. 本期新签 (签约时间在选定时间段内的)
mask_new = (df_all['dt_sign'] >= start_ts) & (df_all['dt_sign'] <= end_ts)
df_new = df_all[mask_new].copy()

# 2. 往期结转
mask_carry = (df_all['dt_sign'] < start_ts) & (df_all['val_contract'] > 10)
df_carry = df_all[mask_carry].copy()

# 指标计算
new_contract_sum = df_new['val_contract'].sum()
new_collection_sum = df_new['val_collection'].sum()
carry_debt_sum = df_carry['val_uncollected'].sum()
total_debt = df_new['val_uncollected'].sum() + carry_debt_sum

# 为了不修改下方的代码，我们动态伪装一个 analysis_year 变量给下面用
analysis_year = f"{start_date.strftime('%Y-%m')} 至 {end_date.strftime('%Y-%m')}"

# --- 宏观看板 ---
k1, k2, k3, k4 = st.columns(4)
k1.metric(f"{analysis_year}年 新签合同额", f"¥ {new_contract_sum/10000:,.1f} 万", f"{len(df_new)} 个项目")
k2.metric("本年新签回款率", f"{(new_collection_sum/new_contract_sum*100):.1f}%" if new_contract_sum else "0.0%", f"回款: ¥{new_collection_sum/10000:.1f}万", delta_color="off")
k3.metric("往年结转欠款", f"¥ {carry_debt_sum/10000:,.1f} 万", "存量风险", delta_color="inverse")
k4.metric("全盘总应收账款", f"¥ {total_debt/10000:,.1f} 万", "需催收总额", delta_color="inverse")

# =========================================================
# 📊 深度分析 (Plotly 升级版)
# =========================================================
st.markdown("### 🔍 结构化分析")
tab1, tab2 = st.tabs(["📉 往年结转·清欠分析", "🚀 本年新签·进度分析"])

# --- Tab 1: 往年坏账分析 ---
with tab1:
    c_chart, c_list = st.columns([1.2, 0.8])
    
    # 筛选欠款 > 1000 的项目
    df_carry_debt = df_carry[df_carry['val_uncollected'] > 1000].sort_values('val_uncollected', ascending=False)
    
    with c_chart:
        st.subheader("往年欠款年份分布")
        if not df_carry_debt.empty:
            # 聚合数据
            debt_by_year = df_carry_debt.groupby('sign_year')['val_uncollected'].sum().reset_index()
            
            # 🔥 Plotly 交互图表
            fig = px.bar(
                debt_by_year, 
                x="sign_year", 
                y="val_uncollected",
                text_auto='.2s', # 自动显示数值 (如 1.5M)
                labels={"sign_year": "签约年份", "val_uncollected": "剩余欠款金额"},
                color="val_uncollected",
                color_continuous_scale="Reds" # 颜色越深欠款越多
            )
            fig.update_layout(xaxis_type='category') # 强制年份显示为分类，不显示小数年份
            st.plotly_chart(fig, width="stretch")
            
            st.caption("💡 提示：鼠标悬停在柱子上可查看精确金额。")
        else:
            st.success("🎉 完美！无往年结转欠款。")

    with c_list:
        st.subheader("💀 TOP 10 风险欠款大户")
        
        # 🟢 1. 计算未收比例 (重点：在这里直接乘以 100！)
        df_carry['uncollected_rate'] = df_carry.apply(
            lambda x: (x['val_uncollected'] / x['val_contract'] * 100) if x['val_contract'] > 0 else 0, 
            axis=1
        )
        
        # 🟢 2. 核心业务逻辑
        # 因为上面乘了 100，所以这里的 0.20 要改成 20 (代表 20%)
        mask_risk = (df_carry['val_uncollected'] > 10000) & (df_carry['uncollected_rate'] > 20)
        df_carry_debt = df_carry[mask_risk].sort_values('val_uncollected', ascending=False)

        if not df_carry_debt.empty:
            st.dataframe(
                df_carry_debt.head(10)[['project_name_safe', 'manager_safe', 'val_contract', 'val_uncollected', 'uncollected_rate']],
                column_config={
                    "project_name_safe": "项目名称",
                    "manager_safe": "负责人",
                    "val_contract": st.column_config.NumberColumn("合同额", format="¥ %.0f"),
                    "val_uncollected": st.column_config.NumberColumn("高危欠款", format="¥ %.0f"),
                    # 🟢 3. 把最大值 (max_value) 从 1 改成 100
                    "uncollected_rate": st.column_config.ProgressColumn("欠款比例", format="%.1f%%", min_value=0, max_value=100) 
                },
                hide_index=True,
                width="stretch",
                height=380
            )
        else:
            st.success("暂无高危欠款项目")

# --- Tab 2: 本年业绩分析 ---
with tab2:
    if not df_new.empty:
        st.subheader(f"{analysis_year}年 部门/负责人 业绩对比")
        
        # 聚合数据
        by_manager = df_new.groupby('manager_safe')[['val_contract', 'val_collection']].sum().reset_index()
        by_manager = by_manager.sort_values('val_contract', ascending=False).head(15)
        
        # 🔥 Plotly 分组柱状图 (Grouped Bar)
        # 将数据宽转长 (Melt) 以便 Plotly 分组
        df_melt = by_manager.melt(id_vars='manager_safe', value_vars=['val_contract', 'val_collection'], var_name='类型', value_name='金额')
        # 汉化图例
        df_melt['类型'] = df_melt['类型'].map({'val_contract': '合同额', 'val_collection': '已回款'})
        
        fig2 = px.bar(
            df_melt, 
            x="manager_safe", 
            y="金额", 
            color="类型",
            barmode="group", # 分组并排显示
            text_auto='.2s',
            color_discrete_map={"合同额": "#4CAF50", "已回款": "#FFC107"}, # 自定义商务配色
            labels={"manager_safe": "负责人/部门"}
        )
        st.plotly_chart(fig2, width="stretch")
    else:
        st.info(f"{analysis_year} 年暂无新签项目。")

# --- AI 简报 ---
st.markdown("---")
st.subheader("📑 智能管理层报告 (CFO 视角)")
st.caption("基于上述宏观图表（新签、结转、坏账比例），自动生成结构化的年度经营诊断与风控警示。")

# 采用卡片式的 UI 包装，显得更正式
with st.container(border=True):
    st.markdown("报告将包含以下维度：\n* 资金盘面健康度综合评估\n* 历史遗留坏账的系统性成因推测\n* 下一季度核心 KPI 优化建议")
    
    if st.button("✨ 一键生成经营诊断书", type="primary"):
        # 🟢 预留给二期工程的解耦占位提示
        st.info("💡 架构解耦准备中：此处宏观数据的整合逻辑及 CFO 提示词，将在二期工程中抽离至独立的 `prompts.py` 模块。")
        # 实际功能暂时悬空

debug_kit.execute_debug_logic()