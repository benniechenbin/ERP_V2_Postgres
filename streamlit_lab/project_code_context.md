# 项目: streamlit_lab

## 🗂️ 项目目录树

```text
streamlit_lab/
├── .streamlit
├── experiments
│   ├── __init__.py
│   ├── ex01_risk_engine.py
│   └── ex02_biz_analysis.py
├── pages
│   ├── 01_📂_项目看板.py
│   ├── 02_🛠️_主合同管理.py
│   ├── 03_🛠️_分包合同管理.py
│   ├── 04_📊_数据分析.py
│   ├── 05_🏢_往来单位.py
│   ├── 06_📥_导入Excel.py
│   ├── 07_⚙️_系统管理.py
│   ├── 99_🧪_实验室.py
│   └── export_to_md.py
├── app.py
├── components.py
├── debug_kit.py
├── sidebar_manager.py
└── 🏠_Dashboard.py
```

---

## 💻 代码详情

### 📄 app.py

```python
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
```

### 📄 components.py

```python
# ==========================================
# 🎨 Streamlit UI 小组件 (偷懒神器) V3
# ==========================================
import streamlit as st
import pandas as pd
from datetime import datetime
import json
from backend.database.db_engine import get_connection
from backend.config import config_manager as cfg
from backend.database.crud import fetch_dynamic_records

def render_smart_widget(col_name, label, val, col_type, config_type, is_disabled, field_meta, override_options=None, override_format_func=None):
    """
    [智能 UI 组件渲染工厂] 根据字段类型，自动生成对应的 Streamlit 输入框。
    """
    # 🟢 魔法注入：如果外部传了选项，强行霸占 options，并把组件类型变异为 select！
    options = override_options if override_options is not None else field_meta.get("options", [])
    if override_options is not None:
        config_type = "select"

    default_val = field_meta.get("default", None)
    step_val = field_meta.get("step", 1000.0)
    min_val = field_meta.get("min_value", None)
    max_val = field_meta.get("max_value", None)

    if val is None and default_val is not None:
        val = default_val

    # ================= 渲染核心逻辑 =================
    
    if config_type == "select" and options:
        try:
            idx = options.index(val) if val in options else 0
        except ValueError:
            idx = 0
            
        # 🟢 魔法注入：如果外部传了 format_func，优先使用！
        if override_format_func:
            return st.selectbox(label, options=options, index=idx, disabled=is_disabled, format_func=override_format_func, key=f"input_{col_name}")
        else:
            return st.selectbox(label, options=options, index=idx, disabled=is_disabled, key=f"input_{col_name}")
    elif col_name == 'is_active':
        return st.toggle(label, value=bool(val) if val is not None else True, key=f"input_{col_name}")

    elif config_type == "date":
        if pd.isna(val) or val is None or str(val).strip() == "":
            default_date = datetime.today().date()
        else:
            try:
                default_date = pd.to_datetime(val).date()
            except:
                default_date = datetime.today().date()
                
        selected_date = st.date_input(label, value=default_date, disabled=is_disabled, key=f"input_{col_name}")
        return str(selected_date) 
      
    elif "DECIMAL" in col_type or "REAL" in col_type or "INT" in col_type:
        try:
            default_num = float(val)
        except (ValueError, TypeError):
            default_num = 0.0
        display_format = "%.2f"
        
        if config_type == "percent":
            label = f"{label} (%)"
            default_num = default_num * 100 
            if min_val is not None: min_val = float(min_val) * 100
            if max_val is not None: max_val = float(max_val) * 100
            if min_val is None: min_val = 0.0
            if max_val is None: max_val = 100.0
            step_val = 5
        
        if min_val is not None:
            default_num = max(default_num, float(min_val))
        if max_val is not None:
            default_num = min(default_num, float(max_val))
            
        raw_input = st.number_input(
            label, 
            value=default_num, 
            min_value=float(min_val) if min_val is not None else None,
            max_value=float(max_val) if max_val is not None else None,
            disabled=is_disabled,
            step=float(step_val),
            format=display_format,
            key=f"input_{col_name}"
        )
        
        return raw_input / 100.0 if config_type == "percent" else raw_input
            
    else:
        default_str = str(val) if val is not None else ""
        widget_key = f"input_{col_name}"
    
    # 🟢 增加智能判断：如果 session state 里已经有这个 key，就不传 value 参数
        if widget_key in st.session_state:
            return st.text_input(label, disabled=is_disabled, key=widget_key)
        else:
            return st.text_input(label, value=default_str, disabled=is_disabled, key=widget_key)

def show_toast_success(msg):
    st.toast(f"✅ {msg}", icon="🎉")

def show_toast_error(msg):
    st.toast(f"❌ {msg}", icon="😱")

def style_metric_card():
    st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #f9f9f9;
        border: 1px solid #e6e6e6;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

def remove_prefix_formatter(prefix: str):
    def formatter(item):
        if isinstance(item, str) and item.startswith(prefix):
            return item[len(prefix):]
        return item
    return formatter

def dict_mapping_formatter(mapping_dict: dict):
    def formatter(item):
        return mapping_dict.get(item, item)
    return formatter

# ==========================================
# 🚀 V3.0 宏观 UI 渲染引擎 (支持动态注入)
# ==========================================
def render_dynamic_form(model_name: str, form_title: str, existing_data: dict = None, hidden_fields: list = None, readonly_fields: list = None, dynamic_options: dict = None, format_funcs: dict = None):
    """
    [宏观组件 2：动态输入表单 - V3 终极版]
    极其强悍的表单生成器！自动根据 JSON 生成输入框，并支持在页面端注入动态下拉选项和格式化魔法！
    """
    field_meta = cfg.get_field_meta(model_name)
    if not field_meta:
        st.error(f"❌ 找不到模型 {model_name} 的配置")
        return None
        
    st.subheader(form_title)
    form_data = {}
    existing_data = existing_data or {}
    
    hidden_fields = hidden_fields or []
    readonly_fields = readonly_fields or []
    
    # 🟢 接收并初始化动态参数
    dynamic_options = dynamic_options or {}
    format_funcs = format_funcs or {}
    
    editable_fields = {
        k: v for k, v in field_meta.items() 
        if not v.get("is_virtual", False) and k not in hidden_fields
    }
    
    with st.form(key=f"form_{model_name}"):
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        
        for idx, (field_key, meta) in enumerate(editable_fields.items()):
            label = meta.get("label", field_key)
            col_type = meta.get("type", "text")
            val = existing_data.get(field_key, None)
            
            is_readonly = meta.get("readonly", False) or (field_key in readonly_fields)
            
            config_type = meta.get("type", "text")
            pseudo_col_type = "DECIMAL" if config_type in ["money", "percent", "number"] else "VARCHAR"
            
            with cols[idx % 3]:
                user_input = render_smart_widget(
                    col_name=field_key,
                    label=label,
                    val=val,
                    col_type=pseudo_col_type,
                    config_type=config_type,
                    is_disabled=is_readonly,
                    field_meta=meta,
                    override_options=dynamic_options.get(field_key),   # 🟢 动态选项注入
                    override_format_func=format_funcs.get(field_key)   # 🟢 格式化魔法注入
                )
                form_data[field_key] = user_input
                
        submit_btn = st.form_submit_button("💾 保存提交", use_container_width=True)
        
        if submit_btn:
            return form_data
    return None


def render_audit_timeline(biz_code: str, model_name: str = None):
    """
    [通用审计组件：时光机]
    传入 biz_code，自动展示该对象的完整生命周期。
    """   
    st.subheader(f"🕰️ 操作审计日志: {biz_code}")
    
    conn = None
    try:
        conn = get_connection()
        # 按时间倒序查询该编号的所有日志
        sql = "SELECT operator_name, action, diff_data, created_at FROM sys_audit_logs WHERE biz_code = %s ORDER BY created_at DESC"
        df_logs = pd.read_sql_query(sql, conn, params=(biz_code,))
        
        if df_logs.empty:
            st.info("🌱 当前暂无变更记录。")
            return

        # 尝试获取该模型的字段中文翻译字典
        field_meta = {}
        if model_name:
            field_meta = cfg.get_model_config(model_name).get("field_meta", {})

        # 绘制时光机时间轴
        for _, row in df_logs.iterrows():
            action_time = row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            action = row['action']
            operator = row['operator_name']
            
            # 解析差异 JSON
            diff_data = row['diff_data']
            if isinstance(diff_data, str):
                try: diff_data = json.loads(diff_data)
                except: diff_data = {}
            
            # 使用 Streamlit 的容器进行样式隔离
            with st.container(border=True):
                # 表头：时间和动作
                action_icon = "🆕" if action == "INSERT" else "✏️" if action == "UPDATE" else "🗑️"
                st.markdown(f"**{action_icon} {action_time}** | 操作人: `{operator}`")
                
                # 遍历差异并显示
                for col_key, changes in diff_data.items():
                    if len(changes) == 2:
                        old_val, new_val = changes
                        # 翻译列名为中文（如果有配置的话）
                        col_label = field_meta.get(col_key, {}).get("label", col_key)
                        
                        st.markdown(
                            f"&nbsp;&nbsp;&nbsp;&nbsp;▪️ **{col_label}**: "
                            f"<span style='color:gray; text-decoration:line-through;'>{old_val}</span> ➡️ "
                            f"<span style='color:green; font-weight:bold;'>{new_val}</span>", 
                            unsafe_allow_html=True
                        )
    except Exception as e:
        st.error(f"读取日志失败: {e}")
    finally:
        if conn: conn.close()
```

### 📄 debug_kit.py

```python
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import os
import json
from backend import database as db
from backend.config import config_manager

def is_debug_mode():
    return st.session_state.get('debug_mode', False)

def render_debug_sidebar():
    st.sidebar.markdown("---")
    if 'debug_mode' not in st.session_state:
        st.session_state['debug_mode'] = False
    
    mode = st.sidebar.toggle("🐞 开发者模式 (Debug)", value=st.session_state['debug_mode'])
    st.session_state['debug_mode'] = mode
    if mode:
        if st.sidebar.button("🚀 进入实验室 (Sandbox)", width="stretch"):
            st.switch_page("pages/99_🧪_实验室.py")

def execute_debug_logic(current_db_path=None):
    if not is_debug_mode(): return

    actual_db_path = current_db_path
    if actual_db_path is None:
        actual_db_path = db.get_connection()
    
    st.markdown("---")
    st.markdown("### 🐞 开发者控制台 (Pro)")
    
    tabs = st.tabs(["⚙️ 系统全量配置","💾 SQL终端", "🧠 内存/Session","🔥 危险区"])
    # =========================================================
    # Tab 1: 核心模型配置 (应急修改区)
    # =========================================================
    with tabs[0]:
        st.subheader("🛠️ 系统全量配置 (App Config JSON)")
        st.caption("⚠️ 警告：此区域用于紧急修改表结构与映射规则。修改后保存，系统底层的引擎会自动将 label 对齐到 column_mapping 中。")
        
        # 获取最新的配置数据
        current_config = config_manager.load_data_rules()
        # 我们只把 models 部分暴露出来（不包含公式等其他信息），防止用户改乱
        models_data = current_config.get("models", {})
        
        # 纯净的大文本框
        models_input = st.text_area(
            "Models JSON (包含各表的 field_meta 与 column_mapping)",
            value=json.dumps(models_data, indent=4, ensure_ascii=False),
            height=600,
            key="json_models_emergency"
        )
        
        if st.button("💾 强制覆写模型配置", type="primary", width="stretch"):
            try:
                # 解析输入的纯文本 JSON
                new_models = json.loads(models_input)
                
                # 将改动合并回原配置 (保留公式等其他节点不被破坏)
                current_config["models"] = new_models
                
                # 🟢 调用 config_manager 的保存方法，它会在内部自动触发 _auto_sync_labels
                if config_manager.save_data_rules(current_config):
                    st.success("🎉 模型配置覆写成功！")
                    
                    # --- 🟢 新增逻辑：强制触发数据库底座的“热更新” ---
                    try:
                        from backend.database import schema
                        schema.sync_database_schema() # 立即对比并增加缺少的列
                        st.cache_resource.clear()     # 清理 app.py 的启动缓存，防止状态不一致
                        st.success("✅ 数据库底层物理表已同步扩容！")
                    except Exception as e:
                        st.error(f"⚠️ 数据库同步失败，请检查终端日志: {e}")
                    # ------------------------------------------------
                    
                    st.rerun() # 刷新页面重新加载内存
                else:
                    st.error("❌ 文件写入失败。")
            except json.JSONDecodeError as je:
                st.error(f"❌ JSON 格式严重错误，请检查标点符号或括号匹配：{je}")

    # =========================================================
    # Tab 2: SQL 终端 (修复版)
    # =========================================================
    with tabs[1]:
        st.write(f"连接库：`{current_db_path}`")
        st.subheader("💻 SQL 执行终端")
        
        # 1. 获取当前所有表名
        all_tables = db.get_all_data_tables()
        default_table = all_tables[0] if all_tables else "data_Project2026"

        # 2. 定义常用 SQL 模板
        SQL_TEMPLATES = {
            "--- 请选择预设模板 (可选) ---": "",
            "🔍 查看所有数据表名": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';",
            "👀 查看前 10 条数据": f'SELECT * FROM "{default_table}" LIMIT 10;',
            "📑 查看表结构 (列定义)": f"SELECT column_name, data_type, character_maximum_length, column_default FROM information_schema.columns WHERE table_name = '{default_table}';",
            "➕ [热修] 增加一个小数列 (用于金额/系数)": f'ALTER TABLE "{default_table}" ADD COLUMN new_column_name NUMERIC(15,2) DEFAULT 0.00;',
            "➕ [热修] 增加一个文本列 (用于备注)": f'ALTER TABLE "{default_table}" ADD COLUMN new_text_col VARCHAR(255);',
            "➕ [热修] 增加一个整数列 (用于状态标记)": f'ALTER TABLE "{default_table}" ADD COLUMN is_flag INTEGER DEFAULT 0;',
            "🧹 [清理] 删除业务编号为空的行": f'DELETE FROM "{default_table}" WHERE biz_code IS NULL OR biz_code = \'\';',
            "🔥 [危险] 删除整个表": f'DROP TABLE "{default_table}";'
        }

        # --- 🟢 核心修复：定义回调函数 ---
        def on_template_change():
            # 获取下拉框当前选中的 key
            selected_key = st.session_state['sql_template_selector']
            # 强制更新输入框的 Session State
            st.session_state['sql_input_area'] = SQL_TEMPLATES.get(selected_key, "")

        # 3. 模板选择器 (添加 on_change)
        c_temp, c_tip = st.columns([3, 1])
        with c_temp:
            st.selectbox(
                "⚡ 快速填充 SQL 模板", 
                options=list(SQL_TEMPLATES.keys()),
                index=0,
                key="sql_template_selector",
                on_change=on_template_change
            )
        with c_tip:
            st.info(f"当前默认表: `{default_table}`")

        # 4. SQL 编辑区
        if "sql_input_area" not in st.session_state:
             st.session_state["sql_input_area"] = ""

        sql_input = st.text_area(
            "SQL 语句 (支持多行)", 
            height=150,
            help="输入标准 PostgreSQL 语法。如需操作特定表，请确保表名加双引号。", # 🟢 修改了这里的提示文字
            key="sql_input_area" 
        )
        
        # 5. 执行按钮
        col_run, col_helper = st.columns([1, 4])
        with col_run:
            run_btn = st.button("🚀 执行 SQL", type="primary")
        
        if run_btn and sql_input.strip():
            # 🟢 拆弹 2：不再使用 sqlite3.connect，直接调用底层的 execute_raw_sql
            success, result = db.execute_raw_sql(sql_input)
            if success:
                if isinstance(result, pd.DataFrame):
                    st.success(f"✅ 查询成功，返回 {len(result)} 行")
                    st.dataframe(result, width="stretch")
                else:
                    st.success(f"✅ {result}")
            else:
                st.error(f"❌ 执行失败: {result}")
    with tabs[2]:
        st.write("当前 Session State 所有变量：")
        st.json(dict(st.session_state))
       
    with tabs[3]:
        if st.button("🔥 重置所有配置为默认值"):
            if os.path.exists(config_manager.CONFIG_FILE):
                os.remove(config_manager.CONFIG_FILE)
            st.success("已重置，请刷新页面。")
            st.rerun()
```

### 📄 sidebar_manager.py

```python
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


```

### 📄 🏠_Dashboard.py

```python
import streamlit as st
st.title('ERP V2 实验室大屏')
```

### 📁 .streamlit

### 📁 experiments

#### 📄 __init__.py

```python

```

#### 📄 ex01_risk_engine.py

```python
import streamlit as st
import pandas as pd
import config_manager as cfg

# ==============================================================================
# 🟢 区域一：待迁移的核心逻辑 (Future Core Logic)
# ------------------------------------------------------------------------------
# 💡 说明：
# 这部分代码目前暂居此处方便调试。
# 测试通过后，请将这部分函数原封不动地剪切到 `core_logic.py` 中。
# 它不包含任何 st.write 等 UI 代码，只接收 DataFrame 和 规则配置字典。
# ==============================================================================

def _parse_rule_to_query_string(rule_config: dict) -> str:
    """
    【内部工具】将规则字典翻译成 Pandas Query 字符串
    """
    gate = rule_config.get("gate", "AND")  # 逻辑门：AND 或 OR
    conditions = rule_config.get("conditions", [])
    
    if not conditions:
        return ""

    # 1. 确定连接符
    connector = " & " if gate == "AND" else " | "
    
    query_parts = []
    for cond in conditions:
        # 获取用户输入的三个部分
        left = str(cond.get("left", "")).strip()   # 左侧：公式或字段
        op = cond.get("op", "==")                  # 中间：运算符
        right = str(cond.get("right", "")).strip() # 右侧：阈值
        
        # 防御：如果左右有一边为空，跳过该条件
        if not left or not right:
            continue
            
        # 2. 组合单个条件 (加括号保证数学运算优先级)
        # 格式: ( contract_amount - cost > 1000 )
        query_parts.append(f"({left} {op} {right})")
        
    # 3. 拼接最终语句
    final_query = connector.join(query_parts)
    return final_query

def execute_risk_filter(df: pd.DataFrame, rule_config: dict) -> pd.DataFrame:
    """
    【核心接口】执行风险筛选
    
    :param df: 原始项目数据表
    :param rule_config: 前端生成的规则字典，格式如下：
           {
               "gate": "AND",
               "conditions": [
                   {"left": "amount", "op": ">", "right": "100"},
                   {"left": "amount - cost", "op": "<", "right": "0"}
               ]
           }
    :return: 筛选后的 DataFrame
    """
    if df.empty:
        return pd.DataFrame()

    # 1. 解析规则
    query_str = _parse_rule_to_query_string(rule_config)
    
    # 如果解析出来是空的（比如用户没填任何条件），返回空还是全量？这里由你决定
    if not query_str:
        return df 

    try:
        # 2. 注入环境变量 (方便公式里使用 today 计算天数)
        # 这样用户可以在公式里写: (today - sign_date).dt.days > 90
        env = {"today": pd.Timestamp.now()}
        
        # 3. 执行 Pandas Query
        # local_dict=env 让 query 字符串能识别 'today' 变量
        filtered_df = df.query(query_str, local_dict=env)
        
        return filtered_df
        
    except Exception as e:
        # 捕获逻辑错误（比如字段名写错、除以零），抛出更友好的异常
        # 实际迁移时，这里可以记录日志
        raise ValueError(f"规则执行失败: {str(e)}")


# ==============================================================================
# 🟡 区域二：实验室 UI 交互层 (Experiment UI)
# ------------------------------------------------------------------------------
# 💡 说明：
# 这部分代码负责“模仿 Apple Music 智能列表”的交互。
# 它负责收集用户输入，组装成 rule_config 字典，然后调用上面的函数。
# ==============================================================================

def run(df, conn):
    # 🟢 接收宿主注入的 df 和 conn
    st.header("🛡️ 智能风控引擎 (Smart Risk Engine)")
    
    if df.empty:
        st.warning("⚠️ 所选表无数据，无法进行测试。")
        return
    for col in df.columns:
        # 1. 自动识别可能的金额列
        if any(key in col for key in ["amount", "fee", "total", "collection", "cost"]):
            # 先把千分位逗号和货币符号去掉 (针对字符串类型)
            if df[col].dtype == 'object':
                 df[col] = df[col].astype(str).str.replace('¥', '').str.replace(',', '').str.replace(' ', '')
            
            # 强制转数字
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) # 转换失败填0
    st.success(f"✅ 数据注入成功 | 样本量: {len(df)} 条 | 来源: 宿主程序预加载")

    for col in df.columns:
        if "date" in col or "time" in col:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # 在界面上展示一下可用字段，方便开发者复制
    with st.expander("📚 字段速查手册 (写公式用点这里)", expanded=False):
        st.info("💡 提示：左侧输入框支持数学运算。请复制【变量名】列的内容。")
        
        # 1. 自动生成对照表
        field_info = []
        
        # 这里的 cfg.STANDARD_FIELDS 是从 data_rules.json 动态加载的
        # 格式: {"contract_amount": "💰 当年合同额"}
        
        for col in df.columns:
            # 尝试获取中文名，如果字典里没有，就标为"扩展字段"
            chn_name = cfg.STANDARD_FIELDS.get(col, "自定义/扩展字段")
            dtype = str(df[col].dtype)
            
            # 给类型加个易读的标签
            if "float" in dtype or "int" in dtype:
                type_icon = "🔢 数字"
            elif "datetime" in dtype:
                type_icon = "📅 日期"
            else:
                type_icon = "🔤 文本"

            field_info.append({
                "变量名 (Copy me)": col,
                "中文含义": chn_name,
                "数据类型": type_icon
            })
        
        # 2. 展示表格
        info_df = pd.DataFrame(field_info)
        st.dataframe(
            info_df, 
            column_config={
                "变量名 (Copy me)": st.column_config.TextColumn(help="双击复制这个名字放入公式"),
            },
            width="stretch",
            hide_index=True
        )
        
        # 3. 快捷复制区 (针对常用计算字段)
        st.markdown("#### ⚡️ 常用计算字段 (点击复制)")
        cols = st.columns(4)
        # 挑出所有数字类型的列，方便直接复制
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        for i, col in enumerate(numeric_cols):
            with cols[i % 4]:
                st.code(col, language=None)


    st.divider()

    # --- 2. 规则构造器 (Rule Builder UI) ---
    st.subheader("🛠️ 规则定义")

    # [A] 顶层逻辑门 (Gate)
    c1, c2 = st.columns([1.5, 5])
    with c1:
        st.markdown("##### 筛选出满足以下")
    with c2:
        # 仿 Apple Music/iTunes 风格
        gate_select = st.selectbox(
            "逻辑", 
            ["所有 (ALL) 条件的项目", "任意 (ANY) 条件的项目"], 
            label_visibility="collapsed"
        )
        # 转换成数据模型需要的 "AND" / "OR"
        gate_val = "AND" if "所有" in gate_select else "OR"

    # [B] 动态条件行 (Dynamic Rows)
    # 初始化 Session State
    if "exp_risk_rules" not in st.session_state:
        st.session_state["exp_risk_rules"] = [
            {"left": "contract_amount", "op": ">", "right": "500"} # 默认给一行
        ]

    rows = st.session_state["exp_risk_rules"]

    # 增删行帮助函数
    def add_row():
        st.session_state["exp_risk_rules"].append({"left": "", "op": "==", "right": ""})
    def del_row(idx):
        st.session_state["exp_risk_rules"].pop(idx)

    # 渲染每一行
    for i, row in enumerate(rows):
        # 布局：[左侧公式] [运算符] [右侧阈值] [删除]
        c_left, c_op, c_right, c_btn = st.columns([3, 1, 2, 0.5])
        
        with c_left:
            # 这里的 left 既可以是单纯的字段名，也可以是公式
            # 比如: contract_amount - cost
            row["left"] = st.text_input(
                f"条件 {i+1} 左侧", 
                value=row["left"], 
                key=f"rule_l_{i}",
                placeholder="字段名 或 数学公式 (如 A - B)"
            )
        
        with c_op:
            # 丰富的运算符支持
            ops = [">", "<", "==", "!=", ">=", "<=", "in (包含)", "not in"]
            # 简单的回显逻辑
            current_op = row["op"]
            # 处理 UI 显示带中文的情况
            display_ops = ops 
            idx = 0
            for k, op_str in enumerate(ops):
                if op_str.startswith(current_op):
                    idx = k
                    break
            
            selected_op = st.selectbox("", ops, index=idx, key=f"rule_o_{i}", label_visibility="collapsed")
            # 存回去的时候只存 > < == 这种纯符号
            row["op"] = selected_op.split(" ")[0]

        with c_right:
            # 右侧值
            row["right"] = st.text_input(
                f"值", 
                value=row["right"], 
                key=f"rule_r_{i}",
                placeholder="数字 或 '文本'"
            )
            
        with c_btn:
            if st.button("🗑️", key=f"rule_d_{i}"):
                del_row(i)
                st.rerun()

    # 底部按钮栏
    if st.button("➕ 添加条件"):
        add_row()
        st.rerun()

    # --- 3. 验证与执行 (Verification) ---
    st.divider()
    
    # 组装 Model (完全解耦的数据结构)
    rule_config = {
        "gate": gate_val,
        "conditions": rows
    }

    # 开发者视图：看一眼生成的 JSON
    with st.expander("🔍 开发者数据视图 (即将存入 Config 的 JSON)"):
        st.json(rule_config)
        st.caption("👆 这就是解耦的关键：前端只负责生成这个 JSON，后端 Core Logic 只负责执行这个 JSON。")

    st.subheader("🎯 筛选结果预览")
    
    # 调用核心逻辑 (模拟未来的调用方式)
    try:
        # 🟢 关键：这里只调用函数，不再写任何逻辑代码！
        filtered_result = execute_risk_filter(df, rule_config)
        
        # 显示统计
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        col_stat1.metric("总项目数", len(df))
        col_stat2.metric("命中规则数", len(filtered_result))
        if len(df) > 0:
            rate = len(filtered_result) / len(df) * 100
            col_stat3.metric("风险占比", f"{rate:.1f}%")
        
        # 显示表格
        st.dataframe(filtered_result, width="stretch")
        
        # 显示最终生成的 SQL/Query (方便调试)
        if not filtered_result.empty or len(rows) > 0:
            query_debug = _parse_rule_to_query_string(rule_config)
            st.info(f"Generated Query: `{query_debug}`")

    except Exception as e:
        st.error("💥 规则运算出错")
        st.warning(f"错误详情: {e}")
        st.markdown("""
        **常见错误排查：**
        1. 文本值忘记加引号？例如状态应该是 `'停工'` 而不是 `停工`。
        2. 字段名拼写错误？请参考顶部的可用字段。
        3. 数学公式里用了非数字字段？
        """)

```

#### 📄 ex02_biz_analysis.py

```python
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
```

### 📁 pages

#### 📄 01_📂_项目看板.py

```python
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
```

#### 📄 02_🛠️_主合同管理.py

```python
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import warnings
from pathlib import Path

# 🟢 1. 环境与路径初始化
warnings.filterwarnings('ignore', category=UserWarning, message='.*SQLAlchemy.*')
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 🟢 2. 引入后端服务与组件
from backend.database import crud_base, crud
from backend.database.db_engine import execute_raw_sql
from backend.config import config_manager as cfg
import backend.database as db
from backend import services as svc
# 核心 AI 提取接口
from backend.services.ai_service import get_main_contract_elements 

import sidebar_manager
import debug_kit 
import components as ui

FORM_HIDDEN_FIELDS = [] 
FORM_READONLY_FIELDS = []

# ==========================================
# 0. 页面配置与初始化
# ==========================================
st.set_page_config(page_title="主合同管理", page_icon="🛠️", layout="wide")

if 'show_main_contract_dialog' not in st.session_state:
    st.session_state.show_main_contract_dialog = False
if 'current_edit_data' not in st.session_state:
    st.session_state.current_edit_data = None
    
if 'refresh_trigger' not in st.session_state:
    st.session_state.refresh_trigger = 0

def trigger_refresh():
    st.session_state.refresh_trigger += 1

# ==========================================
# 1. 核心数据获取
# ==========================================
@st.cache_data(ttl=5, show_spinner=False)
def load_main_contracts(trigger):
    return db.fetch_dynamic_records('main_contract')

# ==========================================
# 1.5 收款计划表 (子表) 读写引擎
# ==========================================
def load_payment_plans(main_contract_code):
    """从数据库加载指定主合同的收款计划 (彻底修复参数报错)"""
    sql = '''
        SELECT biz_code AS "计划编号", milestone_name AS "款项节点", 
               payment_ratio AS "比例(%%)", planned_amount AS "计划金额", 
               planned_date AS "预警日期", remarks AS "备注"
        FROM biz_payment_plans
        WHERE main_contract_code = %s AND deleted_at IS NULL
        ORDER BY planned_date ASC, id ASC
    '''
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            # 🟢 修正点：显式传递参数元组，原生执行
            cur.execute(sql, (str(main_contract_code),)) 
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=cols)
            
        if not df.empty:
            df['比例(%)'] = pd.to_numeric(df['比例(%)'], errors='coerce').fillna(0.0)
            df['计划金额'] = pd.to_numeric(df['计划金额'], errors='coerce').fillna(0.0)
            df['预警日期'] = pd.to_datetime(df['预警日期']).dt.date
        return df
    except Exception as e:
        st.error(f"⚠️ 读取收款计划失败: {e}")
        return pd.DataFrame(columns=["计划编号", "款项节点", "比例(%)", "计划金额", "预警日期", "备注"])
    finally:
        if conn: conn.close()

def load_financial_history(main_contract_code, table_type="collections"):
    """
    统一的历史记录拉取函数
    table_type: 'collections' (收款) 或 'invoices' (开票)
    """
    conn = db.get_connection()
    try:
        if table_type == "collections":
            sql = '''
                SELECT biz_code AS "流水号", collected_date AS "收款日期", 
                       collected_amount AS "金额(元)", update_project_stage AS "对应节点", 
                       operator AS "经办人", remarks AS "备注", created_at AS "录入时间"
                FROM biz_collections
                WHERE main_contract_code = %s AND deleted_at IS NULL
                ORDER BY collected_date DESC, created_at DESC
            '''
        else:
            sql = '''
                SELECT biz_code AS "发票号", invoice_date AS "开票日期", 
                       invoice_amount AS "金额(元)", target_plan_code AS "关联计划", 
                       operator AS "经办人", remarks AS "备注", created_at AS "录入时间"
                FROM biz_invoices
                WHERE main_contract_code = %s AND deleted_at IS NULL
                ORDER BY invoice_date DESC, created_at DESC
            '''
            
        with conn.cursor() as cur:
            cur.execute(sql, (str(main_contract_code),)) 
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=cols)
            
        if not df.empty:
            df['金额(元)'] = pd.to_numeric(df['金额(元)'], errors='coerce').fillna(0.0)
            if '录入时间' in df.columns:
                df['录入时间'] = pd.to_datetime(df['录入时间']).dt.strftime('%Y-%m-%d %H:%M')
        return df
    except Exception as e:
        st.error(f"⚠️ 读取{table_type}历史失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

def save_payment_plans(main_contract_code, df_plans, operator, total_contract_amount):
    """全量覆盖保存：先清空，后写入，确保数据唯一"""
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            # 🟢 1. 强力清场：必须先删除该合同下所有旧计划
            cursor.execute(
                "UPDATE biz_payment_plans SET deleted_at = CURRENT_TIMESTAMP WHERE main_contract_code = %s", 
                (str(main_contract_code),)
            )
            
            # 2. 循环插入新数据
            insert_sql = """
                INSERT INTO biz_payment_plans 
                (biz_code, main_contract_code, milestone_name, payment_ratio, planned_amount, planned_date, remarks, operator)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for idx, row in df_plans.iterrows():
                milestone_name = str(row.get("款项节点", "")).strip()
                if not milestone_name or milestone_name == 'nan': continue 
                
                # 比例与金额智能互算
                raw_ratio = float(row.get("比例(%)", 0.0)) if pd.notna(row.get("比例(%)")) else 0.0
                raw_amount = float(row.get("计划金额", 0.0)) if pd.notna(row.get("计划金额")) else 0.0
                
                final_ratio = raw_ratio
                final_amount = raw_amount
                if raw_amount > 0 and raw_ratio == 0 and total_contract_amount > 0:
                    final_ratio = round((raw_amount / total_contract_amount) * 100, 2)
                elif raw_ratio > 0 and raw_amount == 0:
                    final_amount = round(total_contract_amount * (raw_ratio / 100.0), 2)

                plan_code = f"PLAN-{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{idx}"
                planned_date = row.get("预警日期")
                if pd.isna(planned_date) or not planned_date: planned_date = None
                
                cursor.execute(insert_sql, (
                    plan_code, main_contract_code, milestone_name, 
                    final_ratio, final_amount, planned_date, row.get("备注", ""), operator
                ))
            
            conn.commit() # 🟢 统一提交事务
            return True, "计划已覆盖保存"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

df_main = load_main_contracts(st.session_state.refresh_trigger)
sidebar_manager.render_sidebar()

# ==========================================
# 2. 主合同表单弹窗
# ==========================================
@st.dialog("🏗️ 主合同信息登记", width="large")
def contract_form_dialog(existing_data=None):
    # 状态初始化：用于存放 AI 提取出的数据
    if "ai_extracted_buffer" not in st.session_state:
        st.session_state.ai_extracted_buffer = {}

    # 1. 🤖 AI 解析交互区
    st.subheader("🤖 AI 合同智能解析")
    uploaded_files = st.file_uploader("📂 请上传合同 PDF 或 Word 以供 AI 识别", accept_multiple_files=True)
    
    c_cat, c_btn = st.columns([3, 1])
    with c_cat:
        file_category = st.selectbox(
            "🗂️ 附件类别", 
            ["主合同文本 (需 AI 解析)", "补充协议/变更单 (需 AI 解析)", "工程图纸", "结算单", "其他附件"],
            label_visibility="collapsed" 
        )
    with c_btn:
        # 只有上传了文件，且类别属于“需 AI 解析”时，按钮才可用
        ai_ready = uploaded_files is not None and len(uploaded_files) > 0 and "(需 AI 解析)" in file_category
        
        if st.button("✨ 一键 AI 提取", type="primary", disabled=not ai_ready, use_container_width=True):
            with st.spinner("🧠 AI 正在极速阅读合同条款，请稍候..."):
                
                # 🟢 呼叫真实的后端 AI 接口
                # 🟢 呼叫真实的后端 AI 接口
                ai_results = get_main_contract_elements(uploaded_files[0])
                
                if ai_results:
                    # 拿到当前表单的字段配置，用来知道哪个框是什么类型
                    field_meta = cfg.get_field_meta("main_contract")
                    
                    for k, v in ai_results.items():
                        # 如果 AI 没提取到，或者是空值，就直接跳过
                        if v is None or str(v).strip().lower() in ["", "null", "none"]:
                            continue
                            
                        state_key = f"input_{k}"
                        # 获取这个字段在配置里的真实类型，默认是文本
                        f_type = field_meta.get(k, {}).get("type", "text")
                        
                        try:
                            # 🟢 终极填表魔法 3：精准类型转换！满足 Streamlit 组件的变态要求
                            if f_type == "date":
                                # 把 "2025-06-30" 这样的字符串，变成真正的 datetime.date 对象
                                parsed_date = datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
                                st.session_state[state_key] = parsed_date
                            elif f_type in ["money", "number", "percent"]:
                                # 数字类组件需要 float
                                st.session_state[state_key] = float(v)
                            else:
                                # 其他文本类组件需要 string
                                st.session_state[state_key] = str(v)
                        except Exception as e:
                            # 万一 AI 犯傻（比如把日期写成“年底”），转换失败就跳过这个字段，不引发崩溃
                            pass
                    
                    # 存入 buffer
                    st.session_state.ai_extracted_buffer = ai_results
                    st.success("🎉 提取完毕！下方表单已自动填充。")
                    
                    # 强制刷新
                    st.rerun() 
                else:
                    st.error("❌ 识别失败，未能提取出有效数据。")

    st.markdown("---") 

    # 🟢 2. 数据准备与合并
    is_edit = existing_data is not None
    form_title = "✏️ 修改主合同" if is_edit else "🆕 录入新主合同"
    
    # 建立一个干净的数据副本
    current_data = existing_data.copy() if existing_data else {}
    
    if not is_edit:
        target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
        current_data['biz_code'] = crud_base.generate_biz_code(target_table, prefix_char="MAIN")
        
    # 无论是新增还是修改，只要 AI 提取了，就把它融合进去
    if st.session_state.get("ai_extracted_buffer"):
        current_data.update(st.session_state.ai_extracted_buffer)
        
    # 3. 渲染出高级表单
    result = ui.render_dynamic_form(
        "main_contract", 
        form_title, 
        current_data, 
        hidden_fields=FORM_HIDDEN_FIELDS,
        readonly_fields=FORM_READONLY_FIELDS
    )
    
    # 4. 保存逻辑
    if result:
        final_biz_code = result.get('biz_code', current_data.get('biz_code'))
        target_id = int(existing_data['id']) if is_edit and 'id' in existing_data else None
        current_user = st.session_state.get('user_name', 'System')
        
        # 处理编号变更后的级联更新
        if is_edit and final_biz_code != existing_data.get('biz_code'):
            db.update_biz_code_cascade(existing_data.get('biz_code'), final_biz_code, "biz_main_contracts")
        
        success, msg = crud_base.upsert_dynamic_record("main_contract", result, record_id=target_id, operator_name=current_user)
        
        if success:
            # 1. 物理保存附件
            if uploaded_files:
                target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
                for uf in uploaded_files:
                    svc.save_attachment(final_biz_code, uf, target_table, file_category=file_category)
            
            # 2. 清理所有状态与缓存！(必须放在循环外面)
            st.session_state.ai_extracted_buffer = {}
            st.session_state.show_main_contract_dialog = False # 🟢 彻底关闭弹窗开关
            
            # 3. 提示并刷新页面
            ui.show_toast_success("主合同数据已成功落库！")
            trigger_refresh() 
            st.rerun()
        else:
            ui.show_toast_error(f"保存失败: {msg}")
# ==========================================
# 2. 📊 顶层：全局资金看板 
# ==========================================
@st.dialog("📦 执行年度财务结转", width="small")
def yearly_archive_dialog():
    st.warning("⚠️ 警告：此操作会将系统内所有【已计提】的合同和项目进行归档（软删除）。\n\n请务必确保本年度所有账务已核对完毕！")
    confirm = st.text_input("请输入 '确认结转' 以继续执行：")
    if st.button("🚨 确认执行结转", type="primary", disabled=(confirm != "确认结转"), use_container_width=True):
        
        # 🟢 1. 提取当前操作人
        current_user = st.session_state.get('user_name', 'System')
        
        # 🟢 2. 执行底层结转逻辑 (注意这里需要补上 db. 前缀，确保调用正确)
        success, msg = db.execute_yearly_accrual_archive()
        
        if success:
            # 🟢 3. 智能提取成功数量并写入 job_log
            import re
            # 假设后端的 msg 返回的是 "成功结转 15 份合同"
            nums = re.findall(r'\d+', msg)
            success_count = int(nums[0]) if nums else 0
            
            try:
                # 调用我们在 crud_sys 里写的适配器，记录宏观日志
                db.log_job_operation(
                    operator=current_user,
                    file_name="前端手动触发",         # 借用 file_name 字段存来源
                    import_type="main_contract",    # 借用 import_type 存目标模型
                    success_count=success_count
                )
            except Exception as e:
                print(f"写入结转日志失败: {e}")

            if ui and hasattr(ui, 'show_toast_success'): ui.show_toast_success(msg)
            trigger_refresh()
            st.rerun()
        else:
            st.error(msg)

if st.session_state.show_main_contract_dialog:
    contract_form_dialog(st.session_state.current_edit_data)

col_title, col_add_btn, col_archive_btn = st.columns([6, 2, 2])
with col_title:
    st.title("🛠️ 主合同资金管理台")
with col_add_btn:
    # 🟢 用 CSS 给出精确的下压边距，取代不稳定的 st.write("")
    st.markdown("<div style='margin-top: 22px;'></div>", unsafe_allow_html=True)
    if st.button("➕ 录入新主合同", type="primary", use_container_width=True):
        st.session_state.show_main_contract_dialog = True
        st.session_state.current_edit_data = None # 新增模式
        st.rerun()
        
with col_archive_btn:
    st.markdown("<div style='margin-top: 22px;'></div>", unsafe_allow_html=True)
    if st.button("📦 年度财务结转", use_container_width=True, help="将所有已计提的项目移入历史档案"):
        yearly_archive_dialog()

# 🟢 调用 components 里的卡片美化功能
if ui and hasattr(ui, 'style_metric_card'):
    ui.style_metric_card()

if not df_main.empty:
    # 算总账
    total_amount = df_main['contract_amount'].astype(float).sum()
    total_collected = df_main['total_collected'].astype(float).sum()
    total_uncollected = df_main['uncollected_contract_amount'].astype(float).sum()
    total_invoiced = df_main['total_invoiced'].astype(float).sum()
    contract_count = len(df_main)
    
    # 计算各项比率 (防止除以 0 报错)
    collection_rate = (total_collected / total_amount) * 100 if total_amount else 0.0
    uncollected_rate = (total_uncollected / total_amount) * 100 if total_amount else 0.0
    invoice_rate = (total_invoiced / total_amount) * 100 if total_amount else 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 总盘子 (合同总额)", f"¥ {total_amount:,.2f}", 
                  delta=f"包含 {contract_count} 份主合同", delta_color="off") # off 代表显示中性灰色
    with col2:
        st.metric("💰 钱袋子 (累计到账)", f"¥ {total_collected:,.2f}", 
                  delta=f"总回款率: {collection_rate:.1f}%") # 默认 normal 为绿色
    with col3:
        st.metric("📝 待收款 (剩余未到账)", f"¥ {total_uncollected:,.2f}", 
                  delta=f"资金缺口占比: {uncollected_rate:.1f}%", delta_color="inverse") # inverse 代表红色预警
    with col4:
        st.metric("📄 累计开票", f"¥ {total_invoiced:,.2f}", 
                  delta=f"开票覆盖率: {invoice_rate:.1f}%", delta_color="off")
    
st.markdown("---")

# ==========================================
# 3. 黄金分割布局：左表(行内编辑) + 右抽屉(多Tab)
# ==========================================
if df_main.empty:
    st.info("📭 当前系统暂无主合同数据，请先录入。")
else:
    # 调整比例，给右侧的 Tab 多留一点空间 (2.5 : 1.5)
    col_table, col_form = st.columns([2.5, 1.5])

    # ------------------------------------------
    # 🗂️ 左侧区域：带行内编辑的数据网格
    # ------------------------------------------
    with col_table:
        st.subheader("📑 合同台账明细")
        
        if 'project_stage' not in df_main.columns:
            df_main['project_stage'] = '未设置'
            
        display_cols = {
            'biz_code': '合同编号',
            'project_name': '项目名称',
            'project_stage': '项目阶段', 
            'client_name': '甲方单位',
            'contract_amount': '合同金额',
            'total_collected': '累计到账',
            'collection_progress': '回款进度(%)',
            'uncollected_contract_amount': '未到账金额'
        }
        
        df_display = df_main[list(display_cols.keys())].rename(columns=display_cols)
        df_display['回款进度(%)'] = pd.to_numeric(df_display['回款进度(%)'], errors='coerce').fillna(0.0)
        df_display.insert(0, '☑️', False)
        
        # 🟢 从底层汇聚所有的计划节点，作为下拉框的智能选项
        conn = crud_base.get_connection()
        try:

            sql = """
                SELECT milestone_name 
                FROM biz_payment_plans 
                WHERE deleted_at IS NULL 
                  AND milestone_name IS NOT NULL 
                  AND milestone_name != ''
                GROUP BY milestone_name
                ORDER BY MIN(planned_date) ASC NULLS LAST, MIN(id) ASC
            """
            stage_df = pd.read_sql_query(sql, conn)
            dynamic_stages = stage_df['milestone_name'].tolist()
        except Exception as e:
            dynamic_stages = []
        finally:
            if conn: conn.close()
            
        stage_options = ["未设置"] + dynamic_stages + ["已结项"]
        
        edited_df = st.data_editor(
            df_display,
            column_config={
                "☑️": st.column_config.CheckboxColumn("☑️", help="打勾将此合同提取到右侧操作台", default=False),
                "项目阶段": st.column_config.SelectboxColumn("📌 当前阶段 (双击修改)", help="修改后自动保存", options=stage_options, required=True),
                "回款进度(%)": st.column_config.ProgressColumn("回款进度(%)", format="%.2f %%", min_value=0.0, max_value=100.0),
                "合同编号": st.column_config.TextColumn("合同编号", disabled=True),
                "合同金额": st.column_config.NumberColumn("合同金额", disabled=True, format="¥ %.2f"),
                "累计到账": st.column_config.NumberColumn("累计到账", disabled=True, format="¥ %.2f"),
                "未到账金额": st.column_config.NumberColumn("未到账金额", disabled=True, format="¥ %.2f"),
            },
            width="stretch", hide_index=True, height=500, key="main_contract_editor" 
        )

        # 🟢 魔法引擎：静默捕捉左侧表格的“项目阶段”修改，立刻存库！
        if not edited_df.equals(df_display):
            changes_detected = False
            target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
            for i in range(len(df_display)):
                if df_display.iloc[i]['项目阶段'] != edited_df.iloc[i]['项目阶段']:
                    new_stage = edited_df.iloc[i]['项目阶段']
                    biz_code = df_display.iloc[i]['合同编号']
                    execute_raw_sql(f'UPDATE "{target_table}" SET project_stage = %s WHERE biz_code = %s', (new_stage, biz_code))
                    changes_detected = True
            if changes_detected:
                if ui and hasattr(ui, 'show_toast_success'): ui.show_toast_success("✅ 项目阶段已同步至数据库！")
                trigger_refresh()
                st.rerun()

    # ------------------------------------------
    # 🎛️ 右侧区域：三大 Tab 魔法操作枢纽
    # ------------------------------------------
    with col_form:
        st.subheader(f"🎛️ 操作台")
        
        # 🟢 新增核心魔法 2：智能拦截左侧表格的“打勾”事件
        auto_selected_biz_code = None
        # 筛选出所有被打勾的行 (为了容错，如果用户勾了多个，我们提取最下面的那一个)
        checked_rows = edited_df[edited_df['☑️'] == True]
        if not checked_rows.empty:
            auto_selected_biz_code = checked_rows.iloc[-1]['合同编号']
        
        col_select, col_edit = st.columns([8, 2])
        with col_select:
            contract_options = df_main.apply(lambda row: f"{row['biz_code']} | {row['project_name']}", axis=1).tolist()
            
            # 🟢 新增核心魔法 3：计算被勾选的合同在下拉框里排第几个
            default_index = 0
            if auto_selected_biz_code:
                for i, opt in enumerate(contract_options):
                    if opt.startswith(auto_selected_biz_code):
                        default_index = i
                        break
            
            # 动态绑定 index 属性，实现瞬间对齐
            selected_contract_str = st.selectbox(
                "🎯 目标主合同", 
                contract_options, 
                index=default_index, # 👈 就是这里让它自动切换的
                label_visibility="collapsed"
            )
            selected_biz_code = selected_contract_str.split(" | ")[0]
        
        with col_edit:
            if st.button("✏️ 修改", use_container_width=True):
                current_contract_data = df_main[df_main['biz_code'] == selected_biz_code].iloc[0].to_dict()
                st.session_state.show_main_contract_dialog = True
                st.session_state.current_edit_data = current_contract_data
                st.rerun()
        current_stage = df_main[df_main['biz_code'] == selected_biz_code]['project_stage'].fillna("未设置").iloc[0]
        # 🟢 核心重构：创建三个标签页
        current_contract_amount = float(df_main[df_main['biz_code'] == selected_biz_code]['contract_amount'].iloc[0])
        current_plans_df = load_payment_plans(selected_biz_code)

        tab_flow, tab_history, tab_plan, tab_audit = st.tabs(["⚡ 录入流水", "📜 财务明细", "📝 收款计划", "🛡️ 高级与审计"])
        
        # ==========================================
        # Tab 1: ⚡ 录入流水 (已打通底层)
        # ==========================================
        with tab_flow:
            action_type = st.radio("业务动作", ["录入开票 (开给甲方)","录入收款 (甲方打款)"], horizontal=True)
            
            # 🟢 构造计划节点下拉菜单字典
            with st.form(key="flow_form", clear_on_submit=True):
                # 🟢 魔法填充：自动获取项目当前阶段作为初始建议值
                # 这里将下拉框改为 text_input，实现“手写输入框”需求
                suggested_stage = current_stage if current_stage != "未设置" else ""
                input_stage = st.text_input("🎯 对应业务节点/阶段", value=suggested_stage, help="系统已自动提取当前阶段，您可根据实际情况微调（如：方案一期款）")
                
                amount = st.number_input("💵 操作金额 (元)", min_value=0.01, step=50000.0, format="%.2f")
                action_date = st.date_input("📅 发生日期", datetime.now())
                
                current_user = st.session_state.get('user_name', '当前系统用户')
                operator = st.text_input("👤 经办人", value=current_user, disabled=True)
                custom_remarks = st.text_input("📝 补充备注 (选填)", "")
                
                submit_btn = st.form_submit_button("✅ 确认提交并核算", use_container_width=True)
                
                if submit_btn:                    
                    final_remarks = f"【节点：{input_stage}】 {custom_remarks}".strip()
                    target_plan_code = None
                    selected_node_name = input_stage.strip()
                    if "收款" in action_type:
                        table_model = "biz_collections"
                        data_dict = {
                            'biz_code': f"COLL-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                            'main_contract_code': selected_biz_code,
                            'target_plan_code': target_plan_code,  # 🟢 精准写入流水表
                            'update_project_stage': selected_node_name if selected_node_name != "通用/无特定节点" else None,
                            'collected_amount': amount,
                            'collected_date': action_date.strftime('%Y-%m-%d'),
                            'operator': operator,
                            'remarks': final_remarks
                        }
                    else:
                        table_model = "biz_invoices"
                        data_dict = {
                            'biz_code': f"INV-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                            'main_contract_code': selected_biz_code,
                            'target_plan_code': target_plan_code,  # 🟢 精准写入发票表
                            'invoice_amount': amount,
                            'invoice_date': action_date.strftime('%Y-%m-%d'),
                            'operator': operator,
                            'remarks': final_remarks
                        }
                    
                    keys = list(data_dict.keys())
                    values = tuple(data_dict.values())
                    placeholders = ', '.join(['%s'] * len(keys))
                    sql = f"INSERT INTO {table_model} ({', '.join(keys)}) VALUES ({placeholders})"
                    success, msg = execute_raw_sql(sql, values)

                    if success:
                        # 🟢 同步推演：自动把主合同的阶段改过去！
                        if selected_node_name != "通用/无特定节点":
                            target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
                            execute_raw_sql(f'UPDATE "{target_table}" SET project_stage = %s WHERE biz_code = %s', (selected_node_name, selected_biz_code))
                        db.sync_main_contract_finance(selected_biz_code)

                        if ui and hasattr(ui, 'show_toast_success'): 
                            ui.show_toast_success(f"成功录入 {amount:,.2f} 元！")
                        trigger_refresh()
                    else:
                        st.error(f"录入失败: {msg}")
        # ==========================================
        # Tab 2 (新增): 📜 财务明细 (历史记录台账)
        # ==========================================
        with tab_history:
            sub_tab_coll, sub_tab_inv = st.tabs(["💰 历史收款记录", "📄 历史开票记录"])
            current_user = st.session_state.get('user_name', '当前系统用户')
            
            # ---------------- 款项面板 ----------------
            with sub_tab_coll:
                df_coll = load_financial_history(selected_biz_code, "collections")
                if not df_coll.empty:
                    # 动态 Key 防止复用冲突
                    coll_editor_key = f"coll_editor_{selected_biz_code}_{st.session_state.refresh_trigger}"
                    
                    # 插入供用户勾选的列
                    df_coll.insert(0, '🔴 作废', False)
                    
                    edited_coll = st.data_editor(
                        df_coll, 
                        width="stretch", 
                        hide_index=True,
                        disabled=["流水号", "收款日期", "金额(元)", "对应节点", "经办人", "备注", "录入时间"], # 冻结原有数据，禁止行内直改
                        column_config={
                            "🔴 作废": st.column_config.CheckboxColumn("🔴 作废", default=False, help="勾选后点击下方按钮作废"),
                            "金额(元)": st.column_config.NumberColumn("金额(元)", format="¥ %.2f")
                        },
                        key=coll_editor_key
                    )
                    
                    # 侦测选中项
                    selected_colls = edited_coll[edited_coll['🔴 作废'] == True]
                    if not selected_colls.empty:
                        st.warning(f"⚠️ 即将作废选中的 {len(selected_colls)} 笔收款记录，资金将从主合同中扣除。")
                        if st.button("🗑️ 确认作废收款流水", type="primary", use_container_width=True):
                            for _, row in selected_colls.iterrows():
                                db.void_financial_record(row['流水号'], "collections", current_user)
                            # 作废完毕后，立刻触发资金盘子重算
                            db.sync_main_contract_finance(selected_biz_code)

                            trigger_refresh()
                            st.rerun()
                else:
                    st.info("暂无有效收款记录")
                    
            # ---------------- 开票面板 ----------------
            with sub_tab_inv:
                df_inv = load_financial_history(selected_biz_code, "invoices")
                if not df_inv.empty:
                    inv_editor_key = f"inv_editor_{selected_biz_code}_{st.session_state.refresh_trigger}"
                    df_inv.insert(0, '🔴 作废', False)
                    
                    edited_inv = st.data_editor(
                        df_inv, 
                        width="stretch", 
                        hide_index=True,
                        disabled=["发票号", "开票日期", "金额(元)", "关联计划", "经办人", "备注", "录入时间"],
                        column_config={
                            "🔴 作废": st.column_config.CheckboxColumn("🔴 作废", default=False, help="勾选后点击下方按钮作废"),
                            "金额(元)": st.column_config.NumberColumn("金额(元)", format="¥ %.2f")
                        },
                        key=inv_editor_key
                    )
                    
                    selected_invs = edited_inv[edited_inv['🔴 作废'] == True]
                    if not selected_invs.empty:
                        st.warning(f"⚠️ 即将作废选中的 {len(selected_invs)} 笔开票记录。")
                        if st.button("🗑️ 确认作废开票流水", type="primary", use_container_width=True):
                            for _, row in selected_invs.iterrows():
                                db.void_financial_record(row['发票号'], "invoices", current_user)
                            # 作废完毕后，立刻触发资金盘子重算
                            db.sync_main_contract_finance(selected_biz_code)
                            trigger_refresh()
                            st.rerun()
                else:
                    st.info("暂无有效开票记录")
        # ==========================================
        # Tab 2: 📝 收款计划 (实时同步版)
        # ==========================================
        with tab_plan:
            # 🟢 实时拉取最新数据
            real_db_plans = load_payment_plans(selected_biz_code)
            
            if real_db_plans.empty:
                real_db_plans = pd.DataFrame([{
                    "计划编号": "", "款项节点": "初始阶段", "比例(%)": 0.0, 
                    "计划金额": 0.0, "预警日期": None, "备注": ""
                }])
            
            # 使用动态 Key 确保保存后 UI 强制重载
            editor_key = f"editor_{selected_biz_code}_{st.session_state.refresh_trigger}"
            
            edited_plans = st.data_editor(
                real_db_plans,
                num_rows="dynamic",
                column_config={
                    "计划编号": None, 
                    "款项节点": st.column_config.TextColumn("款项节点", required=True),
                    "比例(%)": st.column_config.NumberColumn("比例(%)", format="%.2f%%"),
                    "计划金额": st.column_config.NumberColumn("计划金额 (元)", format="%.2f"),
                    "预警日期": st.column_config.DateColumn("预警日期"),
                    "备注": st.column_config.TextColumn("补充说明")
                },
                width="stretch",
                hide_index=True,
                key=editor_key
            )
            
            if st.button("💾 确认保存/覆盖计划", use_container_width=True, type="primary"):
                current_user = st.session_state.get('user_name', 'System')
                success, msg = save_payment_plans(selected_biz_code, edited_plans, current_user, current_contract_amount)
                
                if success:
                    ui.show_toast_success("计划已成功覆盖保存并完成互算！")
                    trigger_refresh() # 🟢 改变 Key，迫使下次加载执行 load_payment_plans
                    st.rerun()
                else:
                    st.error(f"保存失败: {msg}")

        # ==========================================
        # Tab 3: 🛡️ 高级与审计
        # ==========================================
        # ==========================================
        # Tab 3: 🛡️ 高级与审计 (接入业财风控引擎)
        # ==========================================
        with tab_audit:
            st.warning("⚠️ 高级与危险操作区")
            
            # --- 1. 计提操作区 ---
            st.markdown("#### 💰 财务计提结算")
            st.caption("💡 计提后，该合同将被标记为财务完结，并将随着年度结转进入归档。")
            
            # 🟢 动态判断该主合同是否已经计提过
            # 注意：需确保主合同表有 is_provisioned 字段，如果没有提取到，默认算作未计提
            is_accrued = df_main[df_main['biz_code'] == selected_biz_code].get('is_provisioned', pd.Series(['否'])).iloc[0] == '是'
            
            if is_accrued:
                st.success("✅ 该主合同已完成财务计提，等待年度结转。")
            else:
                if st.button("📥 申请主合同计提结算", type="primary", use_container_width=True):
                    # 🟢 调用 crud_finance 里的核心计提函数 (内部已包含分包未结清的拦截逻辑)
                    success, msg = db.mark_project_as_accrued("main_contract", selected_biz_code)
                    if success:
                        if ui and hasattr(ui, 'show_toast_success'): ui.show_toast_success("✅ 计提成功！")
                        trigger_refresh()
                        st.rerun()
                    else:
                        st.error(msg) # 拦截信息（比如差额多少元）会在这里直接红色打印出来
            
            st.markdown("---")
            
            # --- 2. 软删除操作区 ---
            st.markdown("#### 🗑️ 合同作废")
            if st.button("🗑️ 软删除该合同 (移入回收站)", use_container_width=True):
                # 🚨 删除前的第一步：呼叫风控锁！
                passed, error_msg = crud.check_main_contract_clearance(selected_biz_code)
                
                if not passed:
                    # 拦截：弹出具体是哪些分包没结清
                    st.error(error_msg) 
                else:
                    # 放行：执行具体的软删除逻辑
                    current_user = st.session_state.get('user_name', 'System')
                    target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
                    
                    # 🟢 核心修复：通过 biz_code 从 df_main 中精准提取物理 id
                    target_id = int(df_main[df_main['biz_code'] == selected_biz_code]['id'].iloc[0])
                    
                    success, msg = crud.soft_delete_project(
                        project_id=target_id, 
                        table_name=target_table,
                        operator_name=current_user
                    )
                    
                    if success:
                        st.toast("已安全移入系统全局回收站", icon="🗑️")
                        trigger_refresh()
                        st.rerun()
                    else:
                        st.error(f"删除失败: {msg}")
            
            st.markdown("---")
            # 🟢 召唤神器的时光机功能 (审计日志)
            if ui and hasattr(ui, 'render_audit_timeline'):
                try:
                    ui.render_audit_timeline(selected_biz_code, "main_contract")
                except Exception as e:
                    st.error(f"时光机加载失败: {e}")

debug_kit.execute_debug_logic()
```

#### 📄 03_🛠️_分包合同管理.py

```python
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import warnings
from pathlib import Path

# 彻底静默 pandas 的 SQLAlchemy 警告
warnings.filterwarnings('ignore', category=UserWarning, message='.*SQLAlchemy.*')

# 确保能找到 backend 模块
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database import crud
from backend.database.db_engine import execute_raw_sql, get_connection
from backend.config import config_manager as cfg
import backend.database as db

import sidebar_manager
import debug_kit 
import components as ui

# 隐藏/只读字段配置
FORM_HIDDEN_FIELDS = [] 
FORM_READONLY_FIELDS = ['total_paid', 'total_invoiced_from_sub', 'unpaid_amount']

# ==========================================
# 0. 页面配置与初始化
# ==========================================
st.set_page_config(page_title="分包合同管理 (支出侧)", page_icon="🛡️", layout="wide")

if 'refresh_trigger' not in st.session_state:
    st.session_state.refresh_trigger = 0

def trigger_refresh():
    st.session_state.refresh_trigger += 1

# ==========================================
# 1. 核心数据获取 (带缓存)
# ==========================================
@st.cache_data(ttl=5, show_spinner=False)
def load_sub_contracts(trigger):
    return db.fetch_dynamic_records('sub_contract')

@st.cache_data(ttl=5, show_spinner=False)
def load_main_contracts_dict(trigger):
    """专门为魔法下拉框准备：拉取所有主合同并做成映射字典"""
    df_main = db.fetch_dynamic_records('main_contract')
    if df_main.empty:
        return {}
    # 返回形如 {"MAIN-001": "万科项目", "MAIN-002": "海尔项目"} 的字典
    return pd.Series(df_main['project_name'].values, index=df_main['biz_code']).to_dict()

def load_sub_financial_history(sub_contract_code, table_type="payments"):
    """拉取分包侧的 纯付款 / 纯收票 历史"""
    conn = get_connection()
    try:
        if table_type == "payments":
            sql = '''
                SELECT biz_code AS "流水号", payment_date AS "付款日期", 
                       payment_amount AS "金额(元)", payment_method AS "支付方式", 
                       operator AS "经办人", remarks AS "备注", created_at AS "录入时间"
                FROM biz_outbound_payments
                WHERE sub_contract_code = %s AND deleted_at IS NULL
                ORDER BY payment_date DESC, created_at DESC
            '''
        else:
            sql = '''
                SELECT biz_code AS "发票号", invoice_date AS "收票日期", 
                       invoice_amount AS "金额(元)", invoice_number AS "发票号码", 
                       invoice_type AS "发票类型", operator AS "经办人", remarks AS "备注"
                FROM biz_sub_invoices
                WHERE sub_contract_code = %s AND deleted_at IS NULL
                ORDER BY invoice_date DESC, created_at DESC
            '''
        with conn.cursor() as cur:
            cur.execute(sql, (str(sub_contract_code),)) 
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=cols)
            
        if not df.empty:
            df['金额(元)'] = pd.to_numeric(df['金额(元)'], errors='coerce').fillna(0.0)
            if '录入时间' in df.columns:
                df['录入时间'] = pd.to_datetime(df['录入时间']).dt.strftime('%Y-%m-%d %H:%M')
        return df
    except Exception as e:
        st.error(f"⚠️ 读取历史失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

df_sub = load_sub_contracts(st.session_state.refresh_trigger)
main_dict = load_main_contracts_dict(st.session_state.refresh_trigger)

sidebar_manager.render_sidebar()

# ==========================================
# 2. 📝 弹窗：分包合同录入 (搭载魔法下拉框)
# ==========================================
@st.dialog("🛡️ 分包合同登记", width="large")
def sub_contract_form_dialog(existing_data=None):
    if ui and hasattr(ui, 'render_dynamic_form'):
        
        # 🟢 AI 占位符 (极简重构布局)
        st.subheader("🤖 AI 分包合同智能解析")
        uploaded_files = st.file_uploader("📂 请拖拽或选择待解析合同 (支持 PDF/Word)", accept_multiple_files=True)
        c_cat, c_btn = st.columns([3, 1])
        with c_cat:
            file_category = st.selectbox(
                "🗂️ 附件类别", 
                ["分包合同正文 (需 AI 解析)", "工程量清单", "结算单", "其他附件"],
                label_visibility="collapsed" 
            )
        with c_btn:
            ai_ready = uploaded_files is not None and len(uploaded_files) > 0 and "(需 AI 解析)" in file_category
            if st.button("✨ 一键 AI 提取", type="primary", disabled=not ai_ready, use_container_width=True):
                with st.spinner("🧠 AI 正在极速提取中..."):
                    import time; time.sleep(1)
                    st.success("🎉 AI 提取完毕！下方表单已更新。")
        st.markdown("---") 

        is_edit = existing_data is not None
        form_title = "✏️ 修改分包合同" if is_edit else "🆕 录入新分包合同"
        
        if not is_edit:
            target_table = cfg.get_model_config("sub_contract").get("table_name", "biz_sub_contracts")
            new_biz_code = crud.generate_biz_code(target_table, prefix_char="SUB")
            current_data = {'biz_code': new_biz_code}
        else:
            current_data = existing_data
            
        # 🟢 终极魔法：构造下拉选项和格式化函数
        all_main_codes = [""] + list(main_dict.keys())
        my_formatters = {
            "book_main_code": lambda code: f"[{code}] {main_dict.get(code, '未知项目')}" if code else "未关联",
            "actual_main_code": lambda code: f"[{code}] {main_dict.get(code, '未知项目')}" if code else "未关联"
        }
        my_options = {
            "book_main_code": all_main_codes,
            "actual_main_code": all_main_codes
        }
            
        # 渲染表单并注入魔法
        result = ui.render_dynamic_form(
            "sub_contract", 
            form_title, 
            current_data, 
            hidden_fields=FORM_HIDDEN_FIELDS,
            readonly_fields=FORM_READONLY_FIELDS,
            dynamic_options=my_options,
            format_funcs=my_formatters
        )
        
        if result:
            # =======================================================
            # 🟢 极简平替魔法：尊崇账面 EBM，单向自动推演实际关联
            # =======================================================
            book_code = result.get('book_main_code')
            actual_code = result.get('actual_main_code')
            
            # 1. 绝对正统逻辑：填了账面（发票资金归属），没填实际（干活归属），自动补齐
            if book_code and not actual_code:
                result['actual_main_code'] = book_code
                
            # 2. 财务防线兜底：万一业务员不懂规矩，只填了实际干活的项目，
            # 系统必须强制把它也变成账面项目，坚决不允许 book_main_code 为空（防风控击穿）
            elif actual_code and not book_code:
                result['book_main_code'] = actual_code
            # =======================================================
            final_biz_code = result.get('biz_code', current_data.get('biz_code'))
            result['biz_code'] = final_biz_code
            target_id = int(existing_data['id']) if is_edit and 'id' in existing_data else None
            current_user = st.session_state.get('user_name', 'System')
            
            success, msg = crud.upsert_dynamic_record(
                model_name="sub_contract", 
                data_dict=result, 
                record_id=target_id,
                operator_name=current_user
            )
            
            if success:
                # 调用解耦后的附件大管家
                if uploaded_files:
                    from backend.services.file_service import save_attachment
                    target_table = cfg.get_model_config("sub_contract").get("table_name", "biz_sub_contracts")
                    for uf in uploaded_files:
                        save_attachment(final_biz_code, uf, target_table, file_category=file_category)
                ui.show_toast_success("分包数据保存成功！")
                trigger_refresh() 
                st.rerun()
            else:
                ui.show_toast_error(f"保存失败: {msg}")       

# ==========================================
# 3. 📊 顶层：防失血 KPI 预警看板
# ==========================================
col_title, col_add_btn = st.columns([8, 2])
with col_title:
    st.title("🛡️ 分包支出与税务防线")
with col_add_btn:
    st.write("") 
    if st.button("➕ 录入新分包合同", type="primary", use_container_width=True):
        sub_contract_form_dialog() 

if ui and hasattr(ui, 'style_metric_card'):
    ui.style_metric_card()

if not df_sub.empty:
    total_cost = df_sub['sub_amount'].astype(float).sum()
    total_paid = df_sub['total_paid'].astype(float).sum()
    total_unpaid = df_sub['unpaid_amount'].astype(float).sum() if 'unpaid_amount' in df_sub.columns else 0.0
    total_inv_rec = df_sub['total_invoiced_from_sub'].astype(float).sum() if 'total_invoiced_from_sub' in df_sub.columns else 0.0
    
    # 核心风控：倒挂欠票金额 = 已付真金白银 - 财务收到的发票
    missing_invoices = total_paid - total_inv_rec
    # 防止因为少量尾差出现负数误报
    missing_invoices = missing_invoices if missing_invoices > 0 else 0.0

    paid_rate = (total_paid / total_cost) * 100 if total_cost else 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💸 总成本盘子", f"¥ {total_cost:,.2f}", delta="支出预算池", delta_color="off")
    with col2:
        st.metric("🏦 累计已支付", f"¥ {total_paid:,.2f}", delta=f"资金流出率: {paid_rate:.1f}%") 
    with col3:
        st.metric("🧾 剩余应付敞口", f"¥ {total_unpaid:,.2f}", delta="未来资金流出压力", delta_color="inverse")
    with col4:
        # 🚨 红色税务预警：付了钱没拿回发票
        warn_color = "inverse" if missing_invoices > 0 else "off"
        warn_text = "🚨 税务流失红线" if missing_invoices > 0 else "票款安全"
        st.metric("⚠️ 欠票敞口 (付>票)", f"¥ {missing_invoices:,.2f}", delta=warn_text, delta_color=warn_color)
    
st.markdown("---")

# ==========================================
# 4. 黄金分割：左表(关注背靠背) + 右抽屉(减法 Tab)
# ==========================================
if df_sub.empty:
    st.info("📭 当前暂无分包合同数据。")
else:
    col_table, col_form = st.columns([2.5, 1.5])

    # ------------------------------------------
    # 🗂️ 左表：强化背靠背风险标识
    # ------------------------------------------
    with col_table:
        st.subheader("📑 分包防线台账")
        
        display_cols = {
            'biz_code': '合同编号',
            'sub_company_name': '分包单位',
            'sub_amount': '合同金额',
            'total_paid': '累计已付',
            'current_payable': '本期应付', # 🟢 增加这行！
            'is_back_to_back': '背靠背', 
            'settlement_status': '结算状态'
        }
        for col in display_cols.keys():
            if col not in df_sub.columns:
                df_sub[col] = None

        df_display = df_sub[list(display_cols.keys())].rename(columns=display_cols)
        df_display.insert(0, '☑️', False)
        
        df_display['背靠背'] = df_display['背靠背'].apply(lambda x: True if str(x).lower() in ['true', '1', '是'] else False)

        edited_df = st.data_editor(
            df_display,
            column_config={
                "☑️": st.column_config.CheckboxColumn("☑️", default=False),
                "背靠背": st.column_config.CheckboxColumn("背靠背条款", help="打勾代表需等甲方付款后才付款", disabled=True),
                "合同金额": st.column_config.NumberColumn("合同金额", disabled=True, format="¥ %.2f"),
                "累计已付": st.column_config.NumberColumn("累计已付", disabled=True, format="¥ %.2f"),
                "本期应付": st.column_config.NumberColumn("本期应付(背靠背)", disabled=True, format="¥ %.2f"), # 🟢 增加这行列配置！
            },
            width="stretch", hide_index=True, height=500
        )

    # ------------------------------------------
    # 🎛️ 右操作台：极简 3 Tab
    # ------------------------------------------
    with col_form:
        st.subheader(f"🎛️ 支出枢纽")
        
        auto_selected_biz_code = None
        checked_rows = edited_df[edited_df['☑️'] == True]
        if not checked_rows.empty:
            auto_selected_biz_code = checked_rows.iloc[-1]['合同编号']
        
        col_select, col_edit = st.columns([8, 2])
        with col_select:
            contract_options = df_sub.apply(lambda row: f"{row['biz_code']} | {row['sub_company_name']}", axis=1).tolist()
            default_index = 0
            if auto_selected_biz_code:
                for i, opt in enumerate(contract_options):
                    if opt.startswith(auto_selected_biz_code):
                        default_index = i
                        break
            
            selected_contract_str = st.selectbox("🎯 目标分包合同", contract_options, index=default_index, label_visibility="collapsed")
            selected_biz_code = selected_contract_str.split(" | ")[0]
        
        with col_edit:
            if st.button("✏️ 修改", use_container_width=True):
                current_contract_data = df_sub[df_sub['biz_code'] == selected_biz_code].iloc[0].to_dict()
                sub_contract_form_dialog(existing_data=current_contract_data)

        # 🟢 减法 Tab：去掉了收款计划，只保留流水、历史、审计
        tab_flow, tab_history, tab_audit = st.tabs(["⚡ 录入流出", "📜 财务明细", "🛡️ 审计"])
        
        # ================= Tab 1: 录入流出 =================
        with tab_flow:
            action_type = st.radio("业务动作", ["录入付款 (流出真金白银)","录入收票 (收到进项票)"], horizontal=True)
            
            with st.form(key="sub_flow_form", clear_on_submit=True):
                amount = st.number_input("💵 操作金额 (元)", min_value=0.01, step=10000.0, format="%.2f")
                action_date = st.date_input("📅 发生日期", datetime.now())
                
                # 动态字段渲染
                if "收票" in action_type:
                    invoice_num = st.text_input("🧾 发票号码 (必填)")
                    inv_type_options = cfg.get_field_meta("sub_contract").get("tax_rate", {}).get("options", ["3%", "6%", "9%"])
                    invoice_type = st.selectbox("🏷️ 进项税率", inv_type_options)
                else:
                    pay_method = st.selectbox("💳 支付方式", ["电汇", "承兑汇票", "现金", "抵扣"])

                current_user = st.session_state.get('user_name', 'System')
                custom_remarks = st.text_input("📝 补充备注 (选填)", "")
                
                if st.form_submit_button("✅ 确认提交并核算", use_container_width=True):
                    if "收票" in action_type:
                        sql = "INSERT INTO biz_sub_invoices (biz_code, sub_contract_code, invoice_amount, invoice_date, invoice_number, invoice_type, operator, remarks) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                        vals = (f"SINV-{datetime.now().strftime('%Y%m%d%H%M%S')}", selected_biz_code, amount, action_date, invoice_num, invoice_type, current_user, custom_remarks)
                        success, msg = execute_raw_sql(sql, vals)
                    else:
                        # 🟢 终极修正：不再直接裸写 SQL，而是调用后端的资金防线！
                        date_str = action_date.strftime('%Y-%m-%d')
                        success, msg = crud.submit_sub_payment(
                            sub_biz_code=selected_biz_code,
                            payment_amount=amount,
                            operator=current_user,
                            payment_date=date_str,
                            remarks=custom_remarks
                        )
                    
                    if success:                        
                        ui.show_toast_success(f"成功录入 {amount:,.2f} 元！")
                        trigger_refresh()
                        st.rerun() # 🟢 加上 rerun 强制刷新页面，让“本期应付”瞬间变化
                    else:
                        st.error(f"🚨 操作拦截: {msg}") # 如果超付，这里就会弹出红字警告！

        # ================= Tab 2: 财务历史 =================
        with tab_history:
            sub_tab_pay, sub_tab_inv = st.tabs(["💸 付款历史", "🧾 收票历史"])
            
            with sub_tab_pay:
                df_pay = load_sub_financial_history(selected_biz_code, "payments")
                if not df_pay.empty:
                    st.dataframe(df_pay, width="stretch", hide_index=True)
                else:
                    st.info("暂无付款流水")
                    
            with sub_tab_inv:
                df_inv = load_sub_financial_history(selected_biz_code, "invoices")
                if not df_inv.empty:
                    st.dataframe(df_inv, width="stretch", hide_index=True)
                else:
                    st.info("暂无收票流水")

        # ================= Tab 3: 审计 =================
            with tab_audit:
                st.markdown("#### 🗑️ 合同作废")
                if st.button("🗑️ 软删除该分包合同", use_container_width=True):
                    target_table = cfg.get_model_config("sub_contract").get("table_name", "biz_sub_contracts")
                    current_user = st.session_state.get('user_name', 'System')
                    
                    # 🟢 必须先算出 target_id
                    target_id = int(df_sub[df_sub['biz_code'] == selected_biz_code]['id'].iloc[0])
                    
                    # 🟢 正确的闭合调用
                    success, msg = crud.soft_delete_project(
                        project_id=target_id, 
                        table_name=target_table,
                        operator_name=current_user
                    )
                    
                    if success:
                        st.toast("已安全移入系统全局回收站", icon="🗑️")
                        trigger_refresh()
                        st.rerun()
                    else:
                        st.error(f"作废失败: {msg}")
                
                st.markdown("---")
                if ui and hasattr(ui, 'render_audit_timeline'):
                    ui.render_audit_timeline(selected_biz_code, "sub_contract")

debug_kit.execute_debug_logic()
```

#### 📄 04_📊_数据分析.py

```python
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

# --- 年份选择 ---
valid_years = sorted(df_all[df_all['sign_year'] > 1900]['sign_year'].unique().tolist(), reverse=True)
if not valid_years:
    st.warning("数据中无有效年份，请检查日期列。")
    st.stop()

current_year = datetime.now().year
default_idx = valid_years.index(current_year) if current_year in valid_years else 0

available_tables = df_all['origin_table'].unique().tolist()
# 在最前面加上“全库”选项
scope_options = ["🌍 总览 "] + available_tables

# 调整顶部布局，分出两个选择框
c_year, c_scope, _ = st.columns([1, 1.5, 2])
with c_year:
    analysis_year = st.selectbox("📅 选择分析年份", valid_years, index=default_idx)
with c_scope:
    analysis_scope = st.selectbox(
        "🏢 选择分析范围", 
        scope_options, 
        index=0,
        format_func=ui.remove_prefix_formatter("data_")
    )

st.divider()

# =========================================================
# 🟢 新增：全局数据切片 (核心过滤逻辑)
# =========================================================
# 如果用户选了特定的表，就把 df_all 砍掉一部分，只留下选中的表的数据
if analysis_scope != "🌍 总览 ":
    df_all = df_all[df_all['origin_table'] == analysis_scope]

st.divider()

# --- 数据切片 ---
# 1. 本年新签
mask_new = (df_all['sign_year'] == analysis_year)
df_new = df_all[mask_new].copy()

# 2. 往年结转 (以前签的 + 有合同额的)
mask_carry = (df_all['sign_year'] < analysis_year) & (df_all['val_contract'] > 10)
df_carry = df_all[mask_carry].copy()

# 指标计算
new_contract_sum = df_new['val_contract'].sum()
new_collection_sum = df_new['val_collection'].sum()
carry_debt_sum = df_carry['val_uncollected'].sum()
total_debt = df_new['val_uncollected'].sum() + carry_debt_sum

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
c_ai_title, c_ai_action = st.columns([2, 1])
with c_ai_title:
    st.subheader("🤖 AI 经营诊断报告")
    st.caption("生成 CEO 视角的决策建议。")
with c_ai_action:
    if st.button("✨ 生成简报 (演示)", type="primary", width="stretch"):
        st.success("AI 接口已就绪，等待接入...")

debug_kit.execute_debug_logic()
```

#### 📄 05_🏢_往来单位.py

```python
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
    
    # 获取正确的 biz_code
    if mode == "add":
        new_code = crud.generate_biz_code(model_name=model_name, prefix_char="ENT")
        current_data = {'biz_code': new_code}
    else:
        current_data = initial_data

    # 2. 🟢 统一常量控制网关：定义隐藏和只读字段
    FORM_HIDDEN_FIELDS = ['id', 'deleted_at', 'source_file', 'sheet_name', 'extra_props', 'created_at', 'updated_at']
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
    # ✂️ 删除了 "查看回收站" 的 checkbox
    
with c_add:
    if st.button("➕ 新增单位", type="primary", width="stretch"):
        render_enterprise_form(mode="add", model_name=selected_model, target_table=target_table)

st.divider()

# --- 🟢 V2.0 查询逻辑 (纯净版，只看存活数据) ---
try:
    df_result = crud.fetch_dynamic_records(selected_model, keyword)
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
    
    # 自动生成类似 {"company_name": "单位名称"} 的翻译字典
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
        
        # 🟢 极简操作区：只有编辑、历史和删除
        ac1, ac2, ac3 = st.columns([1, 1, 1]) 
        with ac1:
            if st.button("📝 修改信息", type="primary", width="stretch"):
                render_enterprise_form(mode="edit", initial_data=selected_row, model_name=selected_model, target_table=target_table)
        with ac2:
            if st.button("🕰️ 查看操作历史", width="stretch"):
                show_audit_log_dialog(current_biz_code, selected_model)
        with ac3:
            if st.button("🗑️ 删除此单位 (软删除)", type="secondary", width="stretch"):
                # 🟢 1. 获取当前操作人（防呆设计）
                current_user = st.session_state.get('user_name', 'System')
                
                # 🟢 2. 调用后端正规军，把 current_user 传进去！
                success, msg = crud.soft_delete_project(
                    project_id=int(selected_row['id']), 
                    table_name=target_table,
                    operator_name=current_user
                )
                
                if success:
                    st.success("✅ 数据已移入回收站。")
                    st.rerun()
                else:
                    st.error(msg)
else:
    st.info("数据为空，或未找到匹配项。")

# 调试工具
debug_kit.execute_debug_logic()
```

#### 📄 06_📥_导入Excel.py

```python
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
            NEW_COL_OPT = "(新建中文物理列)" 
            IGNORE_OPT = "📦 [附加属性] 存入 JSONB"
            all_opts = [NEW_COL_OPT] + standard_opts + [IGNORE_OPT]
            
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
                    
                    if selected_opt == NEW_COL_OPT:
                        user_final_mapping[col_original] = "NEW_PHYSICAL" 
                    elif selected_opt != IGNORE_OPT:
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
```

#### 📄 07_⚙️_系统管理.py

```python
# 文件位置: streamlit_lab/pages/07_⚙️_系统管理.py
import sys
from pathlib import Path
import json

# 🟢 寻路魔法
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from werkzeug.security import generate_password_hash

# 接入新底座
from backend.database.db_engine import get_connection, execute_raw_sql
from backend.config import config_manager as cfg
from sidebar_manager import render_sidebar
import debug_kit
import components as ui

st.set_page_config(page_title="系统管理控制台", page_icon="⚙️", layout="wide")
render_sidebar()

st.title("⚙️ 系统管理控制台")
st.caption("Admin Console：全局用户、回收站与系统级日志调度中心。")

# =========================================================
# 🛠️ 弹窗：新建员工账号
# =========================================================
@st.dialog("🆕 新增系统账号", width="small")
def create_user_dialog():
    with st.form("new_user_form"):
        username = st.text_input("登录账号 (用户名) *", placeholder="例如: zhangsan")
        password = st.text_input("初始密码 *", type="password", placeholder="建议包含字母和数字")
        role = st.selectbox("系统角色", ["普通员工", "部门经理", "财务专员", "系统管理员"])
        
        if st.form_submit_button("💾 保存账号", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("账号和密码不能为空！")
                st.stop()
                
            # 🟢 1. 检查账号是否重复
            check_sql = "SELECT id FROM sys_users WHERE username = %s"
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(check_sql, (username,))
                if cur.fetchone():
                    st.error("该账号已存在，请换一个名称。")
                    conn.close()
                    st.stop()
            
            # 🟢 2. 密码单向哈希加密 (绝对不能存明文！)
            hashed_pwd = generate_password_hash(password)
            
            # 🟢 3. 安全入库
            insert_sql = """
                INSERT INTO sys_users (username, password_hash, role, status)
                VALUES (%s, %s, %s, 'active')
            """
            try:
                with conn.cursor() as cur:
                    cur.execute(insert_sql, (username, hashed_pwd, role))
                conn.commit()
                st.toast("✅ 账号创建成功！")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"创建失败: {e}")
            finally:
                conn.close()

# =========================================================
# 页面布局：四大管理模块
# =========================================================
tab_users, tab_trash, tab_audit, tab_job = st.tabs([
    "👥 员工账号管理", 
    "🗑️ 全局回收站", 
    "🕵️ 操作审计日志 (Audit)", 
    "⚙️ 后台任务日志 (Jobs)"
])

# ---------------------------------------------------------
# 模块 1：👥 员工账号管理
# ---------------------------------------------------------
with tab_users:
    c_title, c_btn = st.columns([8, 2])
    with c_title:
        st.subheader("账号与权限分配")
    with c_btn:
        if st.button("➕ 新增账号", type="primary", use_container_width=True):
            create_user_dialog()
            
    # 获取用户列表
    success, df_users = execute_raw_sql("SELECT id, username, role, status, last_login_at, created_at FROM sys_users ORDER BY id ASC")
    
    if success and not df_users.empty:
        # 添加布尔控制列
        df_users['is_active'] = df_users['status'].apply(lambda x: True if x == 'active' else False)
        df_users.insert(0, '☑️ 选中', False)
        
        edited_users = st.data_editor(
            df_users,
            width="stretch",
            hide_index=True,
            disabled=["id", "username", "created_at", "last_login_at", "status"],
            column_config={
                "☑️ 选中": st.column_config.CheckboxColumn("选择操作", default=False),
                "is_active": st.column_config.CheckboxColumn("允许登录 (活跃状态)"),
                "role": st.column_config.SelectboxColumn("角色", options=["普通员工", "部门经理", "财务专员", "系统管理员"]),
                "last_login_at": st.column_config.DatetimeColumn("最后登录", format="YYYY-MM-DD HH:mm"),
            }
        )
        
        # 侦测状态或角色变化
        if not edited_users.equals(df_users):
            conn = get_connection()
            try:
                for i in range(len(df_users)):
                    old_active = df_users.iloc[i]['is_active']
                    new_active = edited_users.iloc[i]['is_active']
                    old_role = df_users.iloc[i]['role']
                    new_role = edited_users.iloc[i]['role']
                    uid = int(df_users.iloc[i]['id'])
                    uname = df_users.iloc[i]['username']
                    
                    # 防止超级管理员被禁用
                    if not new_active and uname == 'admin':
                        st.error("⛔ 保护机制：系统默认超级管理员 'admin' 无法被禁用！")
                        continue
                        
                    if old_active != new_active or old_role != new_role:
                        new_status = 'active' if new_active else 'disabled'
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE sys_users SET status = %s, role = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                                (new_status, new_role, uid)
                            )
                conn.commit()
                st.toast("✅ 账号状态已更新")
                st.rerun()
            except Exception as e:
                st.error(f"更新失败: {e}")
            finally:
                conn.close()
                
        # 密码重置区
        selected_users = edited_users[edited_users['☑️ 选中'] == True]
        if not selected_users.empty:
            target_username = selected_users.iloc[0]['username']
            st.warning(f"⚠️ 即将重置账号 **{target_username}** 的密码：")
            c_newpwd, c_reset = st.columns([3, 1])
            with c_newpwd:
                new_pwd = st.text_input("输入新密码", type="password", key="reset_pwd_input")
            with c_reset:
                st.write("") # 占位对齐
                if st.button("🔄 强制重置", type="primary", use_container_width=True):
                    if new_pwd:
                        hashed_pwd = generate_password_hash(new_pwd)
                        execute_raw_sql("UPDATE sys_users SET password_hash = %s WHERE username = %s", (hashed_pwd, target_username))
                        st.success(f"已将 {target_username} 的密码重置为新密码！")
                    else:
                        st.error("新密码不能为空")
    else:
        st.info("系统暂无账号，请点击右上角新增。")

# ---------------------------------------------------------
# 模块 2：🗑️ 全局回收站
# ---------------------------------------------------------
with tab_trash:
    st.subheader("全局回收站")
    st.caption("所有被软删除的业务数据均在此处。支持一键还原。")
    
    # 动态扫描所有业务表中的删除数据
    config_models = cfg.load_data_rules().get("models", {})
    trash_data = []
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for m_name, m_cfg in config_models.items():
                t_name = m_cfg.get("table_name")
                if not t_name: continue
                
                # 尝试查询已删除的数据
                try:
                    # 动态判断有没有项目名称等易读字段
                    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t_name}'")
                    cols = {row[0] for row in cur.fetchall()}
                    
                    name_col = "project_name" if "project_name" in cols else ("sub_company_name" if "sub_company_name" in cols else "biz_code")
                    
                    cur.execute(f"""
                        SELECT id, biz_code, "{name_col}" as display_name, deleted_at, deleted_by 
                        FROM "{t_name}" 
                        WHERE deleted_at IS NOT NULL
                    """)
                    for row in cur.fetchall():
                        trash_data.append({
                            "模型": m_name,
                            "物理表": t_name,
                            "ID": row[0],
                            "业务编号": row[1],
                            "名称/摘要": row[2],
                            "删除时间": row[3].strftime("%Y-%m-%d %H:%M") if row[3] else "未知",
                            "操作人": row[4] or "未知"
                        })
                except Exception as e:
                    pass # 表可能不存在，跳过
    finally:
        conn.close()
        
    if trash_data:
        df_trash = pd.DataFrame(trash_data)
        df_trash.insert(0, '☑️ 选中', False)
        
        edited_trash = st.data_editor(
            df_trash,
            width="stretch",
            hide_index=True,
            disabled=["模型", "物理表", "ID", "业务编号", "名称/摘要", "删除时间", "操作人"]
        )
        
        selected_trash = edited_trash[edited_trash['☑️ 选中'] == True]
        if not selected_trash.empty:
            if st.button("♻️ 还原选中数据", type="primary"):
                conn = get_connection()
                try:
                    for _, row in selected_trash.iterrows():
                        t_name = row['物理表']
                        r_id = row['ID']
                        with conn.cursor() as cur:
                            cur.execute(f'UPDATE "{t_name}" SET deleted_at = NULL, deleted_by = NULL WHERE id = %s', (r_id,))
                    conn.commit()
                    st.success("✅ 数据已成功还原，并重返业务列表！")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"还原失败: {e}")
                finally:
                    conn.close()
    else:
        st.success("🎉 回收站目前空空如也。")

# ---------------------------------------------------------
# 模块 3：🕵️ 操作审计日志 (Audit Logs)
# ---------------------------------------------------------
with tab_audit:
    st.subheader("全局操作审计总站")
    st.caption("系统内所有的增、删、改痕迹均在此留底（防篡改）。仅显示最新 200 条。")
    
    success, df_audit = execute_raw_sql("""
        SELECT id, created_at, operator_name, action, model_name, biz_code, diff_data 
        FROM sys_audit_logs 
        ORDER BY created_at DESC LIMIT 200
    """)
    
    if success and not df_audit.empty:
        # 优化显示格式
        df_audit['created_at'] = pd.to_datetime(df_audit['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        # 提取 diff_data 摘要
        df_audit['变更字段数'] = df_audit['diff_data'].apply(lambda x: len(json.loads(x)) if isinstance(x, str) else 0)
        
        st.dataframe(
            df_audit[['created_at', 'operator_name', 'action', 'model_name', 'biz_code', '变更字段数']],
            width="stretch",
            hide_index=True,
            column_config={
                "created_at": "操作时间",
                "operator_name": "操作人",
                "action": "动作",
                "model_name": "模块",
                "biz_code": "业务编号"
            }
        )
        
        st.markdown("##### 🔍 穿透查看底层差异 JSON")
        biz_sel = st.selectbox("选择要查看差异细节的业务编号", df_audit['biz_code'].unique().tolist())
        detail_json = df_audit[df_audit['biz_code'] == biz_sel].iloc[0]['diff_data']
        try:
            st.json(json.loads(detail_json))
        except:
            st.write(detail_json)
    else:
        st.info("暂无审计日志。")

# ---------------------------------------------------------
# 模块 4：⚙️ 后台任务日志 (Job Logs)
# ---------------------------------------------------------
with tab_job:
    st.subheader("后台任务监控中心")
    st.caption("Excel 批量导入、财务年度结转等耗时任务的执行结果。")
    
    success, df_jobs = execute_raw_sql("""
        SELECT id, created_at, operator, job_type, target_model, source_name, status, total_count, success_count, fail_count, error_details
        FROM sys_job_logs
        ORDER BY created_at DESC LIMIT 100
    """)
    
    if success and not df_jobs.empty:
        df_jobs['created_at'] = pd.to_datetime(df_jobs['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        def status_emoji(s):
            if s == 'success': return "✅ 成功"
            if s == 'failed': return "❌ 失败"
            if s == 'partial_fail': return "⚠️ 部分失败"
            return "⏳ 处理中"
            
        df_jobs['执行状态'] = df_jobs['status'].apply(status_emoji)
        
        st.dataframe(
            df_jobs[['created_at', 'job_type', 'target_model', 'source_name', '执行状态', 'total_count', 'success_count', 'fail_count', 'operator']],
            width="stretch",
            hide_index=True,
            column_config={
                "created_at": "执行时间",
                "job_type": "任务类型",
                "target_model": "目标模块",
                "source_name": "来源/文件",
                "total_count": "总条数",
                "success_count": "成功条数",
                "fail_count": "失败条数",
                "operator": "触发人"
            }
        )
        
        # 报错详情诊断
        failed_jobs = df_jobs[df_jobs['fail_count'] > 0]
        if not failed_jobs.empty:
            st.markdown("##### 🚨 失败任务诊断 (Traceback)")
            err_sel = st.selectbox("选择出现失败的任务流水号 (ID)", failed_jobs['id'].tolist())
            err_json = failed_jobs[failed_jobs['id'] == err_sel].iloc[0]['error_details']
            try:
                st.json(json.loads(err_json))
            except:
                st.write(err_json)
    else:
        st.info("暂无后台任务执行记录。")

debug_kit.execute_debug_logic()
```

#### 📄 99_🧪_实验室.py

```python
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
```

#### 📄 export_to_md.py

```python
import os
from pathlib import Path

def generate_tree(dir_path, ignore_dirs, file_extensions, prefix=""):
    """
    递归生成纯文本的目录树字符串
    """
    tree_str = ""
    try:
        items = os.listdir(dir_path)
    except PermissionError:
        return tree_str

    # 过滤并排序文件夹和文件
    dirs = sorted([d for d in items if os.path.isdir(os.path.join(dir_path, d)) and d not in ignore_dirs])
    files = sorted([f for f in items if os.path.isfile(os.path.join(dir_path, f)) and Path(f).suffix in file_extensions])

    entries = dirs + files
    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{entry}\n"

        # 如果是文件夹，继续递归
        if entry in dirs:
            extension = "    " if is_last else "│   "
            tree_str += generate_tree(os.path.join(dir_path, entry), ignore_dirs, file_extensions, prefix + extension)
            
    return tree_str

def export_project_to_markdown(project_dir, output_file, ignore_dirs=None, file_extensions=None):
    """
    将项目导出为包含目录树和代码块的 Markdown 文件。
    """
    if ignore_dirs is None:
        # 默认过滤掉常见的无关文件夹
        ignore_dirs = {'.git', '__pycache__', 'venv', 'env', '.idea', '.vscode', 'node_modules', '__MACOSX'}
    
    if file_extensions is None:
        file_extensions = {'.py'}

    project_path = Path(project_dir).resolve()

    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write(f"# 项目: {project_path.name}\n\n")

        # --- 第一部分：生成并写入目录树概览 ---
        md_file.write("## 🗂️ 项目目录树\n\n```text\n")
        md_file.write(f"{project_path.name}/\n")
        tree_content = generate_tree(project_path, ignore_dirs, file_extensions)
        md_file.write(tree_content)
        md_file.write("```\n\n---\n\n")
        
        # --- 第二部分：遍历并写入代码内容 ---
        md_file.write("## 💻 代码详情\n\n")
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            dirs.sort()
            files.sort()

            current_path = Path(root)
            try:
                relative_path = current_path.relative_to(project_path)
            except ValueError:
                continue

            # 目录标题
            if relative_path.parts:
                depth = len(relative_path.parts)
                # 基础层级从 H3 开始，因为 H2 被用作大板块划分
                dir_heading = "#" * (depth + 2) 
                md_file.write(f"{dir_heading} 📁 {relative_path.name}\n\n")
            else:
                depth = 0

            # 文件标题与代码块
            for file in files:
                file_path = current_path / file
                if file_path.suffix in file_extensions:
                    file_heading = "#" * (depth + 3)
                    md_file.write(f"{file_heading} 📄 {file}\n\n")
                    
                    md_file.write("```python\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            md_file.write(f.read())
                    except Exception as e:
                        md_file.write(f"# 读取文件失败: {e}\n")
                    
                    if not md_file.tell() == 0:
                        md_file.write("\n")
                    md_file.write("```\n\n")

if __name__ == "__main__":
    # 1. 获取当前脚本的绝对路径的父目录 (即 tests/ 目录)
    current_script_dir = Path(__file__).resolve().parent
    
    # 2. 定位到上一级目录 (即 项目根目录)
    PROJECT_DIRECTORY = current_script_dir.parent
    
    # 3. 设置输出文件路径 (这里将其保存在项目根目录下)
    OUTPUT_MARKDOWN_FILE = PROJECT_DIRECTORY / "project_code_context.md"
    
    print(f"开始整理目录: {PROJECT_DIRECTORY}")
    export_project_to_markdown(PROJECT_DIRECTORY, OUTPUT_MARKDOWN_FILE)
    print(f"✅ 整理完成！请查看文件: {OUTPUT_MARKDOWN_FILE}")
```

