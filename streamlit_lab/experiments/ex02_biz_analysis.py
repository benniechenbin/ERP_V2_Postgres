import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from backend.utils import formatters as fmt
from backend.config import config_manager as cfg

def run(df, conn):
    """
    🚀 实验室插件入口
    df: 宿主传来的当前表数据 (已过滤 is_active)
    conn: 宿主传来的数据库连接
    """
    st.subheader("📊 经营与债权深度分析 (实验室插件)")

    # --- 1. 数据预处理 (复用原有的清洗逻辑，但针对传入的 df) ---
    # 强制将列名翻译成英文标准列 (确保后续逻辑不挂)
    rules = cfg.load_data_rules()
    mapping = rules.get("column_mapping", {})
    reverse_mapping = {ch_key: eng_key for eng_key, ch_list in mapping.items() for ch_key in ch_list}
    df = df.rename(columns=reverse_mapping)

    # 强转日期与年份
    if 'sign_date' in df.columns:
        df['dt_sign'] = pd.to_datetime(df['sign_date'], errors='coerce')
        df['sign_year'] = df['dt_sign'].dt.year.fillna(datetime.now().year).astype(int)
    
    # 强转金额
    df['val_contract'] = df['contract_amount'].apply(fmt.safe_float)
    df['val_collection'] = df['total_collection'].apply(fmt.safe_float) if 'total_collection' in df.columns else 0.0
    df['val_uncollected'] = df['val_contract'] - df['val_collection']

    # --- 2. 交互式筛选 (在插件内部的小型控件) ---
    valid_years = sorted(df[df['sign_year'] > 1900]['sign_year'].unique().tolist(), reverse=True)
    if not valid_years:
        st.warning("当前表无可分析的年份数据。")
        return

    analysis_year = st.sidebar.selectbox("📅 实验分析年份", valid_years, key="exp_year_sel")

    # --- 3. 核心可视化逻辑 ---
    df_year = df[df['sign_year'] == analysis_year]
    
    col1, col2 = st.columns(2)
    with col1:
        # 负责人合同分布 (饼图)
        fig_pie = px.pie(df_year, values='val_contract', names='manager', title=f"{analysis_year} 负责人合同贡献")
        st.plotly_chart(fig_pie, width="stretch")
    
    with col2:
        # 欠款排名 (条形图)
        df_debt = df_year.sort_values('val_uncollected', ascending=False).head(10)
        fig_bar = px.bar(df_debt, x='project_name', y='val_uncollected', title=f"{analysis_year} TOP 10 欠款项目")
        st.plotly_chart(fig_bar, width="stretch")

    # --- 4. 数据透视表展示 ---
    with st.expander("查看当前实验原始数据摘要"):
        st.dataframe(df_year[['project_name', 'manager', 'val_contract', 'val_uncollected']], width="stretch")