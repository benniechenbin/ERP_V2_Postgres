# 文件位置: backend/services/analysis_service.py
import pandas as pd
from datetime import datetime
import json
# 🟢 接入数据库大本营
from backend.database import get_connection

def get_all_flows_dataframe():
    """
    [分析服务] 获取全库所有项目的资金流水
    用于：数据分析页面的图表渲染
    """
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT id, biz_code, amount, flow_date, stage, remark, source_table 
            FROM sys_project_flows 
            ORDER BY flow_date DESC
        """
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            df['flow_date'] = pd.to_datetime(df['flow_date'], errors='coerce')
            df['year'] = df['flow_date'].dt.year
            df['month'] = df['flow_date'].dt.month
            df['year_month'] = df['flow_date'].dt.strftime('%Y-%m')
            df = df.dropna(subset=['flow_date'])
        return df
    except Exception as e:
        print(f"🚨 全局流水提取失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

def get_financial_report(year=None):
    """
    [分析服务] 趋势分析：按月汇总收款金额
    返回列：period (YYYY-MM), monthly_amount
    """
    df = get_all_flows_dataframe()
    if df.empty:
        return pd.DataFrame(columns=['period', 'monthly_amount'])
    
    if year:
        df = df[df['year'] == int(year)]
    
    report = df.groupby('year_month', as_index=False)['amount'].sum()
    report = report.rename(columns={'year_month': 'period', 'amount': 'monthly_amount'})
    report = report.sort_values('period')
    return report

def _flatten_extra_props(df):
    """
    [核心机制] PostgreSQL JSONB 展平器
    如果 DataFrame 中存在 extra_props (字典形式)，将其键值对展开为独立的列。
    这样计算引擎就能拿到那些没有被固化为物理列的字段（如进度、起止日期）。
    """
    if 'extra_props' in df.columns:
        # 将字典列展开为一个新的 DataFrame
        # 注意：如果有缺失值，需要用空字典填补，防止 apply 报错
        props_df = df['extra_props'].apply(
            lambda x: x if isinstance(x, dict) else (json.loads(x) if isinstance(x, str) else {})
        ).apply(pd.Series)
        
        # 将展开的列合并回主表 (如果列名重复，保留物理列)
        for col in props_df.columns:
            if col not in df.columns:
                df[col] = props_df[col]
    return df

def calculate_project_timeline(df):
    """
    [核心计算] 清洗并推算项目的生命周期时间点
    """
    df = _flatten_extra_props(df) # 🟢 先把 JSONB 里的属性挖出来
    
    # 1. 确保有开始时间
    if 'start_date' not in df.columns:
        df['start_date'] = df.get('created_at', pd.NaT)
    df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    
    # 2. 确保有结束时间
    if 'end_date' not in df.columns:
        df['end_date'] = pd.NaT
    df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
    
    # 3. 动态补全逻辑
    mask_missing_end = df['end_date'].isna()
    if mask_missing_end.any():
        df.loc[mask_missing_end, 'end_date'] = df.loc[mask_missing_end, 'start_date'] + pd.Timedelta(days=90)
        
    # 4. 计算总工期
    df['duration_days'] = (df['end_date'] - df['start_date']).dt.days
    
    return df

def calculate_schedule_health(df):
    """
    [核心计算] 判定项目进度是否健康
    """
    df = _flatten_extra_props(df) # 🟢 展开 JSONB 获取 progress 等字段
    today = pd.Timestamp.now().normalize()
    
    def get_status(row):
        # 尝试从各种可能的名字中获取进度
        progress = row.get('progress', row.get('进度', 0)) 
        try:
            progress = float(progress)
        except:
            progress = 0
            
        if progress >= 100:
            return "✅ 已完成"
            
        end_date = row.get('end_date', pd.NaT)
        if pd.isna(end_date):
            return "⚪ 状态未知"
            
        days_left = (end_date - today).days
        
        if days_left < 0:
            return "🚨 严重延期"
        elif days_left < 15 and progress < 80:
            return "⚠️ 进度预警"
        else:
            return "🟢 正常推进"

    df['schedule_status'] = df.apply(get_status, axis=1)
    return df

def prepare_gantt_dataframe(df):
    """
    [计算引擎] 准备甘特图所需的数据结构
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df_copy = _flatten_extra_props(df.copy()) # 🟢 展开 JSONB
    
    if 'start_date' not in df_copy.columns:
        current_year = datetime.now().year
        df_copy['start_date'] = pd.to_datetime(f"{current_year}-01-01")
    else:
        df_copy['start_date'] = pd.to_datetime(df_copy['start_date'], errors='coerce')

    if 'end_date' not in df_copy.columns:
        df_copy['end_date'] = df_copy['start_date'] + pd.Timedelta(days=90)
    else:
        df_copy['end_date'] = pd.to_datetime(df_copy['end_date'], errors='coerce')

    df_copy['start_date'] = df_copy['start_date'].fillna(pd.to_datetime(datetime.now()))
    df_copy['end_date'] = df_copy['end_date'].fillna(df_copy['start_date'] + pd.Timedelta(days=90))

    return df_copy

def generate_gantt_data(df):
    """
    [前端适配器] 转化为甘特图标准 JSON
    """
    df_prepared = prepare_gantt_dataframe(df)
    
    if df_prepared.empty:
        return []

    gantt_list = []
    for _, row in df_prepared.iterrows():
        # 尝试获取进度和负责人
        progress_val = row.get('progress', row.get('进度', 0))
        try:
            progress_val = float(progress_val)
        except:
            progress_val = 0
            
        manager = row.get('manager', row.get('项目经理', row.get('负责人', '未分配')))

        gantt_list.append({
            "Task": row.get('project_name', row.get('项目名称', '未命名项目')),
            "Start": row['start_date'].strftime('%Y-%m-%d'),
            "Finish": row['end_date'].strftime('%Y-%m-%d'),
            "Resource": str(manager), 
            "Completion": progress_val * 100 if progress_val <= 1 else progress_val
        })
        
    return gantt_list