import pandas as pd
from backend.config import config_manager as cfg
from backend.core import finance_engine



def apply_business_formulas(df: pd.DataFrame, model_name: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df
        
    df_result = df.copy()

    # 1. 挂载跨表财务数据 (确保数据已经转成 float)
    if model_name == 'main_contract':
        df_result = finance_engine.enrich_main_contract_stats(df_result)
    elif model_name == 'sub_contract':
        df_result = finance_engine.enrich_sub_contract_stats(df_result)

    # 2. 获取公式
    formulas = cfg.get_formulas(model_name)
    field_meta = cfg.get_field_meta(model_name)
    if not formulas: return df_result

    # 3. 🟢 预处理：无差别强转 float (增加对 "num" 的识别)
    for col in df_result.columns:
        f_type = field_meta.get(col, {}).get("type")
        # 关键修复：加入 "num" 类型判断
        is_numeric_meta = f_type in ["money", "percent", "num", "number"] 
        is_in_formula = any(col in str(f) for f in formulas.values())
        
        if is_numeric_meta or is_in_formula:
            df_result[col] = pd.to_numeric(df_result[col], errors='coerce').fillna(0.0)

    # 4. 执行公式
    for target_col, formula_str in formulas.items():
        try:
            # 🟢 使用 engine='python' 兼容性更好
            df_result[target_col] = df_result.eval(formula_str, engine='python')
        except Exception as e:
            print(f"⚠️ 公式执行失败 [{target_col} = {formula_str}]: {e}")
            df_result[target_col] = 0.0

    return df_result