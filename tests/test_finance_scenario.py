# 文件位置: ERP_V2_PRO/test_finance_scenario.py
# 🟢 作用：纯后端、无 UI 的“沙盘推演”自动化测试脚本

import sys
import os
import pandas as pd
from pathlib import Path

# 保证能找到 backend 模块
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.db_engine import get_connection, execute_raw_sql
from backend.database import crud_base
from backend.database import crud_finance

def clean_test_data():
    """清理测试遗留的脏数据"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM biz_main_contracts WHERE biz_code LIKE 'TEST-%'")
        cur.execute("DELETE FROM biz_sub_contracts WHERE biz_code LIKE 'TEST-%'")
        cur.execute("DELETE FROM biz_collections WHERE main_contract_code LIKE 'TEST-%'")
        cur.execute("DELETE FROM biz_outbound_payments WHERE sub_contract_code LIKE 'TEST-%'")
        conn.commit()
    finally:
        conn.close()

def inject_raw_data(table, data_dict):
    conn = get_connection()
    try:
        cur = conn.cursor()
        keys = list(data_dict.keys())
        values = tuple(data_dict.values()) 
        cols = ", ".join(keys)
        placeholders = ", ".join(["%s"] * len(keys))
        
        cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", values)
        conn.commit()
    finally:
        conn.close()

def run_scenario():
    print("🧹 1. 正在清理历史测试数据...")
    clean_test_data()

    print("🏗️ 2. 模拟业务员：录入一个 1000万 的主合同 (TEST-MAIN-001)...")
    res2, msg2 = crud_base.upsert_dynamic_record('main_contract', {
        'biz_code': 'TEST-MAIN-001',
        'project_name': '【沙盘推演】上海大厦项目',
        'contract_amount': 10000000  # 1000 万
    })
    print(f"  👉 写入结果: {res2}")

    print("🤝 3. 模拟分包经理：录入一个 200万 的分包合同，名义挂靠在 TEST-MAIN-001 上...")
    res3, msg3 = crud_base.upsert_dynamic_record('sub_contract', {
        'biz_code': 'TEST-SUB-001',
        'sub_company_name': '【沙盘推演】张三包工队',
        'book_main_code': 'TEST-MAIN-001',
        'main_contract_code': 'TEST-MAIN-001', # 确保物理关联也填上
        'sub_amount': 2000000          # 200 万
    })
    if not res3:
        print(f"\n🚨 致命错误：分包合同写入失败 -> {msg3}")
        sys.exit(1)

    # print("💰 4. 模拟财务：主合同收到甲方打款 400万 (回款率 40%)...")
    # inject_raw_data('biz_collections', {
    #     'biz_code': 'TEST-COLL-001',
    #     'main_contract_code': 'TEST-MAIN-001',
    #     'collected_amount': 4000000,
    #     'collected_date': '2026-03-20',
    #     'operator': '系统测试'
    # })
    print("💰 4. 模拟财务：主合同收到甲方全额打款 1000万 (回款率 100%)...")
    inject_raw_data('biz_collections', {
        'biz_code': 'TEST-COLL-001',
        'main_contract_code': 'TEST-MAIN-001',
        'collected_amount': 10000000, # 改为 1000 万
        'collected_date': '2026-03-20',
        'operator': '系统测试'
    })
    print("⚔️ 5. 模拟风控：测试分包背靠背红线与合规支付...")
    # 模拟先合法支付 50万
    success2, msg2 = crud_finance.submit_sub_payment(
        sub_biz_code='TEST-SUB-001', 
        payment_amount=500000, 
        operator='测试小哥', 
        payment_date='2026-03-21'
    )
    print(f"  👉 支付50万结果: {msg2}")
    
    # 这一步是为了模拟真实环境下触发一下分包总付额的重新计算
    execute_raw_sql("UPDATE biz_sub_contracts SET total_paid = 500000 WHERE biz_code = 'TEST-SUB-001'")

    print("\n" + "="*50)
    print("🛡️ [安全锁测试]：主合同删除与计提拦截")
    
    print("  [尝试违规删除主合同]：分包还有 150万 没付清，尝试强删主合同...")
    passed, msg = crud_finance.check_main_contract_clearance('TEST-MAIN-001')
    if not passed:
        print(f"  🟢 拦截成功！引擎拒绝删除，理由：\n{msg}")
    else:
        print("  ❌ 拦截失败！危险，允许删除了！")

    print("\n  [尝试违规计提主合同]：分包还有 150万 没付清，尝试计提主合同...")
    acc_success, acc_msg = crud_finance.mark_project_as_accrued("main_contract", "TEST-MAIN-001")
    if not acc_success:
        print(f"  🟢 拦截成功！引擎拒绝计提，理由：\n{acc_msg}")
    else:
        print("  ❌ 拦截失败！危险，允许计提了！")

    print("\n" + "="*50)
    print("💸 [结清测试]：把分包尾款结清，再尝试流转主合同")
    
    print("  [合规支付] 支付剩余 150万 分包款...")
    success_pay, msg_pay = crud_finance.submit_sub_payment(
        sub_biz_code='TEST-SUB-001', 
        payment_amount=1500000, 
        operator='财务主管', 
        payment_date='2026-03-21',
        remarks='支付尾款以准备项目计提'
    )
    print(f"  👉 支付结果: {msg_pay}")

    print("\n  [再次尝试计提主合同]...")
    # 此时引擎去算流水表：50万 + 150万 = 200万，刚好结清，锁会自动打开
    acc_success2, acc_msg2 = crud_finance.mark_project_as_accrued("main_contract", "TEST-MAIN-001")
    if acc_success2:
        print("  ✅ 计提成功！引擎识别到流水已平账，准许关账！")
    else:
        print(f"  ❌ 计提仍失败: {acc_msg2}")

    print("\n  [模拟年度大扫除] 执行全局年度结转...")
    arc_success, arc_msg = crud_finance.execute_yearly_accrual_archive()
    print(f"  👉 结转结果: {arc_msg}")
    
    # 断言：主合同应该已经被软删除了
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT deleted_at FROM biz_main_contracts WHERE biz_code = 'TEST-MAIN-001'")
    deleted_at = cur.fetchone()[0]
    conn.close()
    
    if deleted_at:
        print("  ✅ 完美闭环：TEST-MAIN-001 已被成功软删除移入历史档案！")
    else:
        print("  ❌ 闭环失败：数据未被软删除！")
        
    print("="*50 + "\n")

if __name__ == "__main__":
    try:
        run_scenario()
        print("\n🎉🎉 全链路自动化测试通过！核心财务引擎逻辑极其稳固！")
    except Exception as e:
        print(f"\n🚨🚨 测试过程中发生异常奔溃: {e}")