# 文件位置: ERP_V2_PRO/fix_db.py
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.db_engine import get_connection
from backend.database.schema import sync_database_schema

conn = get_connection()
cur = conn.cursor()

print("🧨 正在暴力拆除所有 V1.0 时代的残留表...")
cur.execute("""
    DROP TABLE IF EXISTS 
    biz_main_contracts, 
    biz_sub_contracts, 
    biz_enterprises,
    biz_collections, 
    biz_outbound_payments, 
    biz_invoices,
    sys_audit_logs CASCADE;
""")
conn.commit()
conn.close()

print("🏗️ 正在按 app_config.json 全新标准重建 V2.0 纯净表...")
sync_database_schema()
print("✅ 旧表已全部拆除，V2.0 纯净版表结构已重建完毕！")