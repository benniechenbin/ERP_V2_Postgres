# 🟢 作用：CRUD 门面 (Facade) 路由
# 警告：不要在此文件写具体的业务逻辑！请前往对应的子模块编写！

# 1. 导入底层通用引擎
from backend.database.crud_base import (
    upsert_dynamic_record,
    fetch_dynamic_records,
    delete_dynamic_record,
    check_project_existence,
    generate_biz_code
)

# 2. 导入业财专有逻辑
from backend.database.crud_finance import (
    mark_project_as_accrued,
    execute_yearly_accrual_archive,
    check_main_contract_clearance,
    submit_sub_payment,
    sync_main_contract_finance,
    void_financial_record
)

# 3. 导入系统与后勤辅助
from backend.database.crud_sys import (
    get_attachment_counts,
    update_biz_code_cascade,
    soft_delete_project,
    restore_project,
    get_deleted_projects,
    log_job_operation
)
















