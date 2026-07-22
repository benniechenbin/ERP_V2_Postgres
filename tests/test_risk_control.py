import pytest
import pandas as pd
from backend.database.crud_base import upsert_dynamic_record, delete_dynamic_record
from backend.database.crud_finance import submit_sub_payment, mark_project_as_accrued
from backend.core.finance_engine import validate_sub_payment_risk
from backend.database import db_engine


@pytest.fixture
def setup_risk_data():
    # 注入风控校验场景数据
    main_ids = []
    sub_ids = []

    # 1. 录入主合同 (TEST-RISK-M01), 金额 1000 万
    res1, _ = upsert_dynamic_record(
        "main_contract",
        {
            "biz_code": "TEST-RISK-M01",
            "project_name": "核心风控测试主合同",
            "contract_amount": 10000000.0,
            "total_collected": 5000000.0,  # 收款率 50%
            "uncollected_contract_amount": 5000000.0,
        },
    )

    # 插入一条资金回款流水以确保主合同有 50% 的真实回款率
    conn = db_engine.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO biz_collections (biz_code, main_contract_code, collected_amount, collected_date) VALUES (%s, %s, %s, %s)",
            ("TEST-RISK-COLL-01", "TEST-RISK-M01", 5000000.0, "2026-03-20"),
        )
        conn.commit()
    finally:
        conn.close()

    # 2. 录入分包合同 1 (TEST-RISK-S01), 金额 200 万, 背靠背 (is_back_to_back = 是)
    res2, _ = upsert_dynamic_record(
        "sub_contract",
        {
            "biz_code": "TEST-RISK-S01",
            "sub_company_name": "背靠背分包商",
            "main_contract_code": "TEST-RISK-M01",
            "book_main_code": "TEST-RISK-M01",
            "sub_amount": 2000000.0,
            "is_back_to_back": "是",
        },
    )

    # 3. 录入分包合同 2 (TEST-RISK-S02), 金额 100 万, 非背靠背 (is_back_to_back = 否)
    res3, _ = upsert_dynamic_record(
        "sub_contract",
        {
            "biz_code": "TEST-RISK-S02",
            "sub_company_name": "非背靠背分包商",
            "main_contract_code": "TEST-RISK-M01",
            "book_main_code": "TEST-RISK-M01",
            "sub_amount": 1000000.0,
            "is_back_to_back": "否",
        },
    )

    df_m = pd.read_sql_query(
        "SELECT id FROM biz_main_contracts WHERE biz_code LIKE 'TEST-RISK-%'",
        db_engine.get_connection(),
    )
    main_ids = df_m["id"].tolist()

    df_s = pd.read_sql_query(
        "SELECT id FROM biz_sub_contracts WHERE biz_code LIKE 'TEST-RISK-%'",
        db_engine.get_connection(),
    )
    sub_ids = df_s["id"].tolist()

    yield

    # 清理数据
    conn = db_engine.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM biz_outbound_payments WHERE sub_contract_code LIKE 'TEST-RISK-%'")
        cur.execute("DELETE FROM biz_collections WHERE main_contract_code LIKE 'TEST-RISK-%'")
        conn.commit()
    finally:
        conn.close()

    for mid in main_ids:
        delete_dynamic_record("main_contract", mid)
    for sid in sub_ids:
        delete_dynamic_record("sub_contract", sid)


def test_back_to_back_payment_risk(setup_risk_data):
    # 主合同收款率是 50%

    # 1. 尝试对【非背靠背分包】TEST-RISK-S02 支付 80 万 (占总额 80%)，期待放行 (因为不受主合同收款率限制)
    passed1, msg1 = validate_sub_payment_risk("TEST-RISK-S02", 800000.0)
    assert passed1 is True
    assert "非背靠背合同" in msg1

    # 2. 尝试对【背靠背分包】TEST-RISK-S01 支付 80 万 (占总额 40%)，期待放行 (40% <= 50% 收款率)
    passed2, msg2 = validate_sub_payment_risk("TEST-RISK-S01", 800000.0)
    assert passed2 is True

    # 3. 尝试对【背靠背分包】TEST-RISK-S01 支付 120 万 (占总额 60%)，期待拦截 (60% > 50% 收款率)
    passed3, msg3 = validate_sub_payment_risk("TEST-RISK-S01", 1200000.0)
    assert passed3 is False
    assert "安全拦截" in msg3


def test_main_contract_clearance_accrual(setup_risk_data):
    # 分包总额合计 300万 未支付。尝试对主合同进行计提 (mark_project_as_accrued)，应该被拦截
    acc_success, acc_msg = mark_project_as_accrued("main_contract", "TEST-RISK-M01")
    assert acc_success is False
    assert "操作拦截：名下有分包未结清" in acc_msg

    # 再次插入一条 500万 回款流水，使主合同收款率达到 100%，以允许分包付款正常通过风控拦截
    conn = db_engine.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO biz_collections (biz_code, main_contract_code, collected_amount, collected_date) VALUES (%s, %s, %s, %s)",
            ("TEST-RISK-COLL-02", "TEST-RISK-M01", 5000000.0, "2026-03-21"),
        )
        conn.commit()
    finally:
        conn.close()

    # 模拟支付完分包款 (结清分包)
    # 对分包 1 (200万) 支付 200万
    success_pay1, msg_pay1 = submit_sub_payment(
        sub_biz_code="TEST-RISK-S01",
        payment_amount=2000000.0,
        operator="测试财务",
        payment_date="2026-03-22",
    )
    assert success_pay1 is True
    # 手动更新分包 1 的已付字段（测试脚本中没有触发重新计算，在这里我们更新真实的数据库字段以让 check_main_contract_clearance 正确计算）
    db_engine.execute_raw_sql("UPDATE biz_sub_contracts SET total_paid = 2000000 WHERE biz_code = 'TEST-RISK-S01'")

    # 对分包 2 (100万) 支付 100万
    success_pay2, msg_pay2 = submit_sub_payment(
        sub_biz_code="TEST-RISK-S02",
        payment_amount=1000000.0,
        operator="测试财务",
        payment_date="2026-03-22",
    )
    assert success_pay2 is True
    db_engine.execute_raw_sql("UPDATE biz_sub_contracts SET total_paid = 1000000 WHERE biz_code = 'TEST-RISK-S02'")

    # 再次尝试计提主合同，期待成功！
    acc_success2, acc_msg2 = mark_project_as_accrued("main_contract", "TEST-RISK-M01")
    assert acc_success2 is True
    assert "更新成功" in acc_msg2
