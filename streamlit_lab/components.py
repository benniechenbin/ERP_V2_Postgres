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