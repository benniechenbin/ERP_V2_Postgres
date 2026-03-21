import pandas as pd
import re
from datetime import datetime
import json
import os

from backend.config import config_manager

# =========================================================
# 模块 1: 表头识别与构建
# =========================================================
def suggest_header_row_by_density(df, scan_rows=15):
    """[表头识别] 通过扫描前 N 行非空字符串密度，推测表头行。"""
    best_idx, best_score = 0, -1
    max_scan = min(scan_rows, len(df))
    for i in range(max_scan):
        row = df.iloc[i]
        valid_cells = row.dropna()
        score = sum(1 for v in valid_cells if isinstance(v, (str, datetime)))
        if score > best_score: 
            best_score = score
            best_idx = i
    return best_idx

def _norm_text(s):
    """[文本标准化] 统一全角/半角符号并移除括号内容（兼容旧逻辑）。"""
    if s is None: return ""
    s = str(s).replace("（", "(").replace("）", ")").replace("：", ":")
    return re.sub(r"[（(].*?[）)]", "", s).strip()

def _safe_header_clean(val):
    """[表头清洗] 在保留括号内关键信息的前提下清洗表头。"""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    s = s.replace("\n", "_").replace("\r", "")
    s = s.replace("（", "(").replace("）", ")")
    s = s.replace("：", ":")
    s = re.sub(r'\s+', ' ', s)
    return s

def _build_headers(raw, header_idx):
    """[表头构建] 从指定表头行向上回溯，生成稳定列名。"""
    n_cols = raw.shape[1]
    headers = []
    for j in range(n_cols):
        final = ""
        for i in range(header_idx, -1, -1):
            cell = _safe_header_clean(raw.iloc[i, j])
            if cell: 
                final = cell
                break
        if not final: 
            final = f"未知列_{j}"
        headers.append(final)
    seen = {}
    uniq_headers = []
    for h in headers:
        if h not in seen:
            seen[h] = 0
            uniq_headers.append(h)
        else:
            seen[h] += 1
            uniq_headers.append(f"{h}_{seen[h]}")
    return uniq_headers

# =========================================================
# 模块 2: 数据清洗步骤
# =========================================================
def drop_fully_empty_rows(df):
    """[删除全空行] 去除整行皆为缺失值的记录。"""
    if df is None or df.empty: return df
    return df.dropna(how='all')

def drop_serial_number_columns(df):
    """[删除序号列] 移除仅用于展示顺序的无业务意义列。"""
    if df is None or df.empty: return df
    cfg = config_manager.load_data_rules().get("cleaning_rules", {})
    keywords = set([k.lower() for k in cfg.get("serial_number_keywords", ["序号", "no.", "s/n"])])
    cols_to_drop = []
    for col in df.columns:
        c_clean = str(col).strip().lower()
        if c_clean in keywords:
            cols_to_drop.append(col)
        elif c_clean.replace(".", "") in ["no", "sn", "id"] and len(str(col)) < 5: 
            cols_to_drop.append(col)
    if cols_to_drop:
        return df.drop(columns=cols_to_drop, errors='ignore')
    return df

def _ffill_attributes_only(df):
    """[前向填充] 仅对非金额属性列进行前向填充减少缺失。"""
    targets = []
    cfg = config_manager.load_data_rules().get("cleaning_rules", {})
    allow = cfg.get("allow_fill_keywords", ["部门", "日期", "状态"])
    deny = cfg.get("deny_fill_keywords", ["金额", "amount", "name", "名称"])
    for c in df.columns:
        n = str(c).lower().replace(" ", "")
        if any(x in n for x in allow) and not any(x in n for x in deny):
            targets.append(c)
    for c in targets:
        try: df[c] = df[c].ffill()
        except: pass
    return df

def drop_empty_name_and_code_rows(df):
    """[核心清洗] 删除无效行"""
    if df.empty:
        return df
    code_keywords = ["项目编号", "代码", "Code", "code", "ID", "id"]
    name_keywords = ["项目名称", "名字", "Name", "name", "项目", "Project"]
    target_cols = []
    for col in df.columns:
        c_str = str(col).strip()
        if any(k in c_str for k in code_keywords) or any(k in c_str for k in name_keywords):
            target_cols.append(col)
    if not target_cols:
        target_cols = df.columns.tolist()
    
    temp_df = df[target_cols].copy()
    temp_df = temp_df.replace(r'^\s*$', pd.NA, regex=True)
    valid_index = temp_df.dropna(how='all').index
    return df.loc[valid_index].copy()

def clean_cell_whitespace(df):
    """[去空格] 去除 DataFrame 中字符串值的首尾空格。"""
    return df.map(lambda x: x.strip() if isinstance(x, (str,)) else x)

def _trim_trailing_empty_rows(df):
    """[裁剪尾部空行] 去除末尾连续空白记录。"""
    if df.empty: return df
    last_idx = df.last_valid_index()
    if last_idx is None: return df.iloc[0:0] 
    return df.loc[:last_idx]

# =========================================================
# 模块 3: 清洗主入口
# =========================================================
def clean_excel(file_obj, strategies=None, header_overrides=None):
    """[清洗入口] 对 Excel 各 Sheet 依策略流水线清洗（支持表头覆盖）。"""
    if strategies is None:
        strategies = ['trim_tail', 'drop_empty', 'drop_serial', 'drop_invalid', 'clean_space']
    xls = pd.ExcelFile(file_obj)
    result = []
    for sheet in xls.sheet_names:
        raw = xls.parse(sheet_name=sheet, header=None)
        manual_idx = None
        if header_overrides and sheet in header_overrides:
            manual_idx = header_overrides[sheet]
        if manual_idx is not None:
            best_idx = manual_idx 
        else:
            best_idx = suggest_header_row_by_density(raw) 
        
        if best_idx < len(raw):
            headers = _build_headers(raw, best_idx)
            df = raw.iloc[best_idx+1:].copy()
            if len(df.columns) == len(headers):
                df.columns = headers
            else:
                df.columns = headers[:len(df.columns)]
        else:
            df = pd.DataFrame() 
            
        if 'trim_tail' in strategies:
            df = _trim_trailing_empty_rows(df)
        if 'drop_empty' in strategies:
            df = drop_fully_empty_rows(df)
        if 'drop_serial' in strategies:
            df = drop_serial_number_columns(df)
        if 'fill' in strategies:
            df = _ffill_attributes_only(df)
        if 'clean_space' in strategies:
            df = clean_cell_whitespace(df)
        result.append({"sheet_name": sheet, "df": df})
    return result

def smart_classify_header(header_name: str):
    mapping = config_manager.CORE_MAPPING
    clean_header = str(header_name).strip()
    
    for field_key, aliases in mapping.items():
        for alias in aliases:
            # 1. 精确匹配 (最高优先级)
            if alias == clean_header:
                return field_key
            
            # 2. 模糊匹配 (增加长度限制，防止误伤)
            if len(alias) >= 2 and alias in clean_header:
                return field_key
    return None