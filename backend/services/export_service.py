import os
import pandas as pd
from datetime import datetime
import json

# 🟢 统一从大本营入口引入
from backend.database import get_connection

def export_table_data(table_name, export_dir="exports", file_format="xlsx"):
    """
    [导出服务] 导出数据表为 Excel/CSV (PostgreSQL JSONB 防爆适配版)
    """
    if not os.path.exists(export_dir):
        os.makedirs(export_dir, exist_ok=True)
        
    conn = None
    try:
        conn = get_connection()
        # 读取 PG 数据，此时 JSONB 字段会被 psycopg2 解析为 dict
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
        
        if df.empty:
            return False, "表中无数据"

        # 🟢 防爆装甲：扫描所有列，如果单元格里是字典或列表(来自 JSONB)，强制转回字符串
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{table_name}_{timestamp}.{file_format}"
        file_path = os.path.join(export_dir, file_name)
        
        # 导出文件
        if file_format == 'xlsx':
            # 去除可能导致 openpyxl 报错的非法时区信息
            for col in df.select_dtypes(include=['datetimetz']).columns:
                df[col] = df[col].dt.tz_localize(None)
            df.to_excel(file_path, index=False)
        else:
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
        return True, file_path
    except Exception as e:
        return False, f"导出失败: {str(e)}"
    finally:
        if conn:
            conn.close()