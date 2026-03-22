"""
ERP_V2_PRO 数据库核心引擎 (Database Facade)
对外暴露 V2.0 规范化接口
"""
from .db_engine import (
    get_connection, get_readonly_connection, get_current_db_name,
    backup_db, execute_raw_sql, db_health_report,
    UPLOAD_DIR, 
)
from .schema import (
    sync_database_schema, get_all_data_tables,
    has_column, get_table_schema, get_table_columns
)
from .crud import (
    upsert_dynamic_record, fetch_dynamic_records, delete_dynamic_record, # V2.0 核心三剑客
    check_project_existence,
    generate_biz_code, get_attachment_counts, soft_delete_project, restore_project,
    get_deleted_projects, update_biz_code_cascade, 
    mark_project_as_accrued, execute_yearly_accrual_archive,
    check_main_contract_clearance, submit_sub_payment,
    sync_main_contract_finance, void_financial_record
)

__all__ = [
    "get_connection", "get_readonly_connection", "get_current_db_name", 
     "backup_db", "execute_raw_sql", "db_health_report", 
    "UPLOAD_DIR", "sync_database_schema", "get_all_data_tables", 
    "has_column", "get_table_schema", "get_table_columns",
    "upsert_dynamic_record", "fetch_dynamic_records", "delete_dynamic_record",
    "check_project_existence",
    "generate_biz_code", "get_attachment_counts", "soft_delete_project", "restore_project",
    "get_deleted_projects", "update_biz_code_cascade",
    "mark_project_as_accrued", "execute_yearly_accrual_archive",
    "check_main_contract_clearance", "submit_sub_payment",
    "sync_main_contract_finance", "void_financial_record"
]