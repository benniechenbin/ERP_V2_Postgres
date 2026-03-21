import pandas as pd
import warnings
from backend.services import excel_service
from backend.utils import formatters
from backend.database import db_engine, schema, crud
from backend.config import config_manager as cfg 

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def run_import_process(
    uploaded_file,           
    target_sheet_name,       
    model_name,   
    manual_mapping=None,         
    import_mode="append",    
    relation_config=None,
    header_overrides=None    # 🟢 修正1：由前端作为参数安全传入
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
            conn = engine.get_connection()
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM "{table_name}" WHERE source_file = %s AND sheet_name = %s', 
                           (file_name, target_sheet_name))
            conn.commit()
        except Exception:
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
            
    # B. 逐行处理
    for idx, row in df.iterrows():
        row_data = {} 
        row_errors = [] # 🟢 修正2：补齐缺少的初始化
       
        # 🟢 修正3：彻底删除旧猜测逻辑，完全信任前端映射字典
        if manual_mapping:
            for excel_col, target_key in manual_mapping.items():
                cell_val = row.get(excel_col)
                if pd.isna(cell_val) or str(cell_val).strip() == "": 
                    continue
                
                final_key = excel_col if target_key == "NEW_PHYSICAL" else target_key
                
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
        if not row_data.get('biz_code') and model_name == 'project': 
            row_data['biz_code'] = crud.generate_biz_code(table_name)
            
        if row_errors:
            errors.append(f"第 {idx+2} 行被拦截: " + "；".join(row_errors))
            continue 

        # --- E. 呼叫写入引擎 ---
        row_data['source_file'] = file_name
        row_data['sheet_name'] = target_sheet_name

        res, msg = crud.upsert_dynamic_record(model_name=model_name, data_dict=row_data)
        if res: total_inserted += 1
        else: errors.append(f"第{idx+2}行失败: {msg}")

    # 返回结果拼装
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
        conn = engine.get_connection()
        cursor = conn.cursor()
        cursor.execute(f'SELECT 1 FROM "{table_name}" WHERE biz_code = %s', (str(biz_code),))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"验证主键失败: {e}")
        return False
    finally:
        if conn: conn.close()