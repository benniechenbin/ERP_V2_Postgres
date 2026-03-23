import pandas as pd
from backend import database as db
from backend.config import config_manager as cfg

def get_global_kpi_stats() -> dict:
    """
    [核心业务逻辑] 获取系统全局大屏的 KPI 指标
    返回格式化的字典，方便任何前端 (Streamlit/Vue) 直接读取渲染。
    """
    config = cfg.load_data_rules()
    model_names = config.get("models", {}).keys()
    
    total_projects = 0
    total_contract = 0.0
    total_collection = 0.0
    recent_updates = []

    for m_name in model_names:
        df = db.fetch_dynamic_records(model_name=m_name)
        if not df.empty:
            total_projects += len(df)
            if 'contract_amount' in df.columns:
                total_contract += pd.to_numeric(df['contract_amount'], errors='coerce').fillna(0).sum()
            if 'total_collection' in df.columns:
                total_collection += pd.to_numeric(df['total_collection'], errors='coerce').fillna(0).sum()
            
            if 'updated_at' in df.columns:
                df['updated_at'] = pd.to_datetime(df['updated_at'], errors='coerce')
                df['model_label'] = m_name 
                name_col = 'project_name' if 'project_name' in df.columns else df.columns[1] 
                manager_col = 'manager' if 'manager' in df.columns else 'extra_props'
                
                top5 = df.nlargest(5, 'updated_at')[[name_col, manager_col, 'updated_at', 'model_label']]
                top5.columns = ['display_name', 'operator', 'update_time', 'source_model']
                recent_updates.append(top5)

    df_recent = pd.concat(recent_updates).nlargest(5, 'update_time') if recent_updates else pd.DataFrame()

    # 封装为标准 JSON/Dict 响应格式
    return {
        "total_projects": total_projects,
        "total_contract_amount": total_contract,
        "total_collected_amount": total_collection,
        "stock_amount": total_contract - total_collection, # 计算存量
        "collection_rate": (total_collection / total_contract * 100) if total_contract > 0 else 0.0,
        "recent_updates": df_recent # 未来可以通过 .to_dict('records') 传给 Vue
    }

def get_urgent_receivables() -> tuple[float, pd.DataFrame]:
    """获取 30 天内及已逾期的待收款计划 (预警雷达)"""
    # ... (待补充) ...
    pass