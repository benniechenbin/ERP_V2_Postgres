import os
import psycopg2
import sys
if sys.platform == 'win32':
    os.environ['PGCLIENTENCODING'] = 'utf-8'
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine

# ==========================================
# 1. 路径配置 (仅用于附件 UPLOAD)
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. 数据库连接配置 (对接 Docker)
# ==========================================
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5435")
DB_USER = os.getenv("DB_USER", "erp_admin")
DB_PASS = os.getenv("DB_PASS", "admin")
DB_NAME = os.getenv("DB_NAME", "erp_core_db")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

sql_engine = create_engine(
    DATABASE_URL, 
    pool_size=10, 
    max_overflow=20
)

def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME
        )
        return conn
    except Exception as e:
        # 如果是 UnicodeDecodeError，说明是 Windows 在报中文错误
        if isinstance(e, UnicodeDecodeError):
            # 这里的 e.object 是原始字节，手动用 GBK 解码它
            raw_msg = e.object.decode('gbk', errors='ignore')
            print(f"🚨 数据库连接失败 (已解码): {raw_msg}")
        else:
            print(f"🚨 数据库连接失败: {e}")
        raise e

def get_readonly_connection(db_name=None):
    """【兼容性】实验室只读连接"""
    return get_connection()

# ==========================================
# 3. 状态与管理函数 (收编并改造)
# ==========================================

def get_current_db_name():
    """返回当前连接的库名"""
    return DB_NAME

def set_current_db(name):
    """【废弃兼容】PG 时代不动态切库，仅作 pass"""
    pass

def get_available_dbs():
    """扫描 PG 实例中所有的数据库列表"""
    conn = None
    try:
        # 连接到系统库查询所有数据库
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname='postgres')
        cur = conn.cursor()
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        return [row[0] for row in cur.fetchall()]
    except:
        return [DB_NAME]
    finally:
        if conn: conn.close()

def check_db_exists(name):
    """检查特定名称的库是否存在"""
    return name in get_available_dbs()

# ==========================================
# 4. 运维指令 (重构为 SQL 指令)
# ==========================================

def execute_raw_sql(sql, params=None):
    """执行原生 SQL 语句 (适配 %s 占位符)"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params or [])
        
        # 如果是查询语句，返回 DataFrame
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return True, pd.DataFrame(rows, columns=cols)
        
        conn.commit()
        return True, f"影响行数: {cur.rowcount}"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def backup_db():
    """
    【注意】PG 的备份建议使用命令行 pg_dump。
    此函数仅提供逻辑占位，或执行简单的表级备份。
    """
    return False, "请通过 Docker 使用 pg_dump 进行物理备份"

def db_health_report():
    """扫描 PG 数据健康度"""
    import json
    from backend.database.schema import get_all_data_tables 
    conn = None
    try:
        conn = get_connection()
        tables = get_all_data_tables()
        report = {"total_tables": len(tables), "invalid_json": 0, "stats": {}}
        
        for t in tables:
            try:
                # PG 的 JSONB 验证更严苛，通常不会有非法 JSON
                cur = conn.cursor()
                cur.execute(f'SELECT count(*) FROM "{t}"')
                report["stats"][t] = cur.fetchone()[0]
            except:
                pass
        return report
    finally:
        if conn: conn.close()