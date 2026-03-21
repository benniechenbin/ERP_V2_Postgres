import sys
from pathlib import Path

# ==========================================
# 🟢 寻路魔法
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import importlib
import os
import pandas as pd

# 接入新底座
from backend import database as db
from backend.config import config_manager as cfg
import debug_kit
import components as ui

# ==========================================
# 1. 实验室门禁 (Gatekeeper)
# ==========================================
st.set_page_config(page_title="功能实验室", layout="wide", page_icon="🧪")

# 检查开发者模式 (如果没有 debug_kit，可以暂时注释掉下面两行)
if not debug_kit.is_debug_mode():
    st.warning("🚫 此区域仅限开发者访问。请在侧边栏开启 '开发者模式'。")
    st.stop()

st.title("🧪 功能孵化实验室 (Plugin Mode)")
st.caption("插件化架构：内置核心诊断 + 外部实验脚本加载。")

# ==========================================
# 2. 扫描实验卡带 (Scan Plugins)
# ==========================================
EXP_DIR = "experiments"
if not os.path.exists(EXP_DIR):
    os.makedirs(EXP_DIR)

# 扫描文件夹下的所有 .py 文件
external_files = []
try:
    external_files = [f[:-3] for f in os.listdir(EXP_DIR) if f.endswith(".py") and f != "__init__.py"]
    external_files.sort()
except Exception:
    pass

# 🟢 核心改动：构建选项列表 (内置工具 + 外部文件)
BUILTIN_TOOL_NAME = "🏥 数据映射体检 (内置核心)"
menu_options = [BUILTIN_TOOL_NAME] + external_files

# ==========================================
# 3. 侧边栏控制台 (Console)
# ==========================================
with st.sidebar:
    st.header("🎛️ 实验室控制台")
    
    # [A] 选择实验 (混合列表)
    selected_exp = st.radio("选择实验卡带", options=menu_options)
    
    st.divider()
    
    # [B] 选择数据源 (宿主负责)
    all_tables = db.get_all_data_tables()
    if not all_tables:
        st.error("数据库为空，请先导入数据")
        st.stop()
        
    target_table = st.selectbox("🧪 实验目标数据表", all_tables)

# ==========================================
# 🟢 内置功能：数据映射诊断逻辑
# ==========================================
def run_diagnosis_tool(df):
    st.subheader("📊 数据库列名映射体检报告")
    st.info("此工具用于检查：Excel 表头是否被正确识别为系统所需的字段。")

    # 定义标准字典
    REQUIRED_FIELDS = [
        ("project_name", "项目名称", "🔴 必须"),
        ("manager", "负责人", "🔴 必须"),
        ("contract_amount", "合同金额", "🟠 核心(KPI)"),
        ("sign_date", "签约日期", "🟠 核心(年份)"),
        ("total_collection", "累计回款", "🟠 核心(KPI)"),
    ]

    actual_cols = df.columns.tolist()
    results = []

    for sys_key, cn_name, level in REQUIRED_FIELDS:
        # 1. 检查英文 Key 是否直接存在
        if sys_key in actual_cols:
            status = "✅ 完美 (英文匹配)"
            col_found = sys_key
            val = df[sys_key].iloc[0] if len(df) > 0 else "空"
        else:
            # 2. 检查中文映射 (查 config)
            mapped_cn = cfg.STANDARD_FIELDS.get(sys_key)
            if mapped_cn and mapped_cn in actual_cols:
                status = f"✅ 正常 (中文匹配: {mapped_cn})"
                col_found = mapped_cn
                val = df[mapped_cn].iloc[0] if len(df) > 0 else "空"
            else:
                status = "❌ **缺失！**"
                col_found = "未找到"
                val = "-"
        
        results.append({
            "重要性": level,
            "系统字段": sys_key,
            "业务含义": cn_name,
            "诊断结果": status,
            "实际匹配列": col_found,
            "首行样本": str(val)
        })

    # 展示结果
    st.dataframe(
        pd.DataFrame(results), 
        width="stretch", 
        hide_index=True,
        column_config={"诊断结果": st.column_config.TextColumn("状态", width="medium")}
    )

    # 智能提示
    missing = [r for r in results if "缺失" in r["诊断结果"]]
    if missing:
        st.error(f"⚠️ 发现 {len(missing)} 个关键字段缺失！首页 KPI 计算将受到影响。")
        st.markdown("**修复建议：** 请修改 Excel 表头，确保包含上述“业务含义”对应的列名，然后重新导入。")
    else:
        st.success("🎉 字段映射完美！数据结构健康。")
    
    with st.expander("查看原始数据 (Top 5)"):
        st.dataframe(df.head(5))

# ==========================================
# 4. 宿主加载器 (Host Loader)
# ==========================================
if target_table:
    # --- Step 1: 宿主建立连接 ---
    conn = db.get_readonly_connection()
    if not conn:
        st.stop()

    try:
        # --- Step 2: 预加载数据 ---
        df = pd.read_sql(f'SELECT * FROM "{target_table}"', conn)
        
        # --- Step 3: 分发逻辑 ---
        if selected_exp == BUILTIN_TOOL_NAME:
            # A. 运行内置诊断
            run_diagnosis_tool(df)
        else:
            # B. 运行外部插件
            module_path = f"{EXP_DIR}.{selected_exp}"
            if module_path in sys.modules:
                module = importlib.reload(sys.modules[module_path])
            else:
                module = importlib.import_module(module_path)
            
            if hasattr(module, 'run'):
                st.divider()
                module.run(df, conn) 
            else:
                st.error(f"⚠️ 插件 `{selected_exp}` 缺少 `run(df, conn)` 入口函数。")
            
    except Exception as e:
        st.error(f"💥 运行出错: {e}")
    finally:
        conn.close()