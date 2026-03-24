# 文件位置: tests/generate_mock_data.py
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# 🟢 寻路魔法：确保能找到 backend 模块
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.db_engine import get_connection
from backend.database import crud_base, crud_finance

# --- 逼真的业务字典 ---
CITIES = ["上海", "北京", "深圳", "广州", "杭州", "成都", "武汉", "苏州", "南京", "重庆"]
PROJECT_TYPES = ["商业综合体", "研发中心", "智慧产业园", "高端住宅", "市政道路", "医院扩建", "学校新校区", "仓储物流园", "数据中心", "文旅小镇"]
CLIENTS = ["万科地产", "华润置地", "保利发展", "中海地产", "龙湖集团", "招商蛇口", "融创中国", "绿城中国", "中国建筑", "地方城投"]
MANAGERS = ["张建国", "李志强", "王海涛", "赵宇", "刘洋", "陈斌", "杨百万", "周铁柱"]
SUB_COMPANIES = ["中建一局", "中铁十四局", "上海建工", "江苏中南", "浙江大地", "中建八局", "远大园林", "宏伟机电", "东方防水", "雷霆安防"]
STAGES = ["概念方案", "招投标", "施工准备", "主体施工", "竣工验收", "结算审计", "已结项"]

def random_date(start_year=2024, end_year=2026):
    """生成随机日期"""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31) if end_year < 2026 else datetime.now()
    return start + timedelta(days=random.randint(0, (end - start).days))

def clear_all_data():
    """核弹级清理：清空所有业务表，重置自增 ID"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        tables = [
            "biz_main_contracts", "biz_sub_contracts", "biz_payment_plans", 
            "biz_collections", "biz_invoices", "biz_outbound_payments", "biz_sub_invoices",
            "sys_audit_logs", "sys_attachments"
        ]
        for t in tables:
            cur.execute(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE;")
        conn.commit()
        print("🧹 已清空所有历史业务数据！")
    finally:
        conn.close()

def generate_data():
    clear_all_data()
    print("🚀 开始生成高仿真业务数据...")

    main_codes = []
    
    # ==========================================
    # 1. 自动生成 20 个主合同
    # ==========================================
    print("🏗️ 正在生成主合同...")
    for i in range(1, 21):
        biz_code = f"MAIN-2025-{i:03d}"
        main_codes.append(biz_code)
        amount = random.randint(100, 5000) * 10000  # 100万 到 5000万
        
        crud_base.upsert_dynamic_record("main_contract", {
            "biz_code": biz_code,
            "project_name": f"{random.choice(CITIES)}{random.choice(PROJECT_TYPES)}项目",
            "client_name": random.choice(CLIENTS),
            "manager": random.choice(MANAGERS),
            "contract_amount": amount,
            "sign_date": random_date().strftime("%Y-%m-%d"),
            "project_stage": random.choice(STAGES),
            "is_provisioned": "否"
        }, operator_name="System_Mock")

    # ==========================================
    # 2. 为主合同生成收款计划与资金流水
    # ==========================================
    print("💰 正在生成收款计划与甲方流水...")
    conn = get_connection()
    try:
        cur = conn.cursor()
        for m_code in main_codes:
            # 查出这个主合同的金额
            cur.execute("SELECT contract_amount FROM biz_main_contracts WHERE biz_code = %s", (m_code,))
            m_amount = float(cur.fetchone()[0])
            
            # 生成 3 期收款计划
            ratios = [30, 50, 20]
            stages = ["预付款", "进度款", "结算尾款"]
            for idx, ratio in enumerate(ratios):
                plan_amt = m_amount * (ratio / 100.0)
                # 特意制造一些即将逾期的计划 (点亮大屏红灯)
                p_date = (datetime.now() + timedelta(days=random.randint(-15, 45))).strftime("%Y-%m-%d")
                cur.execute("""
                    INSERT INTO biz_payment_plans (biz_code, main_contract_code, milestone_name, payment_ratio, planned_amount, planned_date, operator)
                    VALUES (%s, %s, %s, %s, %s, %s, 'Mock')
                """, (f"PLAN-{m_code}-{idx}", m_code, stages[idx], ratio, plan_amt, p_date))

            # 随机生成收款流水 (有的大户全收齐，有的严重欠款)
            coll_ratio = random.choice([0, 0.3, 0.8, 1.0]) 
            if coll_ratio > 0:
                coll_amt = m_amount * coll_ratio
                cur.execute("""
                    INSERT INTO biz_collections (biz_code, main_contract_code, collected_amount, collected_date, operator)
                    VALUES (%s, %s, %s, %s, 'Mock')
                """, (f"COLL-{m_code}", m_code, coll_amt, random_date(2025, 2026).strftime("%Y-%m-%d")))
                
            # 随机开票 (制造未开票敞口)
            inv_amt = m_amount * random.choice([0, 0.3, 0.5])
            if inv_amt > 0:
                cur.execute("""
                    INSERT INTO biz_invoices (biz_code, main_contract_code, invoice_amount, invoice_date, operator)
                    VALUES (%s, %s, %s, %s, 'Mock')
                """, (f"INV-{m_code}", m_code, inv_amt, random_date(2025, 2026).strftime("%Y-%m-%d")))
                
            conn.commit()
            # 同步主合同财务数据
            from backend.database.crud_finance import sync_main_contract_finance
            sync_main_contract_finance(m_code)
            
    finally:
        conn.close()

    # ==========================================
    # 3. 自动生成 30 个分包合同及流水
    # ==========================================
    print("🛡️ 正在生成分包合同与流出资金...")
    conn = get_connection()
    try:
        cur = conn.cursor()
        for i in range(1, 31):
            sub_code = f"SUB-2025-{i:03d}"
            m_code = random.choice(main_codes) # 挂靠到随机的主合同
            
            # 分包金额通常是主合同的一小部分
            cur.execute("SELECT contract_amount FROM biz_main_contracts WHERE biz_code = %s", (m_code,))
            m_amt = float(cur.fetchone()[0])
            sub_amt = m_amt * random.uniform(0.1, 0.4)
            
            crud_base.upsert_dynamic_record("sub_contract", {
                "biz_code": sub_code,
                "sub_company_name": random.choice(SUB_COMPANIES),
                "book_main_code": m_code,
                "actual_main_code": m_code,
                "sub_amount": sub_amt,
                "is_back_to_back": random.choice(["是", "否"]),
                "settlement_status": random.choice(["未结算", "结算中", "已结算"])
            }, operator_name="System_Mock")

            # 制造付款流水
            pay_ratio = random.choice([0.2, 0.5, 0.9])
            pay_amt = sub_amt * pay_ratio
            cur.execute("""
                INSERT INTO biz_outbound_payments (biz_code, sub_contract_code, payment_amount, payment_date, operator)
                VALUES (%s, %s, %s, %s, 'Mock')
            """, (f"PAY-{sub_code}", sub_code, pay_amt, random_date(2025, 2026).strftime("%Y-%m-%d")))
            
            # 🔴 特意制造“税务流失红线”：付了钱，但收到的发票金额很少！
            inv_ratio = pay_ratio * random.choice([0.1, 0.5, 1.0]) 
            inv_amt = sub_amt * inv_ratio
            cur.execute("""
                INSERT INTO biz_sub_invoices (biz_code, sub_contract_code, invoice_amount, invoice_date, operator)
                VALUES (%s, %s, %s, %s, 'Mock')
            """, (f"SINV-{sub_code}", sub_code, inv_amt, random_date(2025, 2026).strftime("%Y-%m-%d")))
            
        conn.commit()
    finally:
        conn.close()

    print("🎉 高仿真业务数据生成完毕！请去浏览器刷新 Streamlit 页面查看。")

if __name__ == "__main__":
    generate_data()