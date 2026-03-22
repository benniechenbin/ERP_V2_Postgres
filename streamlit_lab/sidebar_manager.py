import sys
from pathlib import Path
import streamlit as st
from backend import database as db
from backend.config import config_manager as cfg
import debug_kit
import time

def render_sidebar():
    """
    [精简版] 侧边栏：仅保留页面导航、版本信息与 Debug 开关
    """

    st.sidebar.header("🎛️ 项目管理控制台")
    st.sidebar.divider()

    # =========================================================
    # 1. 页面导航区 (移除数据库显示和切换逻辑)
    # =========================================================
    st.sidebar.page_link("app.py", label="系统首页", icon="🏠") # 新增：回首页
    st.sidebar.page_link("pages/01_📂_项目看板.py", label="项目看板", icon="📂")
    st.sidebar.page_link("pages/02_🛠️_主合同管理.py", label="主合同管理", icon="🛠️")
    st.sidebar.page_link("pages/03_🛠️_分包合同管理.py", label="分包合同管理", icon="🛠️")
    st.sidebar.page_link("pages/04_📊_数据分析.py", label="数据分析", icon="📊")
    st.sidebar.page_link("pages/05_🏢_往来单位.py", label="往来单位", icon="🏢")
    st.sidebar.page_link("pages/06_📥_导入Excel.py", label="导入数据", icon="📥")
    st.sidebar.page_link("pages/07_⚙️_系统管理.py", label="系统管理", icon="⚙️")
    
    # 2. 开发者模式
    debug_kit.render_debug_sidebar()

    st.sidebar.divider()
    st.sidebar.caption(f"Ver: {cfg.APP_VERSION} (Build {cfg.BUILD_DATE})")
    st.sidebar.caption("© 2026 陈斌")

