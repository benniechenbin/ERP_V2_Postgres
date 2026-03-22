import pandas as pd
from datetime import datetime
import re
import numpy as np
from decimal import Decimal

# ==========================================
# 📅 日期处理 (原 date_tools.py)
# ==========================================
def humanize_date(date_obj):
    """把日期变成人类喜欢的样子：2023-01-01 -> '2023年1月1日'"""
    if pd.isna(date_obj):
        return "-"
    try:
        return date_obj.strftime("%Y年%m月%d日")
    except:
        return str(date_obj)

def days_until(target_date):
    """计算距离某天还有多久。返回: (天数, 状态颜色)"""
    if pd.isna(target_date):
        return 0, "grey"
    today = pd.Timestamp.now().normalize()
    delta = (pd.to_datetime(target_date) - today).days
    if delta < 0: return delta, "red"
    elif delta < 7: return delta, "orange"
    else: return delta, "green"

def parse_date_cell(val):
    """
    [日期解析] 支持多格式解析并标准化为 YYYY-MM-DD。
    """
    if pd.isna(val) or str(val).strip() == '': return None
    if isinstance(val, (pd.Timestamp, datetime)): return val.strftime('%Y-%m-%d')
    s = str(val).strip()
    fmts = ['%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d', '%Y年%m月%d日', '%Y%m%d', '%Y.%m', '%Y年%m月']
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            if fmt in ['%Y.%m', '%Y年%m月']: return dt.strftime('%Y-%m-01')
            return dt.strftime('%Y-%m-%d')
        except: continue
    return None

# ==========================================
# 💰 金钱与数字格式化 (原 math_tools.py)
# ==========================================
def format_currency(amount):
    """将数字转换为金额格式，保留两位小数，千分位分隔。"""
    if amount is None or pd.isna(amount):
        return "¥0.00"
    try:
        val = float(amount)
        return f"¥{val:,.2f}"
    except (ValueError, TypeError):
        return "¥0.00"

def format_wan(amount):
    """建筑行业喜欢看'万元'。"""
    if amount is None or pd.isna(amount):
        return "0 万"
    try:
        val = float(amount) / 10000
        return f"{val:,.1f} 万"
    except:
        return "0 万"

def safe_float(value):
    """[终极版] 安全地将各种奇葩字符串转为浮点数。"""
    if pd.isna(value) or value is None or str(value).strip() == '':
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    is_negative = False
    if s.startswith('(') and s.endswith(')'):
        is_negative = True
        s = s[1:-1]
    s = s.replace('¥', '').replace('￥', '').replace('$', '').replace(',', '').replace(' ', '')
    unit = 1.0
    if '万' in s: 
        unit = 10000.0
        s = s.replace('万', '')
    elif '亿' in s: 
        unit = 100000000.0
        s = s.replace('亿', '')
    match = re.search(r'-?\d+\.?\d*', s)
    if match:
        final_val = float(match.group()) * unit
        return -final_val if is_negative else final_val
    else:
        return 0.0

# ==========================================
# 🧹 文本清洗 (原 str_tools.py)
# ==========================================
def clean_whitespace(text):
    """去掉字符串前后的空格，把中间的多个空格变成一个。"""
    if not isinstance(text, str):
        return text
    return " ".join(text.split())

def normalize_db_value(value):
    """
    [数据库安检门] 将各类复杂的 Numpy / Pandas / Decimal 类型
    强制收敛为 PostgreSQL 原生认识的 Python 基础类型。
    """
    import pandas as pd # 确保文件顶部有 import pandas as pd
    
    # 1. 拦截各种空值 (NaN, NaT, None) -> 转为数据库的原生 NULL
    if pd.isna(value) or value is None:
        return None
        
    # 2. 拦截 Numpy 整数 -> 转为原生 int
    if isinstance(value, (np.integer, int)):
        return int(value)
        
    # 3. 拦截 Numpy 浮点数、Decimal -> 转为原生 float
    if isinstance(value, (np.floating, float, Decimal)):
        return float(value)
        
    # 4. 拦截字符串 -> 去除首尾空格，且把纯空字符串转为 NULL
    if isinstance(value, str):
        val_str = value.strip()
        return val_str if val_str != "" else None
        
    return value