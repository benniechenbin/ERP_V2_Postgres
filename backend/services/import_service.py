import pandas as pd
import warnings
import json
from backend.services import excel_service
from backend.utils import formatters
from backend.database import db_engine, schema, crud
from backend.config import config_manager as cfg 
from backend import services as svc
from backend.utils.logger import sys_logger
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def run_import_process(
    uploaded_file,           
    target_sheet_name,       
    model_name,   
    manual_mapping=None,         
    import_mode="append",    
    relation_config=None,
    header_overrides=None,
    operator="System"
):
    """
    [V2.0 纯粹执行引擎] 只负责执行前端确认过的 manual_mapping
    """
    total_inserted = 0
    errors = []
    file_name = uploaded_file.name
    model_config = cfg.get_model_config(model_name)
    table_name = model_config.get("table_name")

    # A. 读取 Excel
    try:
        cleaned_data = excel_service.clean_excel(uploaded_file, header_overrides=header_overrides)
        target_item = next((item for item in cleaned_data if item['sheet_name'] == target_sheet_name), None)
        if not target_item: return False, f"找不到工作表: {target_sheet_name}"
        df = target_item['df']
    except Exception as e:
        return False, f"Excel 读取失败: {e}"

    if import_mode == 'overwrite':
        conn = None
        try:
            conn = db_engine.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM \"{table_name}\" WHERE extra_props->>'source_file' = %s AND extra_props->>'sheet_name' = %s", 
                (file_name, target_sheet_name)
            )
            conn.commit()
        except Exception as e:
            sys_logger.error(f"覆盖导入清理旧数据失败: {e}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
            
    # B. 逐行处理 (import_service.py)
    for idx, row in df.iterrows():
        row_data = {} 
        row_errors = [] 
        
        # 🟢 只遍历前端传过来的映射字典，完美实现“没勾选的直接抛弃”！
        if manual_mapping:
            for excel_col, target_key in manual_mapping.items():
                cell_val = row.get(excel_col)
                if pd.isna(cell_val) or str(cell_val).strip() == "": 
                    continue
                
                # 场景 1：明确指定存入 JSONB
                if target_key == "INTO_JSONB":
                    row_data[excel_col] = str(cell_val).strip()
                    continue
                    
                # 场景 2 & 3：物理列或新建列
                final_key = target_key
                
                # 智能清洗转换
                if any(k in final_key for k in ["amount", "collection", "额", "价"]):
                    row_data[final_key] = formatters.safe_float(cell_val)
                elif any(k in final_key for k in ["date", "日期", "时间"]):
                    row_data[final_key] = formatters.parse_date_cell(cell_val)
                else:
                    row_data[final_key] = str(cell_val).strip() 

        # --- C. 附属表严苛拦截 ---
        if relation_config:
            fk_excel_col = relation_config.get('fk_col')
            prime_table = relation_config.get('prime_table')
            fk_val = row.get(fk_excel_col)
            
            if pd.isna(fk_val) or not str(fk_val).strip():
                row_errors.append(f"缺少关联主合同编号(对应列: {fk_excel_col})")
            else:
                fk_val_str = str(fk_val).strip()
                if _verify_prime_id_exists(fk_val_str, prime_table):
                    row_data['parent_biz_code'] = fk_val_str 
                else:
                    row_errors.append(f"在主表 [{prime_table}] 中找不到合同编号 [{fk_val_str}]")

        # --- D. 自动生成业务编号 ---
        if not row_data.get('biz_code'):
            # 🟢 彻底告别写死！直接从配置文件读取 prefix，如果没有配置，默认兜底用 "PRJ"
            prefix = model_config.get("prefix", "PRJ")
            row_data['biz_code'] = crud.generate_biz_code(table_name, prefix_char=prefix)
            
        if row_errors:
            errors.append(f"第 {idx+2} 行被拦截: " + "；".join(row_errors))
            continue 

        # --- E. 呼叫写入引擎 ---
        row_data['source_file'] = file_name
        row_data['sheet_name'] = target_sheet_name

        # 直接入库，底层 crud 会完美接管所有不认识的字段！
        res, msg = crud.upsert_dynamic_record(model_name=model_name, data_dict=row_data)
        
        if res: 
            total_inserted += 1
        else: 
            errors.append(f"第{idx+2}行失败: {msg}")

    # ==========================================
    # 🟢 终极闭环：写入宏观任务日志 (sys_job_logs)
    # ==========================================
    fail_count = len(df) - total_inserted
    # 将 list 格式的 errors 转化为 dict 格式，方便存入 JSONB
    error_details_dict = {f"Error_{i+1}": err for i, err in enumerate(errors)} if errors else None
    
    try:
        crud.log_job_operation(
            operator=operator,
            file_name=file_name,
            import_type=model_name,
            success_count=total_inserted,
            fail_count=fail_count,
            error_details=error_details_dict
        )
    except Exception as log_e:
        sys_logger.warning(f"⚠️ 宏观日志记录失败 (不阻断主流程): {log_e}")

    # ==========================================
    # 返回结果拼装
    # ==========================================
    if errors:
        error_summary = "\n".join(errors[:5]) 
        if total_inserted > 0:
            return True, f"⚠️ 部分导入成功 ({total_inserted} 条)。\n拦截原因示例：\n{error_summary}"
        else:
            return False, f"❌ 导入失败，所有数据被拦截：\n{error_summary}"

    return True, f"✅ 导入成功，共写入 {total_inserted} 条。"

def _verify_prime_id_exists(biz_code, table_name):
    conn = None
    try:
        conn = db_engine.get_connection()
        cursor = conn.cursor()
        cursor.execute(f'SELECT 1 FROM "{table_name}" WHERE biz_code = %s', (str(biz_code),))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"验证主键失败: {e}")
        return False
    finally:
        if conn: conn.close()