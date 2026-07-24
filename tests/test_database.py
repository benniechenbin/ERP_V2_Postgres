from backend.database import db_engine
from backend.database.crud_base import (
    check_project_existence,
    delete_dynamic_record,
    fetch_dynamic_records,
    generate_biz_code,
    upsert_dynamic_record,
)
from backend.database.crud_sys import (
    get_deleted_projects,
    restore_project,
    soft_delete_project,
)
from backend.database.schema import (
    get_all_data_tables,
    get_table_columns,
    get_table_schema,
)


def test_database_metadata():
    # 验证元数据探测功能是否正常
    tables = get_all_data_tables()
    assert len(tables) > 0
    assert "biz_main_contracts" in tables
    assert "biz_sub_contracts" in tables

    # 验证获取列列表
    cols = get_table_columns("biz_main_contracts")
    assert "id" in cols
    assert "biz_code" in cols
    assert "project_name" in cols
    assert "deleted_at" in cols

    # 验证获取表结构
    schema = get_table_schema("biz_main_contracts")
    assert len(schema) > 0
    col_names = [item["name"] for item in schema]
    assert "biz_code" in col_names


def test_crud_dynamic_records():
    # 1. 写入测试数据
    biz_code = "TEST-DB-001"
    data = {
        "biz_code": biz_code,
        "project_name": "测试项目D1",
        "manager": "王测试",
        "contract_amount": 5000000.0,
        "extra_field_abc": "这是溢出JSON字段的数据",  # 模拟扩展字段存入 extra_props
    }

    success, _msg = upsert_dynamic_record("main_contract", data)
    assert success is True

    # 2. 查询验证
    df = fetch_dynamic_records("main_contract", "测试项目D1")
    assert not df.empty
    row = df.iloc[0]
    assert row["biz_code"] == biz_code
    assert row["project_name"] == "测试项目D1"
    assert row["manager"] == "王测试"
    assert float(row["contract_amount"]) == 5000000.0

    # 验证溢出字段是否存入并能够反序列化展平
    from backend.services.analysis_service import _flatten_extra_props

    df_flat = _flatten_extra_props(df)
    assert "extra_field_abc" in df_flat.columns
    assert df_flat.iloc[0]["extra_field_abc"] == "这是溢出JSON字段的数据"

    # 3. 验证审计日志写入
    conn = db_engine.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT action, biz_code, model_name FROM sys_audit_logs WHERE biz_code = %s",
            (biz_code,),
        )
        audit_row = cur.fetchone()
        assert audit_row is not None
        # 如果 row 是 dict 包装的
        if isinstance(audit_row, dict):
            assert audit_row["action"] == "INSERT"
            assert audit_row["model_name"] == "main_contract"
        else:
            assert audit_row[0] == "INSERT"
            assert audit_row[2] == "main_contract"
    finally:
        conn.close()

    # 4. 修改记录测试
    record_id = int(row["id"])
    update_data = {
        "biz_code": biz_code,
        "project_name": "测试项目D1-已修改",
        "contract_amount": 6000000.0,
    }
    success_up, _msg_up = upsert_dynamic_record(
        "main_contract", update_data, record_id=record_id, operator_name="测试修改员"
    )
    assert success_up is True

    # 重新查询核对修改
    df_new = fetch_dynamic_records("main_contract", "已修改")
    assert not df_new.empty
    assert df_new.iloc[0]["project_name"] == "测试项目D1-已修改"
    assert float(df_new.iloc[0]["contract_amount"]) == 6000000.0

    # 5. 唯一性校验测试
    exist_check = check_project_existence(biz_code=biz_code)
    assert exist_check["exists"] is True
    assert "冲突" in exist_check["msg"]

    exist_check_fake = check_project_existence(biz_code="FAKE-BIZ-CODE")
    assert exist_check_fake["exists"] is False

    # 6. 物理删除测试
    del_success, _del_msg = delete_dynamic_record("main_contract", record_id)
    assert del_success is True


def test_soft_delete_and_restore():
    # 1. 写入待删除的数据
    biz_code = "TEST-DB-002"
    data = {"biz_code": biz_code, "project_name": "待回收站项目", "manager": "李删除"}
    success, _msg = upsert_dynamic_record("main_contract", data)
    assert success is True

    df = fetch_dynamic_records("main_contract", "待回收站项目")
    assert not df.empty
    record_id = int(df.iloc[0]["id"])

    # 2. 软删除
    soft_success, _soft_msg = soft_delete_project(record_id, "biz_main_contracts", operator_name="测试审计官")
    assert soft_success is True

    # 确认查询时查不出来了
    df_after_del = fetch_dynamic_records("main_contract", "待回收站项目")
    assert df_after_del.empty

    # 确认出现在回收站中
    deleted_list = get_deleted_projects(["biz_main_contracts"])
    deleted_codes = [item["biz_code"] for item in deleted_list]
    assert biz_code in deleted_codes

    # 3. 恢复项目
    restore_success, _restore_msg = restore_project(record_id, "biz_main_contracts")
    assert restore_success is True

    # 确认重新出现在正常列表
    df_after_restore = fetch_dynamic_records("main_contract", "待回收站项目")
    assert not df_after_restore.empty
    assert df_after_restore.iloc[0]["biz_code"] == biz_code

    # 清理数据
    delete_dynamic_record("main_contract", record_id)


def test_generate_biz_code():
    code1 = generate_biz_code("biz_main_contracts", "TEST-MAIN")
    assert code1.startswith("TEST-MAIN")
    assert len(code1) > 10
