# 文件位置: backend/services/analysis_service.py
import pandas as pd
from datetime import datetime
import json
from backend.database.db_engine import get_connection
from backend.utils.logger import sys_logger

# =========================================================
# 💰 引擎一：全局双向现金流趋势 (Cash Flow Trend)
# =========================================================
def get_cash_flow_trend(year: int = None) -> pd.DataFrame:
    """统合 biz_collections (流入) 和 biz_outbound_payments (流出)"""
    conn = get_connection()
    try:
        sql_in = """
            SELECT TO_CHAR(collected_date, 'YYYY-MM') as month, 
                   SUM(collected_amount) as inflow
            FROM biz_collections 
            WHERE deleted_at IS NULL
            GROUP BY TO_CHAR(collected_date, 'YYYY-MM')
        """
        df_in = pd.read_sql_query(sql_in, conn)
        
        sql_out = """
            SELECT TO_CHAR(payment_date, 'YYYY-MM') as month, 
                   SUM(payment_amount) as outflow
            FROM biz_outbound_payments 
            WHERE deleted_at IS NULL
            GROUP BY TO_CHAR(payment_date, 'YYYY-MM')
        """
        df_out = pd.read_sql_query(sql_out, conn)
        
        if df_in.empty and df_out.empty:
            return pd.DataFrame(columns=['month', 'inflow', 'outflow', 'net_flow'])
            
        df_trend = pd.merge(df_in, df_out, on='month', how='outer').fillna(0.0)
        
        if year:
            df_trend = df_trend[df_trend['month'].str.startswith(str(year))]
            
        df_trend['net_flow'] = df_trend['inflow'] - df_trend['outflow']
        df_trend = df_trend.sort_values('month').reset_index(drop=True)
        
        return df_trend
    except Exception as e:
        sys_logger.error(f"🚨 现金流趋势测算失败: {e}", exc_info=True)
        return pd.DataFrame()
    finally:
        if conn: conn.close()

# =========================================================
# 📈 引擎二：宏观业财剪刀差 (Gross Margin Analysis)
# =========================================================
def calculate_overall_margin() -> dict:
    """计算全盘的账面预估毛利"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(contract_amount::numeric), 0) FROM biz_main_contracts WHERE deleted_at IS NULL")
        total_income = float(cur.fetchone()[0])
        
        cur.execute("SELECT COALESCE(SUM(sub_amount::numeric), 0) FROM biz_sub_contracts WHERE deleted_at IS NULL")
        total_cost = float(cur.fetchone()[0])
        
        gross_profit = total_income - total_cost
        margin_rate = (gross_profit / total_income * 100) if total_income > 0 else 0.0
        
        return {
            "total_income": total_income,
            "total_cost": total_cost,
            "gross_profit": gross_profit,
            "margin_rate": margin_rate
        }
    except Exception as e:
        sys_logger.error(f"🚨 业财剪刀差测算失败: {e}", exc_info=True)
        return {"total_income": 0, "total_cost": 0, "gross_profit": 0, "margin_rate": 0}
    finally:
        if conn: conn.close()

# =========================================================
# 🧾 引擎三：发票与税务敞口分析 (Tax Exposure)
# =========================================================
def get_tax_exposure_stats() -> dict:
    """分为收入侧(应交未交)和支出侧(应抵未抵)"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(collected_amount), 0) FROM biz_collections WHERE deleted_at IS NULL")
        main_coll = float(cur.fetchone()[0])
        cur.execute("SELECT COALESCE(SUM(invoice_amount), 0) FROM biz_invoices WHERE deleted_at IS NULL")
        main_inv = float(cur.fetchone()[0])
        
        cur.execute("SELECT COALESCE(SUM(payment_amount), 0) FROM biz_outbound_payments WHERE deleted_at IS NULL")
        sub_pay = float(cur.fetchone()[0])
        cur.execute("SELECT COALESCE(SUM(invoice_amount), 0) FROM biz_sub_invoices WHERE deleted_at IS NULL")
        sub_inv_rec = float(cur.fetchone()[0])
        
        return {
            "main_collected": main_coll,
            "main_invoiced": main_inv,
            "main_exposure": max(0, main_coll - main_inv), 
            "sub_paid": sub_pay,
            "sub_invoiced_received": sub_inv_rec,
            "sub_exposure": max(0, sub_pay - sub_inv_rec)  
        }
    except Exception as e:
        sys_logger.error(f"🚨 税务敞口测算失败: {e}", exc_info=True)
        return {}
    finally:
        if conn: conn.close()

# =========================================================
# 👤 引擎四：组织/人员绩效聚合 (Performance Aggregation)
# =========================================================
def get_manager_performance(year: int = None) -> pd.DataFrame:
    """按负责人分组统计业绩"""
    conn = get_connection()
    try:
        sql = """
            SELECT 
                COALESCE(manager, '未分配') as manager_name,
                SUM(contract_amount::numeric) as total_contract,
                SUM(total_collected::numeric) as total_collected
            FROM biz_main_contracts
            WHERE deleted_at IS NULL
        """
        if year:
            sql += f" AND EXTRACT(YEAR FROM sign_date) = {year}"
            
        sql += " GROUP BY COALESCE(manager, '未分配') ORDER BY total_contract DESC"
        
        df = pd.read_sql_query(sql, conn)
        df['total_contract'] = df['total_contract'].astype(float)
        df['total_collected'] = df['total_collected'].astype(float)
        return df
    except Exception as e:
        sys_logger.error(f"🚨 绩效聚合失败: {e}", exc_info=True)
        return pd.DataFrame()
    finally:
        if conn: conn.close()

# =========================================================
# 💀 引擎五：高危欠款大户侦测 (High Risk Detection - 智能账龄版)
# =========================================================
def get_high_risk_projects(debt_threshold=100000, rate_threshold=0.2, grace_days=180) -> pd.DataFrame:
    """
    侦测高危主合同 (V2.1 智能升级版)
    屏蔽新签合同悖论，仅侦测：欠款 > 阈值 且 欠款比例 > 比例 且 签约时间 > 宽限期(默认半年)
    """
    from backend.database.db_engine import get_connection
    from backend.utils.logger import sys_logger
    import pandas as pd
    
    conn = get_connection()
    try:
        # 🟢 顺手把项目阶段 (project_stage) 也查出来，方便前端做更深度的警示
        sql = """
            SELECT 
                biz_code, project_name, manager, sign_date, project_stage,
                contract_amount::numeric as contract_amount,
                total_collected::numeric as total_collected,
                uncollected_contract_amount::numeric as uncollected
            FROM biz_main_contracts
            WHERE deleted_at IS NULL 
              AND contract_amount::numeric > 0
        """
        df = pd.read_sql_query(sql, conn)
        if df.empty: return df
        
        # 1. 基础数据类型转换
        for col in ['contract_amount', 'total_collected', 'uncollected']:
            df[col] = df[col].astype(float)
            
        df['uncollected_rate'] = df['uncollected'] / df['contract_amount']
        
        # 2. 🟢 核心账龄计算 (防空指针处理)
        df['sign_date'] = pd.to_datetime(df['sign_date'], errors='coerce')
        # 计算至今已签约天数
        df['days_since_sign'] = (pd.Timestamp.now().normalize() - df['sign_date']).dt.days
        # 如果有些老数据没填签约日期，保守起见默认算作老项目 (赋予一个极大的天数)
        df['days_since_sign'] = df['days_since_sign'].fillna(9999) 
        
        # 3. 三重拦截网：金额 + 比例 + 宽限期
        mask = (
            (df['uncollected'] > debt_threshold) & 
            (df['uncollected_rate'] > rate_threshold) &
            (df['days_since_sign'] > grace_days) # 🛡️ 这一刀直接砍掉了所有新签合同的误报
        )
        
        df_risk = df[mask].sort_values('uncollected', ascending=False)
        return df_risk
        
    except Exception as e:
        sys_logger.error(f"🚨 风险侦测失败: {e}", exc_info=True)
        return pd.DataFrame()
    finally:
        if conn: conn.close()

# =========================================================
# ✂️ 引擎六：通用时间切片器 (Time-Slicing)
# =========================================================
def split_by_period(df: pd.DataFrame, date_col: str, target_year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """返回: (df_new 本年新增, df_carry 往年存量)"""
    if df.empty or date_col not in df.columns:
        return df, pd.DataFrame(columns=df.columns)
        
    df_copy = df.copy()
    df_copy['__year__'] = pd.to_datetime(df_copy[date_col], errors='coerce').dt.year
    
    df_new = df_copy[df_copy['__year__'] == target_year].drop(columns=['__year__'])
    df_carry = df_copy[df_copy['__year__'] < target_year].drop(columns=['__year__'])
    
    return df_new, df_carry

# =========================================================
# 📅 引擎七 (预埋件)：项目进度与甘特图引擎 (Project Management)
# 作用：处理 JSONB 动态扩展字段，生成标准甘特图结构
# =========================================================
def _flatten_extra_props(df: pd.DataFrame) -> pd.DataFrame:
    """
    [核心机制] PostgreSQL JSONB 展平器
    如果 DataFrame 中存在 extra_props (字典形式)，将其键值对展开为独立的列。
    这样计算引擎就能拿到那些没有被固化为物理列的字段（如进度、起止日期）。
    """
    if 'extra_props' in df.columns:
        # 将字典列展开为一个新的 DataFrame
        # 注意：如果有缺失值，需要用空字典填补，防止 apply 报错
        props_df = df['extra_props'].apply(
            lambda x: x if isinstance(x, dict) else (json.loads(x) if isinstance(x, str) else {})
        ).apply(pd.Series)
        
        # 将展开的列合并回主表 (如果列名重复，保留物理列)
        for col in props_df.columns:
            if col not in df.columns:
                df[col] = props_df[col]
    return df

def prepare_gantt_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    [计算引擎] 准备甘特图所需的数据结构
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df_copy = _flatten_extra_props(df.copy()) # 🟢 展开 JSONB
    
    if 'start_date' not in df_copy.columns:
        current_year = datetime.now().year
        df_copy['start_date'] = pd.to_datetime(f"{current_year}-01-01")
    else:
        df_copy['start_date'] = pd.to_datetime(df_copy['start_date'], errors='coerce')

    if 'end_date' not in df_copy.columns:
        df_copy['end_date'] = df_copy['start_date'] + pd.Timedelta(days=90)
    else:
        df_copy['end_date'] = pd.to_datetime(df_copy['end_date'], errors='coerce')

    df_copy['start_date'] = df_copy['start_date'].fillna(pd.to_datetime(datetime.now()))
    df_copy['end_date'] = df_copy['end_date'].fillna(df_copy['start_date'] + pd.Timedelta(days=90))

    return df_copy

def generate_gantt_data(df: pd.DataFrame) -> list:
    """
    [前端适配器] 转化为甘特图标准 JSON
    """
    df_prepared = prepare_gantt_dataframe(df)
    
    if df_prepared.empty:
        return []

    gantt_list = []
    for _, row in df_prepared.iterrows():
        # 尝试获取进度和负责人
        progress_val = row.get('progress', row.get('进度', 0))
        try:
            progress_val = float(progress_val)
        except:
            progress_val = 0
            
        manager = row.get('manager', row.get('项目经理', row.get('负责人', '未分配')))

        gantt_list.append({
            "Task": row.get('project_name', row.get('项目名称', '未命名项目')),
            "Start": row['start_date'].strftime('%Y-%m-%d'),
            "Finish": row['end_date'].strftime('%Y-%m-%d'),
            "Resource": str(manager), 
            "Completion": progress_val * 100 if progress_val <= 1 else progress_val
        })
        
    return gantt_list