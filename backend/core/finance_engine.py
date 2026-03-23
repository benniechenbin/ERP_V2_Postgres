import pandas as pd
import psycopg2.extras
from backend.database.db_engine import get_connection
from backend.utils.logger import sys_logger 

# ==========================================
# ⚙️ 引擎一：主合同水池核算
# ==========================================
def enrich_main_contract_stats(df_main: pd.DataFrame) -> pd.DataFrame:
    if df_main.empty or 'biz_code' not in df_main.columns:
        return df_main
        
    conn = get_connection()
    try:
        df_main['biz_code'] = df_main['biz_code'].astype(str).str.strip()
        biz_codes = df_main['biz_code'].tolist()
        params = tuple(biz_codes)
        placeholders = ', '.join(['%s'] * len(biz_codes))

        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        sql_inv = f"""
            SELECT main_contract_code as biz_code, SUM(invoice_amount) as total_invoiced
            FROM biz_invoices 
            WHERE main_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY main_contract_code
        """
        cur.execute(sql_inv, params)
        df_inv = pd.DataFrame(cur.fetchall())
        if not df_inv.empty:
            df_inv['total_invoiced'] = df_inv['total_invoiced'].astype(float)
            df_inv['biz_code'] = df_inv['biz_code'].astype(str).str.strip()

        sql_coll = f"""
            SELECT main_contract_code as biz_code, SUM(collected_amount) as total_collected
            FROM biz_collections
            WHERE main_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY main_contract_code
        """
        cur.execute(sql_coll, params)
        df_coll = pd.DataFrame(cur.fetchall())
        if not df_coll.empty:
            df_coll['total_collected'] = df_coll['total_collected'].astype(float)
            df_coll['biz_code'] = df_coll['biz_code'].astype(str).str.strip()

        v_cols = ['total_invoiced', 'total_collected']
        df_main = df_main.drop(columns=[c for c in v_cols if c in df_main.columns])

        if not df_inv.empty: df_main = df_main.merge(df_inv, on='biz_code', how='left')
        else: df_main['total_invoiced'] = 0.0

        if not df_coll.empty: df_main = df_main.merge(df_coll, on='biz_code', how='left')
        else: df_main['total_collected'] = 0.0

        return df_main.fillna({'total_invoiced': 0.0, 'total_collected': 0.0})
    finally:
        if conn: conn.close()

# ==========================================
# ⚙️ 引擎二：分包合同核算 (🟢 新增：动态应付金额)
# ==========================================
def enrich_sub_contract_stats(df_sub: pd.DataFrame) -> pd.DataFrame:
    if df_sub.empty or 'biz_code' not in df_sub.columns:
        return df_sub

    conn = get_connection()
    try:
        df_sub['biz_code'] = df_sub['biz_code'].astype(str).str.strip()
        df_sub['actual_main_code'] = df_sub['actual_main_code'].astype(str).str.strip()
        sub_codes = df_sub['biz_code'].tolist()
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        placeholders = ', '.join(['%s'] * len(sub_codes))
        params = tuple(sub_codes)

        sql_pay = f"""
            SELECT sub_contract_code as biz_code, SUM(payment_amount) as total_paid
            FROM biz_outbound_payments
            WHERE sub_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY sub_contract_code
        """
        cur.execute(sql_pay, params)
        df_pay = pd.DataFrame(cur.fetchall())
        if not df_pay.empty:
            df_pay['total_paid'] = df_pay['total_paid'].astype(float)
            df_pay['biz_code'] = df_pay['biz_code'].astype(str).str.strip()

        sql_inv = f"""
            SELECT sub_contract_code as biz_code, SUM(invoice_amount) as total_invoiced_from_sub
            FROM biz_sub_invoices
            WHERE sub_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY sub_contract_code
        """
        cur.execute(sql_inv, params)
        df_inv = pd.DataFrame(cur.fetchall())
        if not df_inv.empty:
            df_inv['total_invoiced_from_sub'] = df_inv['total_invoiced_from_sub'].astype(float)
            df_inv['biz_code'] = df_inv['biz_code'].astype(str).str.strip()

        main_codes = [c for c in df_sub['actual_main_code'].unique().tolist() if c and str(c) != 'nan']
        df_main_data = pd.DataFrame()
        if main_codes:
            m_placeholders = ', '.join(['%s'] * len(main_codes))
            sql_main = f"""
                SELECT m.biz_code as actual_main_code, m.contract_amount as main_contract_amount, 
                       COALESCE(SUM(c.collected_amount), 0) as main_total_collected
                FROM biz_main_contracts m
                LEFT JOIN biz_collections c ON m.biz_code = c.main_contract_code AND c.deleted_at IS NULL
                WHERE m.biz_code IN ({m_placeholders}) AND m.deleted_at IS NULL
                GROUP BY m.biz_code, m.contract_amount
            """
            cur.execute(sql_main, tuple(main_codes))
            df_main_data = pd.DataFrame(cur.fetchall())
            if not df_main_data.empty:
                df_main_data[['main_contract_amount', 'main_total_collected']] = df_main_data[['main_contract_amount', 'main_total_collected']].astype(float)
                df_main_data['actual_main_code'] = df_main_data['actual_main_code'].astype(str).str.strip()

        v_cols = ['total_paid', 'total_invoiced_from_sub', 'main_contract_amount', 'main_total_collected']
        df_sub = df_sub.drop(columns=[c for c in v_cols if c in df_sub.columns])

        if not df_pay.empty: df_sub = df_sub.merge(df_pay, on='biz_code', how='left')
        if not df_inv.empty: df_sub = df_sub.merge(df_inv, on='biz_code', how='left')
        if not df_main_data.empty: df_sub = df_sub.merge(df_main_data, on='actual_main_code', how='left')

        for c in v_cols:
            if c not in df_sub.columns: df_sub[c] = 0.0
            
        df_sub = df_sub.fillna({c: 0.0 for c in v_cols})
        
        # 🟢 核心新增：动态推演本期应付金额
        def calc_payable(row):
            sub_amt = float(row.get('sub_amount', 0))
            paid = float(row.get('total_paid', 0))
            m_amt = float(row.get('main_contract_amount', 0))
            m_coll = float(row.get('main_total_collected', 0))
            is_b2b = str(row.get('is_back_to_back', '')).strip() in ['是', 'True', '1']
            
            if is_b2b and m_amt > 0:
                # 只有背靠背才受主合同收款率压制
                main_ratio = m_coll / m_amt
                target_payable = sub_amt * main_ratio
                payable = target_payable - paid
            else:
                # 非背靠背，理论上随时都可以付满 (扣除已付)
                payable = sub_amt - paid
                
            return max(0.0, payable) # 防止超付时出现负数
            
        df_sub['current_payable'] = df_sub.apply(calc_payable, axis=1)

        return df_sub
    finally:
        if conn: conn.close()

# ==========================================
# ⚙️ 引擎三：名义关联 (EBM) 资金红线拦截器
# ==========================================
# 🟢 修复了 conn=None 默认参数，使其可被外部事务正常调用
def validate_sub_payment_risk(sub_biz_code: str, apply_amount: float, conn=None) -> tuple[bool, str]:
    sys_logger.info(f"🛡️ --- 风控雷达启动: 目标分包 [{sub_biz_code}] ---")
    is_external_conn = conn is not None
    if not is_external_conn:
        conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT * FROM biz_sub_contracts WHERE biz_code = %s AND deleted_at IS NULL FOR UPDATE", (sub_biz_code,))
        sub_raw = cur.fetchone()
        
        if not sub_raw:
            return True, "数据库查无此分包，系统放行"
            
        # 🟢 新增逻辑：只有背靠背合同才拦截，非背靠背随便付
        is_b2b = str(sub_raw.get('is_back_to_back', '')).strip() in ['是', 'True', '1']
        if not is_b2b:
            sys_logger.info("  [放行] 非背靠背合同，无需校验主合同收款比例。")
            return True, "非背靠背合同，风控放行"
            
        # 优先取实际关联，再取账面关联
        ebm_code = sub_raw.get('book_main_code') or sub_raw.get('actual_main_code')
        
        if not ebm_code:
            return True, "无主合同关联，不在风控管辖内，放行"
            
        ebm_code = ebm_code.strip()
        sub_total = float(sub_raw.get('sub_amount') or 0)
        
        cur.execute('SELECT SUM(payment_amount) as paid FROM biz_outbound_payments WHERE sub_contract_code = %s AND deleted_at IS NULL', (sub_biz_code,))
        already_paid = float(cur.fetchone()['paid'] or 0)
        future_ratio = (already_paid + float(apply_amount)) / sub_total if sub_total > 0 else 0
        
        cur.execute("SELECT * FROM biz_main_contracts WHERE biz_code = %s AND deleted_at IS NULL", (ebm_code,))
        main_raw = cur.fetchone()
        
        if not main_raw:
            return True, "归属的账面主合同不存在，强制放行"
            
        main_total = float(main_raw.get('contract_amount') or 0)
        cur.execute('SELECT SUM(collected_amount) as coll FROM biz_collections WHERE main_contract_code = %s AND deleted_at IS NULL', (ebm_code,))
        main_coll = float(cur.fetchone()['coll'] or 0)
        main_ratio = main_coll / main_total if main_total > 0 else 0
        
        # 决断 (增加 0.1% 的浮点数容错率)
        if future_ratio > (main_ratio + 0.001):
            return False, f"🔴 安全拦截：背靠背条款限制！主合同当前收款率仅 {main_ratio:.1%}，本次付款将使分包支付率达 {future_ratio:.1%}，突破红线！"
            
        return True, "风控测算通过，允许付款"
        
    except Exception as e:
        sys_logger.error(f"  [异常] 风控引擎崩溃: {e}", exc_info=True)
        return False, f"风控异常: {e}"
    finally:
        if not is_external_conn and conn: 
            conn.close()