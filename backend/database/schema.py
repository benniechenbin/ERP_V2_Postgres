# 文件位置: backend/database/schema.py
# 🟢 作用：纯粹的底层数据库引擎，以后任何项目都不需要修改此文件！

import re
from backend.config import config_manager as cfg
from backend.database.db_engine import get_connection

# 引入刚刚解耦出去的定制表模块
from backend.database.custom_schema import execute_custom_static_tables

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
            "deleted_at TIMESTAMP DEFAULT NULL",  # 🟢 升级：记录具体的删除时间，NULL表示存活
            "extra_props JSONB DEFAULT '{}'::jsonb" # V2.0 终极兜底袋
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
        
        # 1. 启动动态引擎建主表
        _create_dynamic_business_tables(cursor)
        
        # 2. 调用外部的定制模块建流水表
        execute_custom_static_tables(cursor)
        
        conn.commit()
        print("🚀 [引擎启动] V2.0 数据库架构同步完毕！")
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ 数据库同步失败: {e}")
        return False
    finally:
        if conn: conn.close()

def init_db():
    """向后兼容的别名接口"""
    sync_database_schema()