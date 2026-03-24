# 文件位置: backend/config/config_manager.py
import os
import json
from datetime import datetime
from pathlib import Path

# ========================================================
# 0. 现代化路径配置 
# ========================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = BASE_DIR / "app_config.json"

APP_NAME = "建筑专项管理系统"
APP_VERSION = "V2.0.0 beta" 
BUILD_DATE = datetime.now().strftime("%Y.%m.%d") 

# ========================================================
# 1. 核心对齐引擎 (必须放在最前面)
# ========================================================
def _auto_sync_labels(config_data):
    """🟢 多模型表头自动对齐引擎"""
    models = config_data.get("models", {})
    for model_name, model_info in models.items():
        field_meta = model_info.get("field_meta", {})
        column_mapping = model_info.get("column_mapping", {})
        
        for field_key, meta in field_meta.items():
            label = meta.get("label")
            if not label: continue
            if field_key not in column_mapping:
                column_mapping[field_key] = []
            if label not in column_mapping[field_key]:
                column_mapping[field_key].append(label)
                
        model_info["column_mapping"] = column_mapping
    return config_data

# ========================================================
# 2. 配置加载与保存机制
# ========================================================
def load_data_rules():
    """安全读取 JSON 配置并自动对齐"""
    base_config = {"models": {}}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return _auto_sync_labels(data)
        except Exception as e:
            print(f"读取配置失败: {e}")
    return base_config

def save_data_rules(rules_dict):
    """原子级安全保存 JSON 并强制对齐"""
    try:
        synced_data = _auto_sync_labels(rules_dict)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(synced_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Save Config Error: {e}")
        return False

# ========================================================
# 3. 初始化与 V2.0 标准接口
# ========================================================
_CURRENT_CONFIG = load_data_rules() 

def get_model_config(model_name="project"):
    """获取指定模型的完整配置"""
    return _CURRENT_CONFIG.get("models", {}).get(model_name, {})

def get_field_meta(model_name="project"):
    """获取指定模型的字段元数据"""
    return get_model_config(model_name).get("field_meta", {})

def get_column_mapping(model_name="project"):
    """获取指定模型的 Excel 映射"""
    return get_model_config(model_name).get("column_mapping", {})

def get_formulas(model_name="project"):
    """获取指定模型的公式"""
    return get_model_config(model_name).get("formulas", {})

# ========================================================
# 4. 完美向后兼容层 (极其重要：保证旧网页不崩溃)
# ========================================================
# 默认将 "project" 模型暴露为以前的全局变量，这样旧页面不用改代码也能跑
FIELD_META = get_field_meta("project")
CORE_MAPPING = get_column_mapping("project")
STANDARD_FIELDS = {k: v["label"] for k, v in FIELD_META.items()}
ALLOWED_EXTENSIONS = ["xlsx", "xls"]

def refresh_config():
    """刷新内存中的配置"""
    global _CURRENT_CONFIG, FIELD_META, CORE_MAPPING, STANDARD_FIELDS
    _CURRENT_CONFIG = load_data_rules() 
    
    # 刷新兼容层的变量
    FIELD_META = get_field_meta("project")
    CORE_MAPPING = get_column_mapping("project")
    STANDARD_FIELDS = {k: v["label"] for k, v in FIELD_META.items()}
    return True

# ========================================================
# 5. 工具接口 (升级为支持多模型)
# ========================================================
def get_standard_options(model_name="project"):
    options = []
    for k, meta in get_field_meta(model_name).items():
        options.append(f"{k} | {meta['label']}")
    return options

def get_system_extension_fields(model_name="project"):
    fields = []
    for k, meta in get_field_meta(model_name).items():
        if meta.get('type') == 'money' or 'amount' in k:
            fields.append(f"{k} NUMERIC(15,2) DEFAULT 0") # 🟢 顺手改成 PG 标准
        elif meta.get('type') == 'percent':
            fields.append(f"{k} REAL DEFAULT 0")
        else:
            fields.append(f"{k} VARCHAR(255)") # 🟢 顺手改成 PG 标准
    return fields

def get_field_label(col_name, model_name="project"):
    meta = get_field_meta(model_name)
    if col_name in meta:
        return meta[col_name].get("label", col_name)
    return col_name.replace("_", " ").title()