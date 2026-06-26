import os
import pytest
from backend.config.settings import settings
import backend.database.db_engine as db_engine
from backend.database.schema import sync_database_schema
from sqlalchemy import create_engine, event

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # 1. 强制将配置切换到测试 SQLite 数据库
    settings.DB_TYPE = "sqlite"
    settings.SQLITE_DB_PATH = "data/test_temp.db"
    
    # 2. 重新初始化 db_engine.py 中的 sql_engine
    db_path = settings.sqlite_db_file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 清理可能残留的数据库文件以保持干净测试环境
    if db_path.exists():
        try:
            db_path.unlink()
        except:
            pass
            
    DATABASE_URL = f"sqlite:///{db_path}"
    test_engine = create_engine(DATABASE_URL)
    
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
        
    # 用测试引擎替换 db_engine 的全局 sql_engine
    db_engine.sql_engine = test_engine
    
    # 3. 同步数据库表结构
    sync_database_schema()
    
    yield
    
    # 4. 测试结束后清理测试数据库文件
    test_engine.dispose()
    
    # 尽可能删除临时生成的各种 sqlite 文件 (.db, .db-wal, .db-shm)
    if db_path.exists():
        try:
            db_path.unlink()
        except:
            pass
            
    for f in db_path.parent.glob("test_temp.db*"):
        try:
            f.unlink()
        except:
            pass

@pytest.fixture(autouse=True)
def cleanup_database_tables():
    # 在每个测试执行前清理所有数据表，确保测试隔离
    conn = db_engine.get_connection()
    try:
        cursor = conn.cursor()
        if settings.DB_TYPE == "sqlite":
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                cursor.execute(f'DELETE FROM "{table}"')
                try:
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))
                except:
                    pass
        else:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                cursor.execute(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE')
        conn.commit()
    except Exception as e:
        print(f"Cleanup database tables failed: {e}")
    finally:
        conn.close()
    yield
