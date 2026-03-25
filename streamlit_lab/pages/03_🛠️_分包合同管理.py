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
from backend.services.ai_service import extract_contract_elements

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

if 'show_sub_contract_dialog' not in st.session_state:
    st.session_state.show_sub_contract_dialog = False
if 'current_sub_edit_data' not in st.session_state:
    st.session_state.current_sub_edit_data = None
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
    # 🟢 状态初始化：用于存放分包 AI 提取出的数据
    if "ai_sub_buffer" not in st.session_state:
        st.session_state.ai_sub_buffer = {}

    if ui and hasattr(ui, 'render_dynamic_form'):
        
        # 🟢 AI 占位符 (已打通真接口)
        st.subheader("🤖 AI 分包合同智能解析")
        uploaded_files = st.file_uploader("📂 请拖拽或选择待解析合同 (支持 PDF/Word)", accept_multiple_files=True, key="sub_uploader")
        c_cat, c_btn = st.columns([3, 1])
        with c_cat:
            file_category = st.selectbox(
                "🗂️ 附件类别", 
                ["分包合同正文 (需 AI 解析)", "工程量清单", "结算单", "其他附件"],
                label_visibility="collapsed",
                key="sub_category"
            )
        with c_btn:
            ai_ready = uploaded_files is not None and len(uploaded_files) > 0 and "(需 AI 解析)" in file_category
            if st.button("✨ 一键 AI 提取", type="primary", disabled=not ai_ready, use_container_width=True, key="sub_ai_btn"):
                with st.spinner("🧠 AI 正在极速阅读分包条款，请稍候..."):
                    # 🟢 呼叫通用 AI 接口
                    ai_results = extract_contract_elements(uploaded_files[0], "sub_contract")
                    
                    if ai_results:
                        field_meta = cfg.get_field_meta("sub_contract")
                        for k, v in ai_results.items():
                            if v is None or str(v).strip().lower() in ["", "null", "none"]: continue
                            
                            state_key = f"input_{k}"
                            f_type = field_meta.get(k, {}).get("type", "text")
                            try:
                                if f_type == "date":
                                    st.session_state[state_key] = datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
                                elif f_type in ["money", "number", "num", "percent"]:
                                    st.session_state[state_key] = float(v)
                                else:
                                    st.session_state[state_key] = str(v)
                            except Exception:
                                pass
                                
                        st.session_state.ai_sub_buffer = ai_results
                        st.success("🎉 AI 提取完毕！下方表单已自动填充。")
                        st.rerun()
                    else:
                        st.error("❌ 识别失败，未能提取出有效数据。")

        st.markdown("---") 

        is_edit = existing_data is not None
        form_title = "✏️ 修改分包合同" if is_edit else "🆕 录入新分包合同"
        current_data = existing_data.copy() if existing_data else {}
        if not is_edit:
            target_table = cfg.get_model_config("sub_contract").get("table_name", "biz_sub_contracts")
            current_data['biz_code'] = crud.generate_biz_code(target_table, prefix_char="SUB")
            
        # 融合 AI 提取的数据
        if st.session_state.get("ai_sub_buffer"):
            current_data.update(st.session_state.ai_sub_buffer)
        # =========================================================
        # 🛡️ 数据清洗防弹衣 2.0（终极进化版）
        # =========================================================
        field_meta = cfg.get_field_meta("sub_contract")
        for k, v in list(current_data.items()):
            if pd.isna(v): 
                current_data[k] = None  
            else:
                f_type = field_meta.get(k, {}).get("type", "text")
                
                # 🚨 破案关键：判断该字段是否会在底层被“降级”为 text_input 渲染
                is_forced_text = (
                    f_type in ["text", "select"] or 
                    k in FORM_READONLY_FIELDS or 
                    field_meta.get(k, {}).get("readonly") or 
                    field_meta.get(k, {}).get("is_virtual")
                )
                
                # 如果它注定要进 text_input，且它现在不是字符串，强制转换！
                if is_forced_text and not isinstance(v, str):
                    current_data[k] = str(v)
        # =========================================================   
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
                st.session_state.ai_sub_buffer = {} 
                st.session_state.show_sub_contract_dialog = False  
                
                ui.show_toast_success("分包数据保存成功！")
                trigger_refresh() 
                st.rerun()
            else:
                ui.show_toast_error(f"保存失败: {msg}")       

# ==========================================
# 3. 📊 顶层：防失血 KPI 预警看板
# ==========================================
if st.session_state.show_sub_contract_dialog:
    sub_contract_form_dialog(st.session_state.current_sub_edit_data)
col_title, col_add_btn = st.columns([8, 2])
with col_title:
    st.title("🛡️ 分包支出与税务防线")
with col_add_btn:
    st.write("") 
    if st.button("➕ 录入新分包合同", type="primary", use_container_width=True):
        st.session_state.show_sub_contract_dialog = True
        st.session_state.current_sub_edit_data = None
        st.rerun()

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
                st.session_state.show_sub_contract_dialog = True
                st.session_state.current_sub_edit_data = current_contract_data
                st.rerun()

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