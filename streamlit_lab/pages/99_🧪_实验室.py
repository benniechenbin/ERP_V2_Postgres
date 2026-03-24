import sys
from pathlib import Path
import os
import streamlit as st
import importlib.util  # 🟢 引入动态加载专用库
import pandas as pd

# ==========================================
# 1. 📂 绝对路径定位 (确保在任何环境下都能找到文件夹)
# ==========================================
CURRENT_DIR = Path(__file__).resolve().parent
HOST_DIR = CURRENT_DIR.parent
EXP_DIR_PATH = HOST_DIR / "experiments"
ROOT_DIR = HOST_DIR.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend import database as db
import debug_kit

# ==========================================
# 2. 页面配置与门禁
# ==========================================
st.set_page_config(page_title="功能实验室", layout="wide", page_icon="🧪")

# 检查开发者模式
if not debug_kit.is_debug_mode():
    st.warning("🚫 此区域仅限开发者访问。请开启侧边栏 '开发者模式'。")
    st.stop()

st.title("🧪 功能孵化实验室 (Plugin Sandbox)")
st.caption("Project Reborn 底层沙盒：外部实验脚本的即插即用加载器。")

# ==========================================
# 3. 🔍 扫描实验卡带 (严格执行 'ex' 开头规则)
# ==========================================
if not EXP_DIR_PATH.exists():
    EXP_DIR_PATH.mkdir(parents=True, exist_ok=True)

# 扫描文件夹下的所有 .py 文件
external_files = []
try:
    
    external_files = [
        f[:-3] for f in os.listdir(EXP_DIR_PATH) 
        if f.startswith("ex") and f.endswith(".py") and f != "__init__.py"
    ]
    external_files.sort()
except Exception as e:
    st.error(f"扫描插件目录失败: {e}")

# 🟢 构建选项列表 (内置主页 + 外部卡带)
BUILTIN_TOOL_NAME = "🏠 实验室主控制台 (总览)"
menu_options = [BUILTIN_TOOL_NAME] + external_files

# ==========================================
# 4. 侧边栏控制台 (Console)
# ==========================================
with st.sidebar:
    st.header("🎛️ 实验室控制台")
    selected_exp = st.radio("选择挂载的模块", options=menu_options)
    st.divider()
    
    # [B] 选择数据源 (宿主负责，供给外部脚本使用)
    all_tables = db.get_all_data_tables()
    target_table = st.selectbox("🧪 挂载实验数据表", all_tables) if all_tables else None

# ==========================================
# 🟢 内置功能：实验室主页 (仪表盘)
# ==========================================
def run_lab_dashboard(conn, all_tables_list, plugins):
    st.subheader("🗄️ 数据库实体快照")
    st.markdown("欢迎进入底层控制台。这里是新功能、算法逻辑（如 RAG 向量检索测试）和数据清洗脚本的试验田。")

    # 顶栏指标
    col1, col2, col3 = st.columns(3)
    col1.metric("数据库连接 (Postgres)", "🟢 稳定")
    col2.metric("可用实验卡带 (Plugins)", f"{len(plugins)} 个")
    col3.metric("已挂载数据表", f"{len(all_tables_list)} 张")

    st.divider()

    # 数据库实时快照
    st.subheader("🗄️ 数据库实体快照")
    if all_tables_list:
        table_stats = []
        for tbl in all_tables_list:
            try:
                # 快速统计表行数
                count = pd.read_sql(f'SELECT COUNT(*) FROM "{tbl}"', conn).iloc[0, 0]
                table_stats.append({"数据表名称": tbl, "记录行数": count, "状态": "✅ 正常"})
            except Exception as e:
                table_stats.append({"数据表名称": tbl, "记录行数": "-", "状态": f"❌ 读取失败"})
                
        st.dataframe(pd.DataFrame(table_stats), width="stretch", hide_index=True)
    else:
        st.info("当前架构下暂无业务数据表。")

    # 开发者备忘录
    with st.expander("🛠️ 架构师备忘录：如何编写一个新的实验卡带？", expanded=True):
        st.markdown("""
        1. 在项目根目录的 `experiments/` 文件夹下新建一个 Python 文件，例如 `test_api.py`。
        2. 在文件中必须定义一个 `run(df, conn)` 函数作为入口。
        3. 刷新本页面，左侧边栏就会自动识别到该卡带。
        
        **代码模板：**
        ```python
        import streamlit as st

        def run(df, conn):
            st.subheader("我的第一个测试插件")
            st.write("传入的数据表预览：")
            st.dataframe(df.head())
            # 在这里尽情测试破坏性逻辑，不会影响主干代码！
        ```
        """)

# ==========================================
# 5. 宿主加载器 (Host Loader)
# ==========================================
conn = db.get_readonly_connection()
if not conn: st.stop()

try:
    if selected_exp == BUILTIN_TOOL_NAME:
        run_lab_dashboard(conn, all_tables, external_files)
    else:
        if target_table:
            # 1. 预加载数据
            df = pd.read_sql(f'SELECT * FROM "{target_table}"', conn)
            
            # 2. 🟢 核心修复：使用物理路径加载插件，不再使用 importlib.import_module
            file_path = EXP_DIR_PATH / f"{selected_exp}.py"
            
            # 创建加载规范 (Spec)
            spec = importlib.util.spec_from_file_location(selected_exp, str(file_path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # 将模块注入系统缓存，以便支持热更新
                sys.modules[selected_exp] = module
                spec.loader.exec_module(module)
                
                if hasattr(module, 'run'):
                    st.divider()
                    st.caption(f"🚀 正在运行卡带: `{selected_exp}.py` (只读模式)")
                    module.run(df, conn)
                else:
                    st.error(f"⚠️ 插件 `{selected_exp}` 缺少标准的 `run(df, conn)` 函数。")
            else:
                st.error(f"❌ 无法解析插件文件: {file_path}")
        else:
            st.warning("请在左侧选择一个挂载的数据表。")
finally:
    conn.close()