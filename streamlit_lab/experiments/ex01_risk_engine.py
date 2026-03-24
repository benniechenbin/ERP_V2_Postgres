import streamlit as st
import pandas as pd
import backend.config.config_manager as cfg

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
