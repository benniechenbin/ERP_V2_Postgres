import json
import pandas as pd
from datetime import datetime
import warnings

from backend.config import config_manager as cfg
from backend.database.db_engine import get_connection, sql_engine
from backend.database.schema import get_all_data_tables
from backend.core import core_logic  # 用于应用业务公式

def upsert_dynamic_record(model_name: str, data_dict: dict, record_id: int = None, operator_id: int = 0, operator_name: str = 'System'):
    """
    [V2.0 混合架构写入引擎 + 全自动审计拦截器]
    自带智能分拣，并全自动记录数据变更历史 (时光机)。
    """
    from backend.config import config_manager as cfg
    import json
    
    model_config = cfg.get_model_config(model_name)
    table_name = model_config.get("table_name")
    
    if not table_name: return False, "未找到模型配置"
        
    conn = None
    try:
        from backend.database.db_engine import get_connection # 确保局部导入或在文件头已导入
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. 智能探针：获取数据库真实物理列
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
        valid_columns = {row[0] for row in cursor.fetchall()}
        
        # 2. 🟢 智能分拣 (Smart Routing)
        physical_data = {}
        overflow_data = {}
        
        # 忽略系统保护列
        ignore_cols = ['id', 'created_at', 'updated_at', 'deleted_at', 'extra_props']
        
        for k, v in data_dict.items():
            if k in ignore_cols: continue
            if k in valid_columns:
                physical_data[k] = v
            else:
                overflow_data[k] = v
                
        # 序列化 JSONB 溢出数据
        physical_data['extra_props'] = json.dumps(overflow_data, ensure_ascii=False) if overflow_data else '{}'

        if not physical_data: return False, "没有有效的写入数据"

        keys = list(physical_data.keys())
        values = list(physical_data.values())
        biz_code = data_dict.get('biz_code', 'UNKNOWN') # 获取业务编号，用于审计追踪
        
        # ========================================================
        # 🟢 3. 核心大招：全自动差异引擎 (Diff Engine)
        # ========================================================
        if record_id:
            # (A) 抓取老账本：取出修改前的完整数据
            cursor.execute(f'SELECT * FROM "{table_name}" WHERE id = %s', (record_id,))
            old_row = cursor.fetchone()
            
            if old_row:
                # 把老记录转成字典，并将 extra_props 里的溢出字段也平铺开来
                old_dict = dict(zip([col[0] for col in cursor.description], old_row))
                old_extra = old_dict.get('extra_props', {})
                if isinstance(old_extra, str): 
                    try: old_extra = json.loads(old_extra)
                    except: old_extra = {}
                flat_old_data = {**old_dict, **old_extra}
                
                # (B) ✨ 找不同：比对新老数据
                diff_data = {}
                for k, new_v in data_dict.items():
                    if k in ignore_cols: continue
                    old_v = flat_old_data.get(k)
                    
                    # 统一转成字符串对比，防止数字 100 和浮点数 100.0 被误判为不同
                    # 处理 None 值，使其在 JSON 中更友好
                    str_old = str(old_v) if pd.notna(old_v) and old_v is not None else ""
                    str_new = str(new_v) if pd.notna(new_v) and new_v is not None else ""
                    
                    if str_old != str_new:
                        diff_data[k] = [str_old or "空", str_new or "空"] # 格式: {字段: [旧, 新]}
                
                # (C) 留底案：只要有差异，就静默写入审计表
                if diff_data:
                    audit_sql = """
                        INSERT INTO sys_audit_logs (table_name, biz_code, operator_id, operator_name, action, diff_data) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(audit_sql, (table_name, biz_code, operator_id, operator_name, 'UPDATE', json.dumps(diff_data, ensure_ascii=False)))
        
        else:
            # 如果是新增记录，直接在审计表记一笔 "创建"
            audit_sql = """
                INSERT INTO sys_audit_logs (table_name, biz_code, operator_id, operator_name, action, diff_data) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(audit_sql, (table_name, biz_code, operator_id, operator_name, 'INSERT', json.dumps({"status": ["无", "首次创建数据"]}, ensure_ascii=False)))

        # ========================================================
        # 4. 物理写入：执行真正的 UPDATE 或 INSERT
        # ========================================================
        if record_id:
            set_clause = ', '.join([f'"{k}" = %s' for k in keys])
            sql = f'UPDATE "{table_name}" SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s'
            cursor.execute(sql, values + [record_id])
            msg = "更新成功 (已记录审计日志)"
        else:
            cols_str = ', '.join([f'"{k}"' for k in keys])
            placeholders = ', '.join(['%s'] * len(keys))
            sql = f'INSERT INTO "{table_name}" ({cols_str}) VALUES ({placeholders}) RETURNING id'
            cursor.execute(sql, values)
            msg = "新增成功"
            
        conn.commit()
        return True, msg
        
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def fetch_dynamic_records(model_name: str, keyword: str = "") -> pd.DataFrame:
    """
    [V2.0 终极通用查询引擎]
    使用原生连接 (conn) 替代 SQLAlchemy (sql_engine)，彻底解决参数类型报错。
    """
    
    model_config = cfg.get_model_config(model_name)
    table_name = model_config.get("table_name")
    field_meta = model_config.get("field_meta", {})
    
    if not table_name:
        print(f"🚨 模型 {model_name} 配置不存在！")
        return pd.DataFrame()
        
    conn = None
    try:
        # 🟢 获取原生 psycopg2 连接
        conn = get_connection()
        
        # 1. 基础 SQL
        query = f'SELECT * FROM "{table_name}" WHERE deleted_at IS NULL'
        params = []
        
        # 2. 动态模糊搜索
        if keyword:
            search_cols = []
            for col, meta in field_meta.items():
                if meta.get("is_virtual") is True:
                    continue
                    
                if meta.get("type", "text") == "text":
                    search_cols.append(f'"{col}" LIKE %s')
            
            if search_cols:
                where_clause = " OR ".join(search_cols)
                query += f" AND ({where_clause})"
                # 构造搜索参数
                params.extend([f"%{keyword}%"] * len(search_cols))
                
        query += ' ORDER BY updated_at DESC'
        
        # 3. 🟢 核心修复点：
        # A. 使用 conn 替换 sql_engine，绕过 SQLAlchemy 的严格检查。
        # B. 强制将 params 转换为 tuple。
        df = pd.read_sql_query(query, conn, params=tuple(params) if params else None)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            df = pd.read_sql_query(query, conn, params=tuple(params) if params else None)
        # 4. 应用计算公式
        df = core_logic.apply_business_formulas(df, model_name)                    
        return df

    except Exception as e:
        # 如果这里报错，测试脚本就会打印这句
        print(f"🚨 动态数据读取失败: {e}") 
        return pd.DataFrame()
    finally:
        # 🟢 确保原生连接被关闭
        if conn: conn.close()

def delete_dynamic_record(model_name: str, record_id: int):
    """V2.0 通用物理删除 (如果带有 biz_code，自动触发级联清理)"""
    model_config = cfg.get_model_config(model_name)
    table_name = model_config.get("table_name")
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 探测有没有 biz_code 或 sub_code
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
        # ... (由于篇幅限制，此处逻辑简化：因为我们在 custom_schema.py 设定了 ON DELETE CASCADE，
        # 所以在 V2.0 中，只要执行 DELETE FROM 主表，PG 底层会自动删掉 sys_project_flows 里相关联的数据！)
        
        cursor.execute(f'DELETE FROM "{table_name}" WHERE id = %s', (record_id,))
        conn.commit()
        return True, "物理删除成功，相关流水已自动级联清理"
    except Exception as e:
        if conn: conn.rollback()
        return False, f"删除失败: {e}"
    finally:
        if conn: conn.close()

def check_project_existence(biz_code=None, project_name=None):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        tables = get_all_data_tables()
        
        for table in tables:
            sql = f'SELECT biz_code, project_name, manager FROM "{table}" WHERE biz_code = %s OR project_name = %s'
            cursor.execute(sql, (biz_code, project_name))
            result = cursor.fetchone()
            if result:
                found_code, found_name, manager = result
                reason = "编号" if found_code == biz_code else "名称"
                return {
                    'exists': True,
                    'table': table,
                    'msg': f"⛔ 冲突：{reason}已在表 [{table}] 中存在（负责人：{manager}）"
                }
        return {'exists': False, 'msg': "✅ 该项目信息在全库中唯一"}
    except Exception as e:
        return {'exists': False, 'msg': f"检查失败: {str(e)}"}
    finally:
        if conn: conn.close()

def generate_biz_code(table_name, prefix_char="TMP"):
    """自动生成唯一临时编号 (biz_code 版)"""
    prefix = f"{prefix_char}{datetime.now().strftime('%Y%m%d')}"
    conn = None
    try:
        conn = get_connection()
        # 🟢 替换为 biz_code 和 %s
        query = f'SELECT biz_code FROM "{table_name}" WHERE biz_code LIKE %s ORDER BY biz_code DESC LIMIT 1'
        cursor = conn.cursor()
        cursor.execute(query, (f"{prefix}%",))
        row = cursor.fetchone()
        
        if row and row[0]:
            last_code = row[0]
            try:
                seq = int(last_code[-3:]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
            
        return f"{prefix}{seq:03d}"
    except Exception as e:
        print(f"自动编号生成失败: {e}")
        return f"{prefix}999" 
    finally:
        if conn: conn.close()