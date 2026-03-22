# 文件位置: backend/database/schema.py
# 🟢 作用：纯粹的底层数据库引擎，以后任何项目都不需要修改此文件！

import re
from backend.config import config_manager as cfg
from backend.database.db_engine import get_connection

# 引入刚刚解耦出去的定制表模块
from backend.database.custom_schema import execute_custom_static_tables
from backend.utils.logger import sys_logger

# =========================================================
# 1. 结构探测与工具库 (全部保留您的原始代码)
# =========================================================
def get_table_columns(table_name):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"获取列失败: {e}")
        return []
    finally:
        if conn: conn.close()
        
def get_table_schema(table_name):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", (table_name,))
        return [{"name": row[0], "type": row[1]} for row in cur.fetchall()]
    except Exception as e:
        print(f"获取表结构失败: {e}")
        return []
    finally:
        if conn: conn.close()

def has_column(table_name, column_name):
    return column_name in get_table_columns(table_name)

def sanitize_table_name(name):
    safe_name = re.sub(r'[^\w]', '_', str(name))
    if safe_name and safe_name[0].isdigit():
        safe_name = "_" + safe_name
    return f"data_{safe_name}".lower()

def get_all_data_tables():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND (table_name LIKE 'data_%' OR table_name LIKE 'biz_%')")
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        if conn: conn.close()

# =========================================================
# 2. V2.0 动态建表引擎 (核心黑盒)
# =========================================================
def _create_dynamic_business_tables(cursor):
    """读取 JSON 循环建表，自动注入系统列"""
    # 这里的 _CURRENT_CONFIG 需要通过函数获取最新状态
    config_data = cfg.load_data_rules() 
    models = config_data.get("models", {})
    
    for model_name, config in models.items():
        table_name = config.get("table_name")
        field_meta = config.get("field_meta", {})
        formula_cols = config.get("formulas", {}).keys()
        
        if not table_name or not field_meta: continue

        columns_sql = [
            "id SERIAL PRIMARY KEY",
            "deleted_at TIMESTAMP DEFAULT NULL",  # 原有的删除时间
            "deleted_by VARCHAR(50) DEFAULT NULL",  # 🟢 新增：记录到底是谁删的
            "extra_props JSONB DEFAULT '{}'::jsonb" 
        ]
        
        for field_key, meta in field_meta.items():
            if field_key in formula_cols:
                continue 
            field_type = meta.get("type", "text")
            if field_type == "money": col_def = f"{field_key} NUMERIC(15,2) DEFAULT 0.00"
            elif field_type == "percent": col_def = f"{field_key} REAL DEFAULT 0"
            elif field_type == "date": col_def = f"{field_key} DATE"
            elif field_type == "int": col_def = f"{field_key} INTEGER DEFAULT 0"
            else: col_def = f"{field_key} VARCHAR(255)"
                
            if field_key in ["biz_code", "sub_code"]:
                col_def += " UNIQUE NOT NULL"
                
            columns_sql.append(col_def)
        
        columns_sql.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        columns_sql.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        columns_str = ",\n    ".join(columns_sql)
        final_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n    {columns_str}\n);'
        cursor.execute(final_sql)
        
        # 🟢 热更新：为已存在的表追加 JSON 中新增的列
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
        existing_columns = {row[0] for row in cursor.fetchall()}
        
        for field_key, meta in field_meta.items():
            if field_key in formula_cols:
                continue
            if field_key not in existing_columns:
                field_type = meta.get("type", "text")
                if field_type == "money": alter_type = "NUMERIC(15,2) DEFAULT 0.00"
                elif field_type == "date": alter_type = "DATE"
                else: alter_type = "VARCHAR(255)"
                
                try:
                    cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "{field_key}" {alter_type};')
                    print(f"🔧 热更新：表 [{table_name}] 自动新增列 [{field_key}]")
                except Exception as alt_e:
                    print(f"⚠️ 追加列失败: {alt_e}")

# =========================================================
# 3. 统一入口
# =========================================================
def sync_database_schema():
    """引擎启动器"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # 0. 创建审计日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_audit_logs (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) NOT NULL,     -- 被操作的业务编号
            model_name VARCHAR(50),             -- 所属模型 (如 enterprise, main_contract)
            action VARCHAR(20),                 -- 动作类型 (INSERT/UPDATE/DELETE/RESTORE)
            operator_name VARCHAR(50),          -- 操作人
            diff_data JSONB,                    -- 变更详情快照 {"字段": ["旧值", "新值"]}
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
        # 1. 创建附件归档表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_attachments (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) NOT NULL,      -- 挂载的业务主体编号 (如 MAIN-001, SUB-002)
            source_table VARCHAR(50),            -- 来源模型名称 (如 main_contract)
            
            -- 🟢 新增：对接前端的下拉框分类
            file_category VARCHAR(50),           -- 附件分类 (主合同/图纸/结算单等) 
            
            file_name TEXT,                      -- 原始文件名
            file_path TEXT,                      -- 服务器物理路径或 OSS 链接
            file_type VARCHAR(50),               -- 文件后缀名 (pdf/docx/jpg)
            file_size_kb INTEGER DEFAULT 0,      -- 🟢 新增：文件大小(便于以后做网盘容量统计)
            
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

        # 2. 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL, 
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT '普通员工',
            
            -- 1. 业务状态：账号是否被冻结（例如离职、休假、输错密码锁定）
            status VARCHAR(20) DEFAULT 'active',        -- 状态：active(活跃), disabled(禁用), locked(锁定)
            disabled_at TIMESTAMP DEFAULT NULL,         -- 记录账号被禁用的具体时间
            
            -- 2. 架构一致性：软删除标记
            deleted_at TIMESTAMP DEFAULT NULL,          -- NULL表示在职，有时间表示该账号已从系统中彻底移除
            
            -- 3. 安全审计：最后登录时间
            last_login_at TIMESTAMP DEFAULT NULL,       
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
        
        # 3. 创建AI任务表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_ai_tasks (
            id SERIAL PRIMARY KEY,
            file_id INTEGER,                     
            task_type VARCHAR(50) DEFAULT 'contract_extraction', 
            status VARCHAR(20) DEFAULT 'pending', 
            result_json JSONB,                   
            error_msg TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
        # 4. 创建任务日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_job_logs (
            id SERIAL PRIMARY KEY,
            operator VARCHAR(50),      -- 触发人或系统调度器名 (如 'system_cron')
            
            job_type VARCHAR(50),      -- 任务类型 (如 'excel_import', 'api_sync', 'monthly_accrual')
            target_model VARCHAR(50),  -- 影响的业务模型 (如 'main_contract')
            source_name VARCHAR(255),  -- 数据源载体 (文件名，或接口标识符)
            
            status VARCHAR(20) DEFAULT 'processing', -- 状态: processing, success, partial_fail, failed
            
            total_count INTEGER DEFAULT 0,   -- 计划处理总数
            success_count INTEGER DEFAULT 0, -- 成功条数
            fail_count INTEGER DEFAULT 0,    -- 失败条数
            
            error_details TEXT,              -- 详细报错追踪 (JSON格式)
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP           -- 任务完成时间
        )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_audit_biz" ON sys_audit_logs(biz_code);')
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_attachments_biz" ON sys_attachments(biz_code);')
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_ai_tasks_status" ON sys_ai_tasks(status);')
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_users_status" ON sys_users(status);')
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_users_role" ON sys_users(role);')
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_job_logs_status" ON sys_job_logs(status);')
        # 1. 启动动态引擎建主表
        _create_dynamic_business_tables(cursor)
        
        # 2. 调用外部的定制模块建流水表
        execute_custom_static_tables(cursor)
        
        conn.commit()
        sys_logger.info("🚀 [引擎启动] V2.0 数据库架构同步完毕！")
        return True
    except Exception as e:
        if conn: conn.rollback()
        sys_logger.critical(f"❌ 数据库同步失败: {e}")
        return False
    finally:
        if conn: conn.close()
