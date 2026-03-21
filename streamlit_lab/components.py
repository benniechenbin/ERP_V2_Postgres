# ==========================================
# 🎨 Streamlit UI 小组件 (偷懒神器)
# ==========================================
import streamlit as st
import pandas as pd
from datetime import datetime

from backend.config import config_manager as cfg
from backend.database.crud import fetch_dynamic_records# 假设您的 CRUD 有这个基础查询方法

def render_smart_widget(col_name, label, val, col_type, config_type, is_disabled, field_meta):
    """
    [智能 UI 组件渲染工厂] 根据字段类型，自动生成对应的 Streamlit 输入框，并返回用户输入的值。
    """
    # 1. 提取额外配置
    options = field_meta.get("options", [])
    default_val = field_meta.get("default", None)
    step_val = field_meta.get("step", 1000.0)
    min_val = field_meta.get("min_value", None)
    max_val = field_meta.get("max_value", None)

    # 2. 初始默认值处理（处理新增模式下 val 为空的情况）
    if val is None and default_val is not None:
        val = default_val

    # ================= 渲染核心逻辑 =================
    
    # 类型 A：下拉选择框
    if config_type == "select" and options:
        try:
            idx = options.index(val) if val in options else 0
        except ValueError:
            idx = 0
        if "市场系数" in label or "比例" in label or "率" in label:
            return st.selectbox(
                label, 
                options=options, 
                index=idx, 
                disabled=is_disabled, 
                key=f"input_{col_name}",
                format_func=lambda x: f"{x * 100:g}%" if isinstance(x, (int, float)) else str(x)
            )
        else:
            # 普通的下拉框
            return st.selectbox(label, options=options, index=idx, disabled=is_disabled, key=f"input_{col_name}")

    # 类型 B：开关 Toggle (专供 is_active 使用)
    elif col_name == 'is_active':
        return st.toggle(label, value=bool(val) if val is not None else True, key=f"input_{col_name}")

    # 类型 C：日期选择器 (小日历)
    elif config_type == "date":
        if pd.isna(val) or val is None or str(val).strip() == "":
            default_date = datetime.today().date()
        else:
            try:
                default_date = pd.to_datetime(val).date()
            except:
                default_date = datetime.today().date()
                
        selected_date = st.date_input(label, value=default_date, disabled=is_disabled, key=f"input_{col_name}")
        return str(selected_date) # 转回纯字符串格式迎合数据库
      
    # 类型 D：数字/百分比输入框
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
        
        # 🟢 终极防御：强行限制默认值在合法范围内，防止脏数据导致 Streamlit 崩溃！
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
            
    # 类型 E：默认文本输入框 (兜底)
    else:
        default_str = str(val) if val is not None else ""
        return st.text_input(label, value=default_str, disabled=is_disabled, key=f"input_{col_name}")

def show_toast_success(msg):
    """封装一个统一风格的成功提示"""
    st.toast(f"✅ {msg}", icon="🎉")

def show_toast_error(msg):
    """封装一个统一风格的错误提示"""
    st.toast(f"❌ {msg}", icon="😱")

def style_metric_card():
    """
    (进阶) 给 st.metric 加一点 CSS 样式，让卡片带阴影。
    只需要在页面开头调用一次 utils.style_metric_card()
    """
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
    """
    [通用 UI 工具] 高阶函数：生成一个去除指定前缀的格式化函数。
    极度适合用于 Streamlit 的 format_func。
    
    原理：传入你需要剔除的前缀（如 "data_" 或 "sys_"），
    它会返回一个专门处理该前缀的函数给 selectbox 用。
    """
    def formatter(item):
        if isinstance(item, str) and item.startswith(prefix):
            # 使用字符串切片 [len(prefix):] 比 replace 更安全
            # 因为它只切除开头的对应字符，即使后面内容包含该前缀也不会误伤
            return item[len(prefix):]
        return item
    
    return formatter


def dict_mapping_formatter(mapping_dict: dict):
    """
    [通用 UI 工具] 高阶函数：生成一个基于字典映射的格式化函数。
    常用于把底层的英文 key 翻译成前端漂亮的中文展示。
    """
    def formatter(item):
        # 如果字典里有，就用字典里的漂亮名字；如果没有，就保持原样
        return mapping_dict.get(item, item)
    
    return formatter

# ==========================================
# 🚀 V2.0 宏观 UI 渲染引擎 (缺口 4 补齐)
# ==========================================
def render_dynamic_form(model_name: str, form_title: str, existing_data: dict = None, hidden_fields: list = None, readonly_fields: list = None):
    """
    [宏观组件 2：动态输入表单 - V2 三列增强版]
    极其强悍的表单生成器！自动根据 JSON 生成一整套输入框，并支持通过常量列表覆写字段属性。
    """
    field_meta = cfg.get_field_meta(model_name)
    if not field_meta:
        st.error(f"❌ 找不到模型 {model_name} 的配置")
        return None
        
    st.subheader(form_title)
    form_data = {}
    existing_data = existing_data or {}
    
    # 🟢 接收常量控制列表 (默认为空)
    hidden_fields = hidden_fields or []
    readonly_fields = readonly_fields or []
    
    # 🟢 核心过滤：剔除虚拟列，并且剔除掉业务强行要求隐藏的列 (HIDDEN)
    editable_fields = {
        k: v for k, v in field_meta.items() 
        if not v.get("is_virtual", False) and k not in hidden_fields
    }
    
    # 开启表单域
    with st.form(key=f"form_{model_name}"):
        # 🟢 进化为三列排版，极大提升屏幕空间利用率
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        
        for idx, (field_key, meta) in enumerate(editable_fields.items()):
            label = meta.get("label", field_key)
            col_type = meta.get("type", "text")
            val = existing_data.get(field_key, None)
            
            # 🟢 动态只读控制：取 JSON 底层配置 和 前端强行 READONLY 的并集
            is_readonly = meta.get("readonly", False) or (field_key in readonly_fields)
            
            config_type = meta.get("type", "text")
            pseudo_col_type = "DECIMAL" if config_type in ["money", "percent", "number"] else "VARCHAR"
            
            # 配合三列取余数
            with cols[idx % 3]:
                user_input = render_smart_widget(
                    col_name=field_key,
                    label=label,
                    val=val,
                    col_type=pseudo_col_type,
                    config_type=config_type,
                    is_disabled=is_readonly,
                    field_meta=meta
                )
                form_data[field_key] = user_input
                
        # 提交按钮单独占满一行
        submit_btn = st.form_submit_button("💾 保存提交", use_container_width=True)
        
        if submit_btn:
            return form_data
    return None


def render_audit_timeline(biz_code: str, model_name: str = None):
    """
    [通用审计组件：时光机]
    传入 biz_code，自动展示该对象的完整生命周期。
    """
    from backend.database.db_engine import get_connection
    import json
    
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