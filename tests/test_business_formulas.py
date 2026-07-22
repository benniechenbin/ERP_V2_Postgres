import pytest
import pandas as pd
from backend.database.crud_base import upsert_dynamic_record, delete_dynamic_record
from backend.database import db_engine
from backend.services.analysis_service import (
    calculate_overall_margin,
    get_manager_performance,
    get_high_risk_projects,
)


@pytest.fixture
def setup_business_data():
    # 注入测试所需的主合同和分包数据
    main_ids = []
    sub_ids = []

    # 1. 录入 2 个主合同 (合集 1000 万)
    res1, _ = upsert_dynamic_record(
        "main_contract",
        {
            "biz_code": "TEST-FORMULA-M01",
            "project_name": "核心公式测试项目A",
            "manager": "张绩效",
            "contract_amount": 6000000.0,
            "sign_date": "2025-01-10",
            "total_collected": 3000000.0,
            "uncollected_contract_amount": 3000000.0,
        },
    )

    res2, _ = upsert_dynamic_record(
        "main_contract",
        {
            "biz_code": "TEST-FORMULA-M02",
            "project_name": "核心公式测试项目B",
            "manager": "李绩效",
            "contract_amount": 4000000.0,
            "sign_date": "2026-02-15",
            "total_collected": 1000000.0,
            "uncollected_contract_amount": 3000000.0,
        },
    )

    # 2. 录入 2 个分包合同 (合计 400 万)
    res3, _ = upsert_dynamic_record(
        "sub_contract",
        {
            "biz_code": "TEST-FORMULA-S01",
            "sub_company_name": "分包A公司",
            "main_contract_code": "TEST-FORMULA-M01",
            "book_main_code": "TEST-FORMULA-M01",
            "sub_amount": 2500000.0,
        },
    )

    res4, _ = upsert_dynamic_record(
        "sub_contract",
        {
            "biz_code": "TEST-FORMULA-S02",
            "sub_company_name": "分包B公司",
            "main_contract_code": "TEST-FORMULA-M02",
            "book_main_code": "TEST-FORMULA-M02",
            "sub_amount": 1500000.0,
        },
    )

    # 记录生成的 ID 供清理
    df_m = pd.read_sql_query(
        "SELECT id FROM biz_main_contracts WHERE biz_code LIKE 'TEST-FORMULA-%'",
        db_engine.get_connection(),
    )
    main_ids = df_m["id"].tolist()

    df_s = pd.read_sql_query(
        "SELECT id FROM biz_sub_contracts WHERE biz_code LIKE 'TEST-FORMULA-%'",
        db_engine.get_connection(),
    )
    sub_ids = df_s["id"].tolist()

    yield

    # 清理数据
    for mid in main_ids:
        delete_dynamic_record("main_contract", mid)
    for sid in sub_ids:
        delete_dynamic_record("sub_contract", sid)


def test_margin_calculations(setup_business_data):
    # 测试毛利率分析公式
    # 收入: 600万 + 400万 = 1000万
    # 成本: 250万 + 150万 = 400万
    # 毛利: 600万, 毛利率: 60.0%
    report = calculate_overall_margin()
    assert report["total_income"] == 10000000.0
    assert report["total_cost"] == 4000000.0
    assert report["gross_profit"] == 6000000.0
    assert abs(report["margin_rate"] - 60.0) < 0.01


def test_manager_performance(setup_business_data):
    # 测试负责人绩效指标
    # 张绩效: 600万合同额, 李绩效: 400万合同额
    df = get_manager_performance()
    assert not df.empty

    row_zhang = df[df["manager_name"] == "张绩效"]
    assert not row_zhang.empty
    assert float(row_zhang.iloc[0]["total_contract"]) == 6000000.0
    assert float(row_zhang.iloc[0]["total_collected"]) == 3000000.0

    row_li = df[df["manager_name"] == "李绩效"]
    assert not row_li.empty
    assert float(row_li.iloc[0]["total_contract"]) == 4000000.0
    assert float(row_li.iloc[0]["total_collected"]) == 1000000.0


def test_high_risk_projects(setup_business_data):
    # 测试高危欠款大户检测
    # TEST-FORMULA-M01 签约日期为 2025 年，天数绝对超过宽限期 (grace_days)，且欠款为 300万 > 阈值 且欠款率 50% > 比例阈值
    # 期待它出现在高危名单中
    df = get_high_risk_projects(debt_threshold=1000000, rate_threshold=0.3, grace_days=180)
    assert not df.empty
    risk_codes = df["biz_code"].tolist()
    assert "TEST-FORMULA-M01" in risk_codes
