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
from backend.services.ai_service import extract_contract_elements

import sidebar_manager
import debug_kit 
import components as ui

FORM_HIDDEN_FIELDS = [] 

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
@st.cache_data(ttl=5, show_spinner=False)
def load_main_contracts(trigger):
    return db.fetch_dynamic_records('main_contract')

# 🟢 新增：拉取往来单位库的公司名称
@st.cache_data(ttl=5, show_spinner=False)
def load_enterprise_names(trigger):
    df_ent = db.fetch_dynamic_records('enterprise')
    if df_ent.empty:
        return [""]
    # 提取 company_name 列并去重，最前面加一个空选项
    return [""] + df_ent['company_name'].dropna().unique().tolist()
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
                ai_results = extract_contract_elements(uploaded_files[0],"main_contract")
                
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
    # =========================================================
    # 🛡️ 新增：数据清洗防弹衣（消除 Pandas NaN 和 AI 数据错乱引发的崩溃）
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
                field_meta.get(k, {}).get("readonly") or 
                field_meta.get(k, {}).get("is_virtual")
            )
            
            # 如果它注定要进 text_input，且它现在不是字符串，强制转换！
            if is_forced_text and not isinstance(v, str):
                current_data[k] = str(v)
    # =========================================================
        
    ent_names = load_enterprise_names(st.session_state.refresh_trigger)
    my_options = {
        "client_name": ent_names  # 将甲方单位字段变为下拉框
    }
    
    # 3. 渲染出高级表单
    result = ui.render_dynamic_form(
        "main_contract", 
        form_title, 
        current_data, 
        hidden_fields=FORM_HIDDEN_FIELDS,
        dynamic_options=my_options  # 👈 魔法注入：让 client_name 变成可搜索下拉框
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