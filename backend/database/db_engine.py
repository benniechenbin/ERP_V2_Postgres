import os
import sys
if sys.platform == 'win32':
    os.environ['PGCLIENTENCODING'] = 'utf-8'

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = "RealDictCursor"

import re
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, event
from backend.observability.logger import setup_logger, sys_logger 
from backend.config.settings import BACKUP_DIR, PROJECT_ROOT, UPLOAD_DIR, settings

# ==========================================
# 1. 路径配置 (仅用于附件 UPLOAD)
# ==========================================
BASE_DIR = PROJECT_ROOT  # 兼容旧代码中的命名
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. 数据库连接配置
# ==========================================
if settings.DB_TYPE == "sqlite":
    db_path = settings.sqlite_db_file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"
    sql_engine = create_engine(DATABASE_URL)
    
    # 启用 WAL 模式以在 Streamlit 线程环境下支持更好的并发
    @event.listens_for(sql_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
else:
    DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    sql_engine = create_engine(
        DATABASE_URL, 
        pool_size=10, 
        max_overflow=20
    )

# ==========================================
# 3. SQLite 兼容适配层
# ==========================================
def translate_pg_to_sqlite(sql: str) -> str:
    if not sql:
        return sql
    
    # 1. 占位符替换 %s -> ?
    sql = sql.replace('%s', '?')
    
    # 2. DDL 语法适配
    sql = re.sub(r'\bSERIAL\s+PRIMARY\s+KEY\b', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bJSONB\b', 'TEXT', sql, flags=re.IGNORECASE)
    
    # 剥离 PG 类型强转语法 (如 ::jsonb, ::numeric, ::text)
    sql = re.sub(r'::jsonb\b', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'::numeric\b', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'::text\b', '', sql, flags=re.IGNORECASE)
    
    # 剥离 PG FOR UPDATE 行锁
    sql = re.sub(r'\bFOR\s+UPDATE\b', '', sql, flags=re.IGNORECASE)
    
    # EXTRACT(YEAR FROM column) -> CAST(strftime('%Y', column) AS INTEGER)
    sql = re.sub(
        r'\bEXTRACT\s*\(\s*YEAR\s+FROM\s+([\w\.]+)\s*\)', 
        r"CAST(strftime('%Y', \1) AS INTEGER)", 
        sql, 
        flags=re.IGNORECASE
    )
    
    # 剥离 DDL ADD COLUMN 中的 IF NOT EXISTS
    sql = re.sub(r'\bADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\b', 'ADD COLUMN', sql, flags=re.IGNORECASE)
    
    # 剥离 RETURNING id，避免老版本 SQLite 兼容性报错
    sql = re.sub(r'\bRETURNING\s+id\b', '', sql, flags=re.IGNORECASE)

    # 1. 修复 analysis_service 中的 TO_CHAR(xxx, 'YYYY-MM') -> strftime('%Y-%m', xxx)
    sql = re.sub(
        r"\bTO_CHAR\s*\(\s*([\w\.]+)\s*,\s*'YYYY-MM'\s*\)",
        r"strftime('%Y-%m', \1)",
        sql,
        flags=re.IGNORECASE
    )

    # 2. 修复看板中的 CURRENT_DATE + INTERVAL '30 days' -> date('now', '+30 days')
    sql = re.sub(
        r"\bCURRENT_DATE\s*\+\s*INTERVAL\s*'(\d+)\s+days?'",
        r"date('now', '+\1 days')",
        sql,
        flags=re.IGNORECASE
    )

    # 3. 剥离 SQLite 不支持的 NULLS LAST 排序规则
    sql = re.sub(r'\bNULLS\s+LAST\b', '', sql, flags=re.IGNORECASE)
    return sql



class SQLiteCursorWrapper:
    def __init__(self, cursor, as_dict=False):
        self._cursor = cursor
        self.as_dict = as_dict

    def execute(self, sql, params=None):
        sql = translate_pg_to_sqlite(sql)
        if params is None:
            return self._cursor.execute(sql)
        else:
            return self._cursor.execute(sql, params)

    def executemany(self, sql, seq_of_parameters):
        sql = translate_pg_to_sqlite(sql)
        return self._cursor.executemany(sql, seq_of_parameters)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self.as_dict:
            keys = [col[0] for col in self._cursor.description] if self._cursor.description else []
            if keys:
                return dict(zip(keys, row))
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows:
            return []
        if self.as_dict:
            keys = [col[0] for col in self._cursor.description] if self._cursor.description else []
            if keys:
                return [dict(zip(keys, rows_item)) for rows_item in rows]
        return rows

    def __iter__(self):
        return self

    def __next__(self):
        row = next(self._cursor)
        if self.as_dict:
            keys = [col[0] for col in self._cursor.description] if self._cursor.description else []
            if keys:
                return dict(zip(keys, row))
        return row

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getattr__(self, name):
        return getattr(self._cursor, name)

class SQLiteConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, cursor_factory=None):
        # 只要 cursor_factory 不为 None，我们认为其需要 RealDictCursor 特性
        cursor = self._conn.cursor()
        return SQLiteCursorWrapper(cursor, as_dict=(cursor_factory is not None))

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)

# ==========================================
# 4. 数据库引擎接口
# ==========================================
def get_connection():
    """
    🟢 架构升级：直接从 SQLAlchemy 的连接池中借用底层连接，并进行多数据库适配。
    """
    try:
        conn = sql_engine.raw_connection()
        if settings.DB_TYPE == "sqlite":
            return SQLiteConnectionWrapper(conn)
        return conn
    except Exception as e:
        sys_logger.exception(f"🚨 数据库连接获取失败: {e}", exc_info=True)
        raise e
        
def get_readonly_connection(db_name=None):
    """【兼容性】实验室只读连接"""
    return get_connection()

def get_current_db_name():
    """返回当前连接的库名"""
    if settings.DB_TYPE == "sqlite":
        return settings.sqlite_db_file.name
    return settings.DB_NAME

def execute_raw_sql(sql, params=None):
    """执行原生 SQL 语句"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params or [])
        
        # 如果是查询语句，返回 DataFrame
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            # 如果 rows 中的元素是 dict (源自 RealDictCursor 适配器)，我们需要提取 values
            if rows and isinstance(rows[0], dict):
                rows = [list(r.values()) for r in rows]
            return True, pd.DataFrame(rows, columns=cols)
        
        conn.commit()
        return True, f"影响行数: {cur.rowcount}"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def backup_db():
    """数据库备份"""
    if settings.DB_TYPE == "sqlite":
        try:
            import shutil
            db_path = settings.sqlite_db_file
            if not db_path.exists():
                return False, "数据库文件不存在，无法备份"
            backup_dir = BACKUP_DIR
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_name = f"sqlite_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = backup_dir / backup_name
            shutil.copy2(db_path, backup_path)
            return True, f"SQLite 数据库备份成功: {backup_path.name}"
        except Exception as e:
            return False, f"SQLite 备份失败: {e}"
    else:
        return False, "请通过 Docker 使用 pg_dump 进行物理备份"

def db_health_report():
    """数据健康度扫描"""
    from backend.database.schema import get_all_data_tables 
    conn = None
    try:
        conn = get_connection()
        tables = get_all_data_tables()
        report = {"total_tables": len(tables), "invalid_json": 0, "stats": {}}
        
        for t in tables:
            try:
                cur = conn.cursor()
                cur.execute(f'SELECT count(*) FROM "{t}"')
                row = cur.fetchone()
                # 如果 row 是 dict 包装的
                val = row[0] if not isinstance(row, dict) else list(row.values())[0]
                report["stats"][t] = val
            except:
                pass
        return report
    finally:
        if conn: conn.close()
