"""
ERP_V2_PRO 数据库核心引擎 (Database Facade)
对外暴露 V2.0 规范化接口
"""

from .crud import (
    check_main_contract_clearance,
    check_project_existence,
    delete_dynamic_record,  # V2.0 核心三剑客
    execute_yearly_accrual_archive,
    fetch_dynamic_records,
    generate_biz_code,
    get_attachment_counts,
    get_deleted_projects,
    mark_project_as_accrued,
    restore_project,
    soft_delete_project,
    submit_sub_payment,
    sync_main_contract_finance,
    update_biz_code_cascade,
    upsert_dynamic_record,
    void_financial_record,
)
from .db_engine import (
    UPLOAD_DIR,
    backup_db,
    db_health_report,
    execute_raw_sql,
    get_connection,
    get_current_db_name,
    get_readonly_connection,
)
from .schema import (
    get_all_data_tables,
    get_table_columns,
    get_table_schema,
    has_column,
    sync_database_schema,
)

__all__ = [
    "UPLOAD_DIR",
    "backup_db",
    "check_main_contract_clearance",
    "check_project_existence",
    "db_health_report",
    "delete_dynamic_record",
    "execute_raw_sql",
    "execute_yearly_accrual_archive",
    "fetch_dynamic_records",
    "generate_biz_code",
    "get_all_data_tables",
    "get_attachment_counts",
    "get_connection",
    "get_current_db_name",
    "get_deleted_projects",
    "get_readonly_connection",
    "get_table_columns",
    "get_table_schema",
    "has_column",
    "mark_project_as_accrued",
    "restore_project",
    "soft_delete_project",
    "submit_sub_payment",
    "sync_database_schema",
    "sync_main_contract_finance",
    "update_biz_code_cascade",
    "upsert_dynamic_record",
    "void_financial_record",
]
