# ==========================================
# 🟢 绝对第一顺位：打通项目底层路径 (必须放在最前面！)
# ==========================================
import sys
from pathlib import Path
import time
import warnings
warnings.filterwarnings('ignore', category=UserWarning, message='.*SQLAlchemy.*')
# 获取当前 app.py 的父目录(streamlit_lab) 的父目录(ERP_V2_PRO)
ROOT_DIR = Path(__file__).resolve().parent.parent
# 强制把根目录插队到 Python 搜索列表的第 0 号位置！
sys.path.insert(0, str(ROOT_DIR))

# ==========================================
# 🟢 第二顺位：导入第三方标准库
# ==========================================
import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 🟢 第三顺位：导入我们自己的 backend
# ==========================================
from backend import database as db
from backend.database import schema
from backend.config import config_manager as cfg
import sidebar_manager
import debug_kit

st.set_page_config(page_title="建筑专项管理系统", page_icon="🏗️", layout="wide")
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = '管理员(单机试用)'
# 1. 侧边栏
sidebar_manager.render_sidebar()
# ==========================================
# 🟢 核心数据统计 (V2.0 元数据驱动版)
# ==========================================
@st.cache_resource
def init_system_database():
    """🟢 增加 5 秒缓冲，确保数据库服务已就绪"""
    print("⏳ 等待数据库容器响应...")
    time.sleep(5)  # 给予数据库充足的冷启动时间
    schema.sync_database_schema()
    print("✅ 数据库底座初始化完毕！")

# 立即调用！(由于有 cache_resource 保护，它在服务器运行期间只会执行这一次)
init_system_database()
@st.cache_data(ttl=60) 
def load_global_stats():
    """
    [V2.0 升级] 不再扫描物理表名，而是根据 app_config.json 中的模型定义进行汇总。
    这样能确保公式计算（如回款率、欠款金额）在统计前被自动补齐。
    """
    # 1. 拿到所有业务模型的名字 (如 'project', 'enterprise')
    # 这里的 cfg.load_data_rules() 确保拿到的是最新配置
    config = cfg.load_data_rules()
    model_names = config.get("models", {}).keys()
    
    total_projects = 0
    total_contract = 0.0
    total_collection = 0.0
    recent_updates = []

    for m_name in model_names:
        # 🟢 核心替换：调用 V2.0 终极查询引擎
        # 它会自动执行 core_logic 里的公式，补齐‘回款率’、‘欠款’等动态字段
        df = db.fetch_dynamic_records(model_name=m_name)
        
        if not df.empty:
            total_projects += len(df)
            
            # 2. 物理列与公式列的兼容累加
            # 在 V2.0 中，contract_amount 和 total_collection 可能是物理列，也可能是公式列
            if 'contract_amount' in df.columns:
                total_contract += pd.to_numeric(df['contract_amount'], errors='coerce').fillna(0).sum()
            if 'total_collection' in df.columns:
                total_collection += pd.to_numeric(df['total_collection'], errors='coerce').fillna(0).sum()
            
            # 3. 收集最近更新 (V2.0 适配：使用 updated_at 系统列)
            if 'updated_at' in df.columns:
                df['updated_at'] = pd.to_datetime(df['updated_at'], errors='coerce')
                # 标记模型名称，方便用户识别数据来源
                df['model_label'] = m_name 
                # 截取需要的列（注意：project_name 是 project 模型特有的，其他模型可能叫别的，这里做个兜底）
                name_col = 'project_name' if 'project_name' in df.columns else df.columns[1] 
                manager_col = 'manager' if 'manager' in df.columns else 'extra_props'
                
                # 提取最近 5 条
                top5 = df.nlargest(5, 'updated_at')[[name_col, manager_col, 'updated_at', 'model_label']]
                # 统一重命名方便合并展示
                top5.columns = ['display_name', 'operator', 'update_time', 'source_model']
                recent_updates.append(top5)

    # 合并全局最近更新
    if recent_updates:
        df_recent = pd.concat(recent_updates).nlargest(5, 'update_time')
    else:
        df_recent = pd.DataFrame()

    return total_projects, total_contract, total_collection, df_recent

@st.cache_data(ttl=60)
def load_upcoming_receivables():
    """获取 30 天内及已逾期的待收款计划"""
    # 1. 获取主合同和收款计划表
    conn = db.get_connection()
    try:
        df_plans = pd.read_sql_query("SELECT * FROM biz_payment_plans WHERE deleted_at IS NULL", conn)
    except Exception as e:
        print(f"首页预警读取失败: {e}")
        df_plans = pd.DataFrame()
    finally:
        conn.close()
    df_contracts = db.fetch_dynamic_records(model_name="main_contract")
    
    if df_plans.empty:
        return 0.0, pd.DataFrame()
        
    # 2. 数据类型清洗
    df_plans['planned_date'] = pd.to_datetime(df_plans['planned_date'], errors='coerce')
    df_plans['planned_amount'] = pd.to_numeric(df_plans['planned_amount'], errors='coerce').fillna(0)
    # 兼容公式计算出的剩余未收，如果没有则默认等于计划金额
    if 'remaining_uncollected' in df_plans.columns:
        df_plans['remaining_uncollected'] = pd.to_numeric(df_plans['remaining_uncollected'], errors='coerce').fillna(0)
    else:
        df_plans['remaining_uncollected'] = df_plans['planned_amount']

    # 3. 核心业务过滤：剩余未收 > 0 且 日期 <= 今天 + 30天
    target_date = pd.Timestamp.today().normalize() + pd.Timedelta(days=30)
    
    # 过滤出需要催款的记录
    urgent_plans = df_plans[
        (df_plans['remaining_uncollected'] > 0) & 
        (df_plans['planned_date'] <= target_date)
    ].copy()
    
    if urgent_plans.empty:
        return 0.0, pd.DataFrame()
        
    # 4. 算出总共需要收多少钱
    total_urgent_amount = urgent_plans['remaining_uncollected'].sum()
    
    # 5. 关联主合同拿到项目名称
    if not df_contracts.empty and 'biz_code' in df_contracts.columns:
        urgent_plans = urgent_plans.merge(
            df_contracts[['biz_code', 'project_name']], 
            left_on='main_contract_code', 
            right_on='biz_code', 
            how='left'
        )
    else:
        urgent_plans['project_name'] = urgent_plans['main_contract_code']
        
    # 6. 计算状态标签（逾期 / 30天内）
    today = pd.Timestamp.today().normalize()
    urgent_plans['status_label'] = urgent_plans['planned_date'].apply(
        lambda x: "🚨 已逾期" if x < today else "⏳ 即将到期"
    )
    
    # 按日期排序，逾期的、马上到期的排在最前面
    urgent_plans = urgent_plans.sort_values(by='planned_date', ascending=True)
    
    return total_urgent_amount, urgent_plans


# 3. 页面渲染
st.title(f"👋 欢迎使用建筑专项项目管理系统")
st.caption(f"今天是 {datetime.now().strftime('%Y年%m月%d日')} | 系统状态: 🟢 正常运行")

# 加载数据
with st.spinner("正在汇总全库数据..."):
    t_proj, t_cont, t_coll, df_recent = load_global_stats()

# --- A. 核心指标卡 (KPI Cards) ---
st.divider()
k1, k2, k3, k4 = st.columns(4)

# 计算存量 (总额 - 已收)
stock_amount = t_cont - t_coll

with k1:
    st.metric("🏗️ 在库项目总数", f"{t_proj} 个", delta="全库统计")

with k2:
    # 🟢 修改点：这里改成了“存量合同额”
    st.metric(
        "💰 存量合同额 (未收)", 
        f"¥ {stock_amount/10000:,.1f} 万", 
        delta="核心关注指标",
        help="计算公式：累计合同总额 - 累计已收款"
    )

with k3:
    # 回款率计算
    rate = (t_coll / t_cont * 100) if t_cont > 0 else 0
    st.metric("💸 累计实收回款", f"¥ {t_coll/10000:,.1f} 万", delta=f"回款率 {rate:.1f}%")

with k4:
    # 🟢 修改点：原本的待收金额移到了K2，这里改为显示“历史总合同额”作为背景参考
    st.metric(
        "📜 历史累计签约", 
        f"¥ {t_cont/10000:,.1f} 万", 
        delta_color="off",
        help="所有项目的合同额总和 (含已完工)"
    )

# --- B. 快捷入口 & 最近动态 ---
st.divider()
c_main, c_side = st.columns([2, 1])

# 加载预警数据
total_urgent, df_urgent = load_upcoming_receivables()

with c_main:
    st.subheader("🚨 近期收款预警 (30天内及逾期)")
    
    # 增加一个醒目的汇总横幅
    if total_urgent > 0:
        st.error(f"**资金预警：** 近期共有 **¥ {total_urgent / 10000:,.1f} 万** 应收账款需要催办！")
        
        # 挑选要展示的列，优化表头体验
        display_df = df_urgent[['project_name', 'milestone_name', 'planned_date', 'remaining_uncollected', 'status_label']]
        
        st.dataframe(
            display_df,
            column_config={
                "project_name": st.column_config.TextColumn("归属项目", width="medium"),
                "milestone_name": "款项节点",
                "planned_date": st.column_config.DateColumn("预计收款日", format="YYYY-MM-DD"),
                "remaining_uncollected": st.column_config.NumberColumn("待收金额(元)", format="¥ %.2f"),
                "status_label": "紧急状态"
            },
            width="stretch",
            hide_index=True
        )
    else:
        st.success("🎉 太棒了！30 天内没有积压或即将到期的应收账款。")

with c_side:
    st.subheader("🚀 快速开始")
    with st.container(border=True):
        st.write("常用功能直达：")
        if st.button("📂 进入项目看板", width="stretch"):
            st.switch_page("pages/01_📂_项目看板.py")
        if st.button("🛠️ 新增/维护项目", width="stretch"):
            st.switch_page("pages/02_🛠️_主合同管理.py")
        if st.button("📊 查看财务报表", width="stretch"):
            st.switch_page("pages/04_📊_数据分析.py")

debug_kit.execute_debug_logic()