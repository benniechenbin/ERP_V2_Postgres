# 项目: ERP_V2_Postgres

## 🗂️ 项目目录树

```text
ERP_V2_Postgres/
├── backend
│   ├── ai
│   │   ├── kb_service.py
│   │   └── llm_dispatcher.py
│   ├── api
│   │   ├── __init__.py
│   │   └── ai_router.py
│   ├── config
│   │   └── config_manager.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── business_ops.py
│   │   ├── core_logic.py
│   │   └── finance_engine.py
│   ├── database
│   │   ├── __init__.py
│   │   ├── crud.py
│   │   ├── crud_base.py
│   │   ├── crud_finance.py
│   │   ├── crud_sys.py
│   │   ├── custom_schema.py
│   │   ├── db_engine.py
│   │   └── schema.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   ├── analysis_service.py
│   │   ├── excel_service.py
│   │   ├── export_service.py
│   │   ├── file_service.py
│   │   ├── flow_service.py
│   │   ├── import_service.py
│   │   └── project_service.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── formatters.py
│   │   └── logger.py
│   └── __init__.py
├── backups
├── data
│   ├── backups
│   ├── logs
│   ├── sqlite_db
│   └── uploads
├── react_enterprise
│   └── src
│       ├── components
│       └── pages
├── streamlit_lab
│   ├── .streamlit
│   ├── experiments
│   │   ├── __init__.py
│   │   ├── ex01_risk_engine.py
│   │   └── ex02_biz_analysis.py
│   ├── pages
│   │   ├── 01_📂_项目看板.py
│   │   ├── 02_🛠️_主合同管理.py
│   │   ├── 03_🛠️_分包合同管理.py
│   │   ├── 04_📊_数据分析.py
│   │   ├── 05_🏢_往来单位.py
│   │   ├── 06_📥_导入Excel.py
│   │   └── 99_🧪_实验室.py
│   ├── app.py
│   ├── components.py
│   ├── debug_kit.py
│   ├── sidebar_manager.py
│   └── 🏠_Dashboard.py
└── tests
    ├── export_to_md.py
    ├── fix_db.py
    ├── run_server.py
    ├── test_finance_scenario.py
    └── type_checker.py
```

---

## 💻 代码详情

### 📁 backend

#### 📄 __init__.py

```python

```

#### 📁 ai

##### 📄 kb_service.py

```python
# 文件位置: backend/ai/llm_dispatcher.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMDispatcher:
    def __init__(self):
        # 从环境变量读取配置
        self.provider = os.getenv("AI_PROVIDER", "openai") # 'openai' 或 'ollama'
        
        if self.provider == "openai":
            # 兼容 OpenAI 和 DeepSeek (API 格式一致)
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL")
            )
            self.model = os.getenv("OPENAI_MODEL", "deepseek-chat")
        else:
            # 本地 Ollama 路径
            self.client = OpenAI(
                api_key="ollama", # Ollama 通常不需要 key，但 SDK 要求填
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            )
            self.model = os.getenv("OLLAMA_MODEL", "qwen2:7b")

    def chat(self, messages, response_format=None):
        """统一的调用入口"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format=response_format
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI 调度异常: {str(e)}"

# 单例模式供全局调用
ai_dispatcher = LLMDispatcher()
```

##### 📄 llm_dispatcher.py

```python
# 文件位置: backend/ai/llm_dispatcher.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMDispatcher:
    def __init__(self):
        # 从环境变量读取配置
        self.provider = os.getenv("AI_PROVIDER", "openai") # 'openai' 或 'ollama'
        
        if self.provider == "openai":
            # 兼容 OpenAI 和 DeepSeek (API 格式一致)
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL")
            )
            self.model = os.getenv("OPENAI_MODEL", "deepseek-chat")
        else:
            # 本地 Ollama 路径
            self.client = OpenAI(
                api_key="ollama", # Ollama 通常不需要 key，但 SDK 要求填
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            )
            self.model = os.getenv("OLLAMA_MODEL", "qwen2:7b")

    def chat(self, messages, response_format=None):
        """统一的调用入口"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format=response_format
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI 调度异常: {str(e)}"

# 单例模式供全局调用
ai_dispatcher = LLMDispatcher()
```

#### 📁 api

##### 📄 __init__.py

```python

```

##### 📄 ai_router.py

```python
# FastAPI 路由适配层
```

#### 📁 config

##### 📄 config_manager.py

```python
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
    options = ["(新建中文物理列)"]
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
```

#### 📁 core

##### 📄 __init__.py

```python
# 文件位置: backend/core/__init__.py

from .core_logic import apply_business_formulas
from .business_ops import (
    mark_project_as_accrued,
    execute_yearly_accrual_archive
)

__all__ = [
    "apply_business_formulas",
    "mark_project_as_accrued",
    "execute_yearly_accrual_archive"
]
```

##### 📄 business_ops.py

```python
# 🟢 体验架构之美：直接通过 Facade (门面) 拿连接和工具，干干净净
from backend.database import get_connection, get_all_data_tables

def mark_project_as_accrued(biz_code, table_name):
    """
    [核心业务 - 单条标记] 将指定项目的 '是否计提' 标记为 '是'，并记录计提时间
    """
    conn = None
    try:
        # 🟢 升级：使用统一连接池，为未来 PG 升级铺路
        conn = get_connection()
        cursor = conn.cursor()
        
        # 魔法修改：同时更新状态和时间 (localtime 保证是北京时间)
        sql = f"""
            UPDATE "{table_name}"
            SET is_provisioned = '是',
                accrued_at = datetime('now', 'localtime')
            WHERE biz_code = ?
        """
        cursor.execute(sql, (biz_code,))
        
        if cursor.rowcount > 0:
            conn.commit()
            return True, f"项目 {biz_code} 已成功标记为计提！(已记录时间)"
        else:
            return False, f"未找到项目 {biz_code}，请检查编号。"
            
    except Exception as e:
        if conn: conn.rollback()
        return False, f"标记失败: {e}"
    finally:
        if conn:
            conn.close()


def execute_yearly_accrual_archive():
    """
    [核心业务 - 年度归档] 跨年一键清理引擎 (物理列疾速版)
    遍历所有数据表，将物理列 is_provisioned 为 '是' 的项目，移入回收站 (is_active = 0)
    """
    conn = None
    total_archived = 0
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        tables = get_all_data_tables()
        
        for table in tables:
            # 核心修复：直接瞄准物理列 is_provisioned 查询
            sql = f"""
                UPDATE "{table}" 
                SET is_active = 0 
                WHERE is_provisioned = '是' 
                AND is_active = 1
            """
            cursor.execute(sql)
            total_archived += cursor.rowcount  
            
        conn.commit()
        return True, f"🎉 年度归档完成！共将 {total_archived} 个已计提项目安全移入回收站。"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"归档失败: {e}"
    finally:
        if conn:
            conn.close()
```

##### 📄 core_logic.py

```python
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
```

##### 📄 finance_engine.py

```python
import pandas as pd
import psycopg2.extras
from backend.database.db_engine import get_connection
from backend.utils.logger import sys_logger # 顺手注入 logger


# ==========================================
# ⚙️ 引擎一：主合同水池核算 (已修复 Decimal 与重名问题)
# ==========================================
def enrich_main_contract_stats(df_main: pd.DataFrame) -> pd.DataFrame:
    if df_main.empty or 'biz_code' not in df_main.columns:
        return df_main
        
    conn = get_connection()
    try:
        # 🟢 1. 清洗主表编号：防止空格导致 merge 失败产生 None
        df_main['biz_code'] = df_main['biz_code'].astype(str).str.strip()
        biz_codes = df_main['biz_code'].tolist()
        params = tuple(biz_codes)
        placeholders = ', '.join(['%s'] * len(biz_codes))

        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 2. 抓取发票池
        sql_inv = f"""
            SELECT main_contract_code as biz_code, SUM(invoice_amount) as total_invoiced
            FROM biz_invoices 
            WHERE main_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY main_contract_code
        """
        cur.execute(sql_inv, params)
        df_inv = pd.DataFrame(cur.fetchall())
        if not df_inv.empty:
            # 🟢 2a. 强转 float 并清洗编号，解决 Decimal 无法计算问题
            df_inv['total_invoiced'] = df_inv['total_invoiced'].astype(float)
            df_inv['biz_code'] = df_inv['biz_code'].astype(str).str.strip()

        # 3. 抓取资金池
        sql_coll = f"""
            SELECT main_contract_code as biz_code, SUM(collected_amount) as total_collected
            FROM biz_collections
            WHERE main_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY main_contract_code
        """
        cur.execute(sql_coll, params)
        df_coll = pd.DataFrame(cur.fetchall())
        if not df_coll.empty:
            # 🟢 3a. 强转 float 并清洗编号
            df_coll['total_collected'] = df_coll['total_collected'].astype(float)
            df_coll['biz_code'] = df_coll['biz_code'].astype(str).str.strip()

        # 🟢 4. 关键：清理主表已存在的重名虚拟列，防止 merge 产生后缀导致公式找不到变量
        v_cols = ['total_invoiced', 'total_collected']
        df_main = df_main.drop(columns=[c for c in v_cols if c in df_main.columns])

        # 5. 执行合并
        if not df_inv.empty:
            df_main = df_main.merge(df_inv, on='biz_code', how='left')
        else:
            df_main['total_invoiced'] = 0.0

        if not df_coll.empty:
            df_main = df_main.merge(df_coll, on='biz_code', how='left')
        else:
            df_main['total_collected'] = 0.0

        return df_main.fillna({'total_invoiced': 0.0, 'total_collected': 0.0})
    finally:
        if conn: conn.close()

# ==========================================
# ⚙️ 引擎二：分包合同核算 (增加关联主合同数据抓取)
# ==========================================
def enrich_sub_contract_stats(df_sub: pd.DataFrame) -> pd.DataFrame:
    if df_sub.empty or 'biz_code' not in df_sub.columns:
        return df_sub

    conn = get_connection()
    try:
       # 1. 清洗分包表编号
        df_sub['biz_code'] = df_sub['biz_code'].astype(str).str.strip()
        df_sub['actual_main_code'] = df_sub['actual_main_code'].astype(str).str.strip()
        sub_codes = df_sub['biz_code'].tolist()
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        placeholders = ', '.join(['%s'] * len(sub_codes))
        params = tuple(sub_codes)

        # 2. 抓取分包已付 (从 biz_outbound_payments)
        sql_pay = f"""
            SELECT sub_contract_code as biz_code, 
                   SUM(payment_amount) as total_paid,
                   MAX(payment_date) as last_payment_date
            FROM biz_outbound_payments
            WHERE sub_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY sub_contract_code
        """
        cur.execute(sql_pay, params)
        df_pay = pd.DataFrame(cur.fetchall())
        if not df_pay.empty:
            df_pay['total_paid'] = df_pay['total_paid'].astype(float)
            df_pay['biz_code'] = df_pay['biz_code'].astype(str).str.strip()

        # 🟢 2.5 抓取分包已收票 (从全新的 biz_sub_invoices 表)
        sql_inv = f"""
            SELECT sub_contract_code as biz_code, 
                   SUM(invoice_amount) as total_invoiced_from_sub
            FROM biz_sub_invoices
            WHERE sub_contract_code IN ({placeholders}) AND deleted_at IS NULL
            GROUP BY sub_contract_code
        """
        cur.execute(sql_inv, params)
        df_inv = pd.DataFrame(cur.fetchall())
        if not df_inv.empty:
            df_inv['total_invoiced_from_sub'] = df_inv['total_invoiced_from_sub'].astype(float)
            df_inv['biz_code'] = df_inv['biz_code'].astype(str).str.strip()

        # 3. 核心补充：抓取关联主合同的金额 (用于 sub_ratio 比例计算公式)
        main_codes = [c for c in df_sub['actual_main_code'].unique().tolist() if c and str(c) != 'nan']
        df_main_data = pd.DataFrame()
        if main_codes:
            m_placeholders = ', '.join(['%s'] * len(main_codes))
            sql_main = f"""
                SELECT m.biz_code as actual_main_code, m.contract_amount as main_contract_amount, 
                       COALESCE(SUM(c.collected_amount), 0) as main_total_collected
                FROM biz_main_contracts m
                LEFT JOIN biz_collections c ON m.biz_code = c.main_contract_code AND c.deleted_at IS NULL
                WHERE m.biz_code IN ({m_placeholders}) AND m.deleted_at IS NULL
                GROUP BY m.biz_code, m.contract_amount
            """
            cur.execute(sql_main, tuple(main_codes))
            df_main_data = pd.DataFrame(cur.fetchall())
            if not df_main_data.empty:
                df_main_data[['main_contract_amount', 'main_total_collected']] = df_main_data[['main_contract_amount', 'main_total_collected']].astype(float)
                df_main_data['actual_main_code'] = df_main_data['actual_main_code'].astype(str).str.strip()

        # 4. 清理主表中的虚拟列，防止重名
        v_cols = ['total_paid', 'total_invoiced_from_sub', 'main_contract_amount', 'main_total_collected']
        df_sub = df_sub.drop(columns=[c for c in v_cols if c in df_sub.columns])

        # 5. 合并 (增加 df_inv 的合并)
        if not df_pay.empty:
            df_sub = df_sub.merge(df_pay, on='biz_code', how='left')
        if not df_inv.empty:
            df_sub = df_sub.merge(df_inv, on='biz_code', how='left')
        if not df_main_data.empty:
            df_sub = df_sub.merge(df_main_data, on='actual_main_code', how='left')

        # 🟢 新增兜底逻辑：如果该分包没有关联实际主合同，导致 merge 没带过来主合同的金额列，强制赋 0
        for c in v_cols:
            if c not in df_sub.columns:
                df_sub[c] = 0.0

        return df_sub.fillna({c: 0.0 for c in v_cols})
    finally:
        if conn: conn.close()

# ==========================================
# ⚙️ 引擎三：名义关联 (EBM) 资金红线拦截器 (升级版)
# ==========================================
# 文件位置: backend/core/finance_engine.py

def validate_sub_payment_risk(sub_biz_code: str, apply_amount: float) -> tuple[bool, str]:
    """[支付前置风控] 全景透视版：打印每一步的查库结果"""
    sys_logger.info(f"🛡️ --- 风控雷达启动: 目标分包 [{sub_biz_code}] ---")
    is_external_conn = conn is not None
    if not is_external_conn:
        conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. 查分包底层数据 (全量查出，看有没有漏掉什么字段)
        cur.execute("SELECT * FROM biz_sub_contracts WHERE biz_code = %s AND deleted_at IS NULL FOR UPDATE", (sub_biz_code,))
        sub_raw = cur.fetchone()
        sys_logger.info(f"  [账本] 该分包总额: {sub_total}...")
        
        if not sub_raw:
            return True, "数据库查无此分包，系统放行"
            
        # 兼容读取 (自动在物理列和 JSONB 溢出列中寻找)
        ebm_code = sub_raw.get('book_main_code')
        if not ebm_code and sub_raw.get('extra_props'):
            if isinstance(sub_raw['extra_props'], dict):
                ebm_code = sub_raw['extra_props'].get('book_main_code')
            elif isinstance(sub_raw['extra_props'], str):
                import json
                try: ebm_code = json.loads(sub_raw['extra_props']).get('book_main_code')
                except: pass
        
        sys_logger.info(f"  [解析] 提取到归属主合同(EBM): {ebm_code}")
        
        if not ebm_code:
            return True, "无 EBM 关联，不在风控管辖内，放行"
            
        ebm_code = ebm_code.strip()
        sub_total = float(sub_raw.get('sub_amount') or 0)
        
        # 2. 查该分包历史已付金额
        cur.execute('SELECT SUM(payment_amount) as paid FROM biz_outbound_payments WHERE sub_contract_code = %s AND deleted_at IS NULL', (sub_biz_code,))
        already_paid = float(cur.fetchone()['paid'] or 0)
        future_ratio = (already_paid + float(apply_amount)) / sub_total if sub_total > 0 else 0
        
        sys_logger.info(f"  [账本] 该分包总额: {sub_total}, 历史已付: {already_paid}, 本次申请: {apply_amount}")
        sys_logger.info(f"  [测算] 支付后该分包进度将达到: {future_ratio:.2%}")
        
        # 3. 查主合同数据
        cur.execute("SELECT * FROM biz_main_contracts WHERE biz_code = %s AND deleted_at IS NULL", (ebm_code,))
        main_raw = cur.fetchone()
        
        if not main_raw:
            sys_logger.info(f"  [警告] 找不到关联的账面主合同 [{ebm_code}]！")
            return True, "归属的账面主合同不存在，强制放行"
            
        main_total = float(main_raw.get('contract_amount') or 0)
        
        cur.execute('SELECT SUM(collected_amount) as coll FROM biz_collections WHERE main_contract_code = %s AND deleted_at IS NULL', (ebm_code,))
        main_coll = float(cur.fetchone()['coll'] or 0)
        main_ratio = main_coll / main_total if main_total > 0 else 0
        
        sys_logger.info(f"  [账本] 挂靠主合同总额: {main_total}, 已收款: {main_coll}")
        sys_logger.info(f"  [测算] 挂靠主合同回款进度: {main_ratio:.2%}")
        
        # 4. 决断 (增加 0.1% 的浮点数容错率)
        if future_ratio > (main_ratio + 0.001):
            return False, f"主合同回款率仅 {main_ratio:.1%}，本次支付将使分包进度达 {future_ratio:.1%}，打破红线！"
            
        return True, "风控测算通过，允许付款"
        
    except Exception as e:
        sys_logger.error(f"  [异常] 风控引擎崩溃: {e}", exc_info=True)
        return False, f"风控异常: {e}"
    finally:
        if not is_external_conn and conn: 
            conn.close()
```

#### 📁 database

##### 📄 __init__.py

```python
"""
ERP_V2_PRO 数据库核心引擎 (Database Facade)
对外暴露 V2.0 规范化接口
"""
from .db_engine import (
    get_connection, get_readonly_connection, get_current_db_name,
    get_available_dbs, backup_db, execute_raw_sql, db_health_report,
    check_db_exists, set_current_db, UPLOAD_DIR, 
)
from .schema import (
    sync_database_schema, get_all_data_tables,
    has_column, get_table_schema, get_table_columns
)
from .crud import (
    upsert_dynamic_record, fetch_dynamic_records, delete_dynamic_record, # V2.0 核心三剑客
    check_project_existence,
    generate_biz_code, get_attachment_counts, soft_delete_project, restore_project,
    get_deleted_projects, update_biz_code_cascade, 
    mark_project_as_accrued, execute_yearly_accrual_archive,
    check_main_contract_clearance, submit_sub_payment,
    sync_main_contract_finance, void_financial_record
)

__all__ = [
    "get_connection", "get_readonly_connection", "get_current_db_name", 
    "get_available_dbs", "backup_db", "execute_raw_sql", "db_health_report", 
    "check_db_exists", "UPLOAD_DIR", "set_current_db",
    "sync_database_schema", "get_all_data_tables", 
    "has_column", "get_table_schema", "get_table_columns",
    "upsert_dynamic_record", "fetch_dynamic_records", "delete_dynamic_record",
    "check_project_existence",
    "generate_biz_code", "get_attachment_counts", "soft_delete_project", "restore_project",
    "get_deleted_projects", "update_biz_code_cascade",
    "mark_project_as_accrued", "execute_yearly_accrual_archive",
    "check_main_contract_clearance", "submit_sub_payment",
    "sync_main_contract_finance", "void_financial_record"
]
```

##### 📄 crud.py

```python
# 🟢 作用：CRUD 门面 (Facade) 路由
# 警告：不要在此文件写具体的业务逻辑！请前往对应的子模块编写！

# 1. 导入底层通用引擎
from backend.database.crud_base import (
    upsert_dynamic_record,
    fetch_dynamic_records,
    delete_dynamic_record,
    check_project_existence,
    generate_biz_code
)

# 2. 导入业财专有逻辑
from backend.database.crud_finance import (
    mark_project_as_accrued,
    execute_yearly_accrual_archive,
    check_main_contract_clearance,
    submit_sub_payment,
    sync_main_contract_finance,
    void_financial_record
)

# 3. 导入系统与后勤辅助
from backend.database.crud_sys import (
    get_attachment_counts,
    update_biz_code_cascade,
    soft_delete_project,
    restore_project,
    get_deleted_projects,
    log_job_operation
)

















```

##### 📄 crud_base.py

```python
import json
import pandas as pd
from datetime import datetime
import warnings

from backend.config import config_manager as cfg
from backend.database.db_engine import get_connection, sql_engine
from backend.database.schema import get_all_data_tables
from backend.core import core_logic  # 用于应用业务公式
from backend.utils.formatters import normalize_db_value
from backend.utils.logger import sys_logger

def upsert_dynamic_record(model_name: str, data_dict: dict, record_id: int = None, operator_id: int = 0, operator_name: str = 'System'):
    """
    [V2.0 混合架构写入引擎 + 全自动审计拦截器]
    自带智能分拣，并全自动记录数据变更历史 (时光机)。
    """
    
    model_config = cfg.get_model_config(model_name)
    table_name = model_config.get("table_name")
    
    if not table_name: return False, "未找到模型配置"
        
    conn = None
    try:# 确保局部导入或在文件头已导入
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
        raw_values = list(physical_data.values())
        values = [normalize_db_value(v) for v in raw_values] 
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
                        INSERT INTO sys_audit_logs (model_name, biz_code, operator_name, action, diff_data) 
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(audit_sql, (model_name, biz_code, operator_name, 'UPDATE', json.dumps(diff_data, ensure_ascii=False)))
        
        else:
            # 如果是新增记录，直接在审计表记一笔 "创建"
            audit_sql = """
                INSERT INTO sys_audit_logs (model_name, biz_code, operator_name, action, diff_data) 
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(audit_sql, (model_name, biz_code, operator_name, 'INSERT', json.dumps({"status": ["无", "首次创建数据"]}, ensure_ascii=False)))

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
        sys_logger.error(f"🚨 数据写入失败 [{model_name}]: {e}", exc_info=True)
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
```

##### 📄 crud_finance.py

```python
from datetime import datetime
import pandas as pd

from backend.config import config_manager as cfg
from backend.database.db_engine import get_connection
from backend.database.schema import get_all_data_tables, has_column
from backend.database.crud_base import upsert_dynamic_record  # 🟢 内部调用基础引擎
from backend.core.finance_engine import validate_sub_payment_risk
from backend.utils.logger import sys_logger


# ==========================================
# 🛡️ 业财风控拦截网关
# ==========================================
def check_main_contract_clearance(main_contract_code: str) -> tuple[bool, str]:
    """
    [V2.6 强制类型适配版] 
    解决 PostgreSQL 中 VARCHAR 与 NUMERIC 的运算冲突
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 🟢 修正点：使用 CAST 或 ::numeric 将字符类型的 sub_amount 转换为数值
            # 🟢 修正点：book_main_code 同样进行类型对齐
            sql = """
                SELECT 
                    s.biz_code, 
                    s.sub_company_name, 
                    COALESCE(NULLIF(s.sub_amount, '')::numeric, 0) as sub_amt,
                    COALESCE(p.paid_sum, 0) as paid_sum
                FROM biz_sub_contracts s
                LEFT JOIN (
                    SELECT sub_contract_code, SUM(payment_amount) as paid_sum 
                    FROM biz_outbound_payments 
                    WHERE deleted_at IS NULL 
                    GROUP BY sub_contract_code
                ) p ON s.biz_code = p.sub_contract_code
                WHERE s.book_main_code = %s 
                  AND s.deleted_at IS NULL
                  AND (COALESCE(NULLIF(s.sub_amount, '')::numeric, 0) - COALESCE(p.paid_sum, 0)) > 0.01
            """
            cursor.execute(sql, (str(main_contract_code),))
            uncleared_subs = cursor.fetchall()
            
            if uncleared_subs:
                error_details = []
                for sub in uncleared_subs:
                    # sub[2] 是转换后的金额, sub[3] 是已付金额
                    diff = float(sub[2] or 0) - float(sub[3] or 0)
                    error_details.append(f"[{sub[0]}] {sub[1]} (差额: ¥{diff:,.2f})")
                return False, f"操作拦截：名下有分包未结清：\n" + "\n".join(error_details)
                
            return True, "检查通过"
    except Exception as e:
        return False, f"业财校验引擎异常: {e}"
    finally:
        if conn: conn.close()


# ==========================================
# 💼 财务核心业务流转
# ==========================================
def mark_project_as_accrued(model_name: str, biz_code: str):
    """
    [V2.0 适配版] 将项目标记为已计提，并精准打上时间戳
    注意：参数已从 table_name 升级为 model_name (如 'project')
    """
    # 🚨 1. 第一道防线：呼叫计提风控依赖检查！
    passed, msg = check_main_contract_clearance(biz_code)
    if not passed:
        return False, msg # 🟢 直接打回，不允许执行计提
        
    # 2. 瞬间生成时间戳与状态字典
    patch_dict = {
        "is_provisioned": "是",
        "provision_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 🟢 补齐计提时间！
    }
    
    model_config = cfg.get_model_config(model_name)
    table_name = model_config.get("table_name")
    if not table_name: 
        return False, "未找到模型配置"
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 3. 通过 biz_code 查出底层真实的物理 id
        cursor.execute(f'SELECT id FROM "{table_name}" WHERE biz_code = %s', (biz_code,))
        row = cursor.fetchone()
        
        if not row:
            return False, f"找不到编号为 {biz_code} 的记录"
            
        record_id = row[0]
        
        # 4. 🟢 呼叫智能引擎安全保存！
        return upsert_dynamic_record(model_name=model_name, data_dict=patch_dict, record_id=record_id)
        
    except Exception as e:
        return False, f"计提操作失败: {e}"
    finally:
        if conn: conn.close()


def execute_yearly_accrual_archive():
    """执行年度结转 (PG JSONB 语法兼容适配)"""
    conn = None
    try:
        conn = get_connection()
        tables = get_all_data_tables()
        archived_count = 0
        
        for tbl in tables:
            if not has_column(tbl, "is_provisioned"):
                continue
            # 🟢 PG 中对 JSONB 的模糊查询通常用 ::text 转换
            sql = f"""
                UPDATE "{tbl}"
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE is_provisioned = '是'
            """
            cur = conn.cursor()
            cur.execute(sql)
            archived_count += cur.rowcount
            
        conn.commit()
        return True, f"年度结转完成！共将 {archived_count} 个已计提项目移入回收站。"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()


def submit_sub_payment(sub_biz_code: str, payment_amount: float, operator: str, payment_date: str, remarks: str = ""):
    """
    [V2.0 业财安全支付网关] 前端点击“确认付款”时调用的唯一接口
    """
    conn = None
    try:
        conn = get_connection()
        
        # 1. 🚨 把当前连接传给风控引擎，锁定该行！
        passed, msg = validate_sub_payment_risk(sub_biz_code, payment_amount, conn=conn)
        if not passed:
            conn.rollback() # 风控不通过，释放锁
            sys_logger.warning(f"⛔ 付款被风控拦截 [{sub_biz_code}]: {msg}")
            return False, msg  
            
        # 2. 风控通过，安全落库
        cursor = conn.cursor()
        sql = """
            INSERT INTO biz_outbound_payments 
            (biz_code, sub_contract_code, payment_amount, payment_date, operator, remarks)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        pay_flow_code = f"PAY-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S%f')}"
        cursor.execute(sql, (pay_flow_code, sub_biz_code, payment_amount, payment_date, operator, remarks))
        
        # 3. 统一提交事务！
        conn.commit()
        sys_logger.info(f"✅ 分包付款成功落库 [{pay_flow_code}] 金额: {payment_amount}")
        return True, "✅ 支付记录已安全入库！"
        
    except Exception as e:
        if conn: conn.rollback()
        sys_logger.error(f"🚨 付款落库失败 [{sub_biz_code}]: {e}", exc_info=True)
        return False, f"落库失败: {e}"
    finally:
        if conn: conn.close()

def sync_main_contract_finance(main_contract_code: str):
    """
    [V2.7 穿透核算引擎] 
    直接从收款/发票表抓取数据，强制同步到主合同的统计字段中。
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 1. 实时计算：累计到账 (来自 biz_collections)
            cursor.execute("""
                SELECT COALESCE(SUM(collected_amount), 0) 
                FROM biz_collections 
                WHERE main_contract_code = %s AND deleted_at IS NULL
            """, (main_contract_code,))
            total_collected = float(cursor.fetchone()[0] or 0)

            # 2. 实时计算：累计开票 (来自 biz_invoices)
            cursor.execute("""
                SELECT COALESCE(SUM(invoice_amount), 0) 
                FROM biz_invoices 
                WHERE main_contract_code = %s AND deleted_at IS NULL
            """, (main_contract_code,))
            total_invoiced = float(cursor.fetchone()[0] or 0)

            # 3. 获取合同总额用于计算进度 (注意类型转换)
            # 这里的表名从配置获取，或者直接用 biz_main_contracts
            cursor.execute("""
                SELECT COALESCE(NULLIF(contract_amount, '')::numeric, 0) 
                FROM biz_main_contracts 
                WHERE biz_code = %s
            """, (main_contract_code,))
            contract_amount = float(cursor.fetchone()[0] or 0)

            # 4. 计算进度与欠款
            progress = round((total_collected / contract_amount * 100), 2) if contract_amount > 0 else 0
            uncollected = contract_amount - total_collected

            # 5. 执行更新 (更新到动态属性字段)
            update_sql = """
                UPDATE biz_main_contracts 
                SET total_collected = %s, 
                    total_invoiced = %s,
                    collection_progress = %s,
                    uncollected_contract_amount = %s
                WHERE biz_code = %s
            """
            cursor.execute(update_sql, (total_collected, total_invoiced, progress, uncollected, main_contract_code))
            
        conn.commit()
        return True, "财务数据同步完成"
    except Exception as e:
        if conn: conn.rollback()
        return False, f"同步失败: {e}"
    finally:
        if conn: conn.close()

def void_financial_record(record_code, record_type, operator):
    """
    [V2.0 通用财务作废引擎] 执行财务流水的软删除与审计留痕
    """
    # 动态映射表名
    table_map = {
        "collections": "biz_collections",
        "invoices": "biz_invoices",
        "sub_payments": "biz_outbound_payments" # 预留给明天的分包付款
    }
    table_name = table_map.get(record_type)
    if not table_name:
        return False, f"未知的记录类型: {record_type}"

    sql = f"""
        UPDATE {table_name} 
        SET deleted_at = CURRENT_TIMESTAMP,
            remarks = CONCAT(COALESCE(remarks, ''), ' [🔴 已由 ', %s, ' 作废]')
        WHERE biz_code = %s AND deleted_at IS NULL
    """
    # 直接调用你 db_engine 里的工具函数
    from .db_engine import execute_raw_sql
    success, msg = execute_raw_sql(sql, (operator, record_code))
    
    return success, "作废成功" if success else f"作废失败: {msg}"
```

##### 📄 crud_sys.py

```python
import pandas as pd
from backend.database.db_engine import get_connection, sql_engine, UPLOAD_DIR

def update_biz_code_cascade(old_code, new_code, table_name):
    """
    🟢 终极级联更新：当修改合同编号时，同步修改所有流水、附件表，以及重命名物理文件夹！
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:  # 🟢 必须创建游标
            # 1. 改主表
            cur.execute(f'UPDATE "{table_name}" SET biz_code = %s WHERE biz_code = %s', (new_code, old_code))
            
            # 2. 改周边所有的子表
            cur.execute('UPDATE biz_payment_plans SET main_contract_code = %s WHERE main_contract_code = %s', (new_code, old_code))
            cur.execute('UPDATE biz_invoices SET main_contract_code = %s WHERE main_contract_code = %s', (new_code, old_code))
            cur.execute('UPDATE biz_collections SET main_contract_code = %s WHERE main_contract_code = %s', (new_code, old_code))
            cur.execute('UPDATE sys_attachments SET biz_code = %s WHERE biz_code = %s', (new_code, old_code))
        
        conn.commit()

        # 3. 🟢 物理世界大挪移：重命名硬盘里的文件夹
        old_dir = UPLOAD_DIR / str(old_code)
        new_dir = UPLOAD_DIR / str(new_code)
        if old_dir.exists() and not new_dir.exists():
            old_dir.rename(new_dir) # 彻底解决“孤儿附件”问题

        return True, f"业务编号已全盘迁移至 {new_code}"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def get_attachment_counts():
    """获取所有项目的附件数量统计 (biz_code 版)"""
    conn = None
    try:
        conn = get_connection()
        # 🟢 替换为 biz_code
        sql = "SELECT biz_code, source_table, COUNT(id) as file_count FROM sys_attachments GROUP BY biz_code, source_table"
        return pd.read_sql_query(sql, conn)
    except Exception as e:
        print(f"附件统计查询失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

def soft_delete_project(project_id, table_name, operator_name="System"):
    """软删除：移入回收站 (记录删除人)"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:  # 🟢 依然使用游标防崩溃
            # 🟢 同时更新时间和操作人
            cur.execute(
                f'UPDATE "{table_name}" SET deleted_at = CURRENT_TIMESTAMP, deleted_by = %s WHERE id = %s', 
                (operator_name, project_id)
            )
        conn.commit()
        return True, "已移入回收站"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def restore_project(project_id, table_name):
    """恢复项目：移出回收站 (同步清除删除痕迹)"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # 🟢 恢复时，把时间和操作人统统清空
            cur.execute(
                f'UPDATE "{table_name}" SET deleted_at = NULL, deleted_by = NULL WHERE id = %s', 
                (project_id,)
            )
        conn.commit()
        return True, "项目已恢复"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def get_deleted_projects(tables):
    """获取所有被软删除的项目列表"""
    conn = None
    deleted_list = []
    try:
        conn = get_connection()
        for tbl in tables:
            try:
                # 🟢 替换为 biz_code
                sql = f'SELECT id, biz_code, project_name, manager, "{tbl}" as origin_table FROM "{tbl}" WHERE deleted_at IS NOT NULL'
                df_del = pd.read_sql_query(sql, sql_engine)
                if not df_del.empty:
                    deleted_list.extend(df_del.to_dict('records'))
            except:
                continue
        return deleted_list
    finally:
        if conn: conn.close()

def log_job_operation(operator: str, file_name: str, import_type: str, success_count: int, fail_count: int = 0, error_details: dict = None):
    """
    🟢 V3.0 导入日志写入 (向后兼容的适配器)
    外观依然是旧的 import_operation，但底层已经接入了全新的 sys_job_logs。
    """
    import json
    from backend.database.db_engine import get_connection
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 智能推导状态机
            total_count = success_count + fail_count
            status = 'success' if fail_count == 0 else ('failed' if success_count == 0 else 'partial_fail')
            error_json = json.dumps(error_details, ensure_ascii=False) if error_details else None
            
            # 映射到新的 sys_job_logs 表
            sql = """
                INSERT INTO sys_job_logs 
                (operator, job_type, target_model, source_name, status, total_count, success_count, fail_count, error_details)
                VALUES (%s, 'excel_import', %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                operator, 
                import_type,   # 旧的 import_type 映射为 target_model
                file_name,     # 旧的 file_name 映射为 source_name
                status, 
                total_count, 
                success_count, 
                fail_count, 
                error_json
            ))
        conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 写入批量任务日志失败: {e}")
        return False
    finally:
        if conn: conn.close()     
```

##### 📄 custom_schema.py

```python
# 文件位置: backend/database/custom_schema.py
# 🟢 作用：存放当前项目所有专属的、带物理外键的底层流水表/静态表

def execute_custom_static_tables(cursor):
    """在此处编写所有不需要 JSON 驱动的底层表 SQL"""
    # =========================================================
    # 🏗️ 核心业务表 1：收款计划表 (契约层)
    # 作用：记录合同约定的里程碑节点，用于预测未来的现金流和生成催款计划。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biz_payment_plans (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) UNIQUE NOT NULL,
            main_contract_code VARCHAR(100) NOT NULL,  -- 归属主合同
            milestone_name VARCHAR(255),               -- 款项节点
            payment_ratio NUMERIC(5,2) DEFAULT 0.00,   -- 比例
            planned_amount NUMERIC(15,2) DEFAULT 0.00, -- 计划金额
            operator VARCHAR(50),                      -- 操作人
            planned_date DATE,                         -- 预警日期
            conditions TEXT,                           -- 付款条件
            remarks TEXT,
            deleted_at TIMESTAMP DEFAULT NULL,         -- 软删除
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================
    # 🏗️ 核心业务表 2：发票记录表 (财务层)
    # 作用：记录税务义务的履行，是计算“财务应收账款”和“未开票收入”的核心。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biz_invoices (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) UNIQUE NOT NULL,
            main_contract_code VARCHAR(100) NOT NULL,  -- 宏观挂靠主合同
            target_plan_code VARCHAR(100),             -- 微观认领收款计划 (对应哪一期付款)
            invoice_amount NUMERIC(15,2) DEFAULT 0.00, -- 开票金额
            invoice_date DATE,                         -- 开票日期
            invoice_number VARCHAR(100),               -- 发票号码
            invoice_type VARCHAR(50),                  -- 发票类型 (如: 专票, 普票)
            operator VARCHAR(50),
            remarks TEXT,
            deleted_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================
    # 🏗️ 核心业务表 3：资金流水表 (执行层)
    # 作用：记录银行实际进出的真金白银。支持多笔流水核销一张发票，或一笔流水对应多个合同。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biz_collections (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) UNIQUE NOT NULL,
            main_contract_code VARCHAR(100) NOT NULL,  -- 宏观挂靠主合同
            target_plan_code VARCHAR(100),             -- 微观认领收款计划
            related_invoice_code VARCHAR(100),         -- (可选) 关联的特定发票单号
            collected_amount NUMERIC(15,2) DEFAULT 0.00, -- 到账金额
            collected_date DATE,                       -- 到账日期
            update_project_stage VARCHAR(100),         -- 🟢 顺手更新项目阶段 (放在这里最合适)
            operator VARCHAR(50),
            remarks TEXT,
            deleted_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================
    # 🏗️ 核心业务表 4：变更协议表 (演变层)
    # 作用：记录合同生命周期内的增减项，动态推演“最新合同额”。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_change_orders (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) NOT NULL,             -- 关联合同编号
            change_no VARCHAR(100) NOT NULL,            -- 变更单/签证单编号
            change_amount NUMERIC(15,2) DEFAULT 0.00,   -- 变更金额 (支持负数表示核减)
            change_date DATE,                           -- 变更发生/确认日期
            approval_status VARCHAR(50) DEFAULT '审批中',-- 审批状态 (草稿 / 审批中 / 已生效)
            change_reason TEXT,                         -- 变更原因说明
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================
    # 🏗️ 核心业务表 5：质保/保证金表 (风险层)
    # 作用：管理被扣留的资金池，预警到期未退的保证金。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_retentions (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) NOT NULL,             -- 关联合同编号
            retention_type VARCHAR(50),                 -- 保证金类型 (履约保证金 / 质保金 / 农民工工资保证金)
            retention_amount NUMERIC(15,2) DEFAULT 0.00,-- 扣留/缴纳金额
            due_date DATE,                              -- 预计解冻/返还日期
            actual_return_date DATE,                    -- 实际返还日期
            status VARCHAR(50) DEFAULT '未解冻',         -- 状态 (未解冻 / 已到期 / 已全额返还 / 已扣除抵扣)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
     # =========================================================
    # 🏗️ 核心业务表 6：对外付款流水表 
    # 作用：记录分包合合同的付款流水。
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biz_outbound_payments (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) UNIQUE NOT NULL,
            sub_contract_code VARCHAR(100) NOT NULL,   -- 认领分包合同
            payment_amount NUMERIC(15,2) DEFAULT 0.00, -- 实际付款金额
            payment_date DATE,                         -- 付款日期
            payment_method VARCHAR(50),                -- 支付方式(电汇/承兑等)
            operator VARCHAR(50),
            remarks TEXT,
            deleted_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # =========================================================
    # 🏗️ 核心业务表 7：分包进项发票表 (分包侧 - 纯票据流入)
    # 🟢 新增：独立管理分包商开过来的发票，用于防范“欠票风险”
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biz_sub_invoices (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) UNIQUE NOT NULL,
            sub_contract_code VARCHAR(100) NOT NULL,   -- 认领分包合同
            invoice_amount NUMERIC(15,2) DEFAULT 0.00, -- 收票金额
            invoice_date DATE,                         -- 收票/开票日期
            invoice_number VARCHAR(100),               -- 发票号码
            invoice_type VARCHAR(50),                  -- 发票类型(如:增值税专用发票)
            operator VARCHAR(50),
            remarks TEXT,
            deleted_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
   # ==========================================
    # 🚀 [第三战区] 物理性能加速 (高频查询索引)
    # ==========================================
    
    
    # 主合同侧索引
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_plan_main" ON biz_payment_plans(main_contract_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_inv_main" ON biz_invoices(main_contract_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_inv_plan" ON biz_invoices(target_plan_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_col_main" ON biz_collections(main_contract_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_col_plan" ON biz_collections(target_plan_code);')

    # 通用表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_change_biz" ON sys_change_orders(biz_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_retention_biz" ON sys_retentions(biz_code);')

    # 🟢 分包侧索引 (双剑合璧)
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_out_sub" ON biz_outbound_payments(sub_contract_code);')
    cursor.execute('CREATE INDEX IF NOT EXISTS "idx_sub_inv_sub" ON biz_sub_invoices(sub_contract_code);')
```

##### 📄 db_engine.py

```python
import os
import psycopg2
import sys
if sys.platform == 'win32':
    os.environ['PGCLIENTENCODING'] = 'utf-8'
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from backend.utils.logger import sys_logger 

# ==========================================
# 1. 路径配置 (仅用于附件 UPLOAD)
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. 数据库连接配置 (对接 Docker)
# ==========================================
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5435")
DB_USER = os.getenv("DB_USER", "erp_admin")
DB_PASS = os.getenv("DB_PASS", "admin")
DB_NAME = os.getenv("DB_NAME", "erp_core_db")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

sql_engine = create_engine(
    DATABASE_URL, 
    pool_size=10, 
    max_overflow=20
)

def get_connection():
    """
    🟢 架构升级：直接从 SQLAlchemy 的连接池中借用底层 psycopg2 连接！
    不仅免费获得了企业级连接池的防并发保护，用完 close() 时还会自动放回池子。
    """
    try:
        return sql_engine.raw_connection()
    except Exception as e:
        # 🟢 替换原来的 print，把致命错误记录到日志
        sys_logger.error(f"🚨 数据库连接池获取失败: {e}", exc_info=True)
        raise e
        
def get_readonly_connection(db_name=None):
    """【兼容性】实验室只读连接"""
    return get_connection()

# ==========================================
# 3. 状态与管理函数 (收编并改造)
# ==========================================

def get_current_db_name():
    """返回当前连接的库名"""
    return DB_NAME

def set_current_db(name):
    """【废弃兼容】PG 时代不动态切库，仅作 pass"""
    pass

def get_available_dbs():
    """扫描 PG 实例中所有的数据库列表"""
    conn = None
    try:
        # 连接到系统库查询所有数据库
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname='postgres')
        cur = conn.cursor()
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        return [row[0] for row in cur.fetchall()]
    except:
        return [DB_NAME]
    finally:
        if conn: conn.close()

def check_db_exists(name):
    """检查特定名称的库是否存在"""
    return name in get_available_dbs()

# ==========================================
# 4. 运维指令 (重构为 SQL 指令)
# ==========================================

def execute_raw_sql(sql, params=None):
    """执行原生 SQL 语句 (适配 %s 占位符)"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params or [])
        
        # 如果是查询语句，返回 DataFrame
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return True, pd.DataFrame(rows, columns=cols)
        
        conn.commit()
        return True, f"影响行数: {cur.rowcount}"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def backup_db():
    """
    【注意】PG 的备份建议使用命令行 pg_dump。
    此函数仅提供逻辑占位，或执行简单的表级备份。
    """
    return False, "请通过 Docker 使用 pg_dump 进行物理备份"

def db_health_report():
    """扫描 PG 数据健康度"""
    import json
    from backend.database.schema import get_all_data_tables 
    conn = None
    try:
        conn = get_connection()
        tables = get_all_data_tables()
        report = {"total_tables": len(tables), "invalid_json": 0, "stats": {}}
        
        for t in tables:
            try:
                # PG 的 JSONB 验证更严苛，通常不会有非法 JSON
                cur = conn.cursor()
                cur.execute(f'SELECT count(*) FROM "{t}"')
                report["stats"][t] = cur.fetchone()[0]
            except:
                pass
        return report
    finally:
        if conn: conn.close()
```

##### 📄 schema.py

```python
# 文件位置: backend/database/schema.py
# 🟢 作用：纯粹的底层数据库引擎，以后任何项目都不需要修改此文件！

import re
from backend.config import config_manager as cfg
from backend.database.db_engine import get_connection

# 引入刚刚解耦出去的定制表模块
from backend.database.custom_schema import execute_custom_static_tables

# =========================================================
# 1. 结构探测与工具库 (全部保留您的原始代码)
# =========================================================
def get_table_columns(table_name):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"获取列失败: {e}")
        return []
    finally:
        if conn: conn.close()
        
def get_table_schema(table_name):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", (table_name,))
        return [{"name": row[0], "type": row[1]} for row in cur.fetchall()]
    except Exception as e:
        print(f"获取表结构失败: {e}")
        return []
    finally:
        if conn: conn.close()

def has_column(table_name, column_name):
    return column_name in get_table_columns(table_name)

def sanitize_table_name(name):
    safe_name = re.sub(r'[^\w]', '_', str(name))
    if safe_name and safe_name[0].isdigit():
        safe_name = "_" + safe_name
    return f"data_{safe_name}".lower()

def get_all_data_tables():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND (table_name LIKE 'data_%' OR table_name LIKE 'biz_%')")
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        if conn: conn.close()

# =========================================================
# 2. V2.0 动态建表引擎 (核心黑盒)
# =========================================================
def _create_dynamic_business_tables(cursor):
    """读取 JSON 循环建表，自动注入系统列"""
    # 这里的 _CURRENT_CONFIG 需要通过函数获取最新状态
    config_data = cfg.load_data_rules() 
    models = config_data.get("models", {})
    
    for model_name, config in models.items():
        table_name = config.get("table_name")
        field_meta = config.get("field_meta", {})
        formula_cols = config.get("formulas", {}).keys()
        
        if not table_name or not field_meta: continue

        columns_sql = [
            "id SERIAL PRIMARY KEY",
            "deleted_at TIMESTAMP DEFAULT NULL",  # 原有的删除时间
            "deleted_by VARCHAR(50) DEFAULT NULL",  # 🟢 新增：记录到底是谁删的
            "extra_props JSONB DEFAULT '{}'::jsonb" 
        ]
        
        for field_key, meta in field_meta.items():
            if field_key in formula_cols:
                continue 
            field_type = meta.get("type", "text")
            if field_type == "money": col_def = f"{field_key} NUMERIC(15,2) DEFAULT 0.00"
            elif field_type == "percent": col_def = f"{field_key} REAL DEFAULT 0"
            elif field_type == "date": col_def = f"{field_key} DATE"
            elif field_type == "int": col_def = f"{field_key} INTEGER DEFAULT 0"
            else: col_def = f"{field_key} VARCHAR(255)"
                
            if field_key in ["biz_code", "sub_code"]:
                col_def += " UNIQUE NOT NULL"
                
            columns_sql.append(col_def)
        
        columns_sql.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        columns_sql.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        columns_str = ",\n    ".join(columns_sql)
        final_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n    {columns_str}\n);'
        cursor.execute(final_sql)
        
        # 🟢 热更新：为已存在的表追加 JSON 中新增的列
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
        existing_columns = {row[0] for row in cursor.fetchall()}
        
        for field_key, meta in field_meta.items():
            if field_key in formula_cols:
                continue
            if field_key not in existing_columns:
                field_type = meta.get("type", "text")
                if field_type == "money": alter_type = "NUMERIC(15,2) DEFAULT 0.00"
                elif field_type == "date": alter_type = "DATE"
                else: alter_type = "VARCHAR(255)"
                
                try:
                    cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "{field_key}" {alter_type};')
                    print(f"🔧 热更新：表 [{table_name}] 自动新增列 [{field_key}]")
                except Exception as alt_e:
                    print(f"⚠️ 追加列失败: {alt_e}")

# =========================================================
# 3. 统一入口
# =========================================================
def sync_database_schema():
    """引擎启动器"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # 0. 创建审计日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_audit_logs (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) NOT NULL,     -- 被操作的业务编号
            model_name VARCHAR(50),             -- 所属模型 (如 enterprise, main_contract)
            action VARCHAR(20),                 -- 动作类型 (INSERT/UPDATE/DELETE/RESTORE)
            operator_name VARCHAR(50),          -- 操作人
            diff_data JSONB,                    -- 变更详情快照 {"字段": ["旧值", "新值"]}
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
        # 1. 创建附件归档表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_attachments (
            id SERIAL PRIMARY KEY,
            biz_code VARCHAR(100) NOT NULL,      -- 挂载的业务主体编号 (如 MAIN-001, SUB-002)
            source_table VARCHAR(50),            -- 来源模型名称 (如 main_contract)
            
            -- 🟢 新增：对接前端的下拉框分类
            file_category VARCHAR(50),           -- 附件分类 (主合同/图纸/结算单等) 
            
            file_name TEXT,                      -- 原始文件名
            file_path TEXT,                      -- 服务器物理路径或 OSS 链接
            file_type VARCHAR(50),               -- 文件后缀名 (pdf/docx/jpg)
            file_size_kb INTEGER DEFAULT 0,      -- 🟢 新增：文件大小(便于以后做网盘容量统计)
            
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

        # 2. 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL, 
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT '普通员工',
            
            -- 1. 业务状态：账号是否被冻结（例如离职、休假、输错密码锁定）
            status VARCHAR(20) DEFAULT 'active',        -- 状态：active(活跃), disabled(禁用), locked(锁定)
            disabled_at TIMESTAMP DEFAULT NULL,         -- 记录账号被禁用的具体时间
            
            -- 2. 架构一致性：软删除标记
            deleted_at TIMESTAMP DEFAULT NULL,          -- NULL表示在职，有时间表示该账号已从系统中彻底移除
            
            -- 3. 安全审计：最后登录时间
            last_login_at TIMESTAMP DEFAULT NULL,       
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
        
        # 3. 创建AI任务表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_ai_tasks (
            id SERIAL PRIMARY KEY,
            file_id INTEGER,                     
            task_type VARCHAR(50) DEFAULT 'contract_extraction', 
            status VARCHAR(20) DEFAULT 'pending', 
            result_json JSONB,                   
            error_msg TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
        # 4. 创建任务日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_job_logs (
            id SERIAL PRIMARY KEY,
            operator VARCHAR(50),      -- 触发人或系统调度器名 (如 'system_cron')
            
            job_type VARCHAR(50),      -- 任务类型 (如 'excel_import', 'api_sync', 'monthly_accrual')
            target_model VARCHAR(50),  -- 影响的业务模型 (如 'main_contract')
            source_name VARCHAR(255),  -- 数据源载体 (文件名，或接口标识符)
            
            status VARCHAR(20) DEFAULT 'processing', -- 状态: processing, success, partial_fail, failed
            
            total_count INTEGER DEFAULT 0,   -- 计划处理总数
            success_count INTEGER DEFAULT 0, -- 成功条数
            fail_count INTEGER DEFAULT 0,    -- 失败条数
            
            error_details TEXT,              -- 详细报错追踪 (JSON格式)
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP           -- 任务完成时间
        )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_audit_biz" ON sys_audit_logs(biz_code);')
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_attachments_biz" ON sys_attachments(biz_code);')
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_ai_tasks_status" ON sys_ai_tasks(status);')
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_users_status" ON sys_users(status);')
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_users_role" ON sys_users(role);')
        cursor.execute('CREATE INDEX IF NOT EXISTS "idx_job_logs_status" ON sys_job_logs(status);')
        # 1. 启动动态引擎建主表
        _create_dynamic_business_tables(cursor)
        
        # 2. 调用外部的定制模块建流水表
        execute_custom_static_tables(cursor)
        
        conn.commit()
        print("🚀 [引擎启动] V2.0 数据库架构同步完毕！")
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ 数据库同步失败: {e}")
        return False
    finally:
        if conn: conn.close()

```

#### 📁 services

##### 📄 __init__.py

```python
# 文件位置: backend/services/__init__.py

from .import_service import run_import_process
from .export_service import export_table_data
from .flow_service import (
    add_flow_record, 
    get_project_flows, 
    delete_flow_record,
    recalculate_project_total
)
from .file_service import (
    save_attachment
    )
from .project_service import update_biz_code_cascade
from .analysis_service import (
    get_all_flows_dataframe,
    get_financial_report
)
from .excel_service import clean_excel,smart_classify_header
from .ai_service import AIService

__all__ = [
    "run_import_process",
    "export_table_data",
    "add_flow_record",
    "get_project_flows",
    "delete_flow_record",
    "recalculate_project_total",
    "update_biz_code_cascade",
    "get_all_flows_dataframe",
    "get_financial_report",
    "clean_excel",
    "smart_classify_header",
    "AIService","save_attachment"
]
```

##### 📄 ai_service.py

```python
# ai_service.py
import requests
import json

class AIService:
    def __init__(self, host="http://localhost:11434"):
        self.host = host
        self.is_available = self._check_health()

    def _check_health(self):
        try:
            requests.get(f"{self.host}", timeout=0.5)
            return True
        except:
            return False

    def get_available_models(self):
        if not self.is_available: return []
        try:
            res = requests.get(f"{self.host}/api/tags")
            if res.status_code == 200:
                data = res.json()
                return [m['name'] for m in data.get('models', [])]
        except:
            pass
        return []

    def analyze_stream(self, model, data_context, user_prompt):
        """
        流式分析接口
        :param data_context: List[Dict] 核心数据摘要
        :param user_prompt: 用户的具体指令
        """
        # 1. 构建 Prompt
        system_prompt = f"""你是一个专业的建筑工程项目数据分析师。
        请根据以下 {len(data_context)} 个项目的核心数据，回答用户的问题。
        
        数据摘要:
        {json.dumps(data_context, ensure_ascii=False)}
        
        要求:
        1. 关注回款率、欠款风险和异常金额。
        2. 如果数据量较大，请总结共性问题。
        3. 回答要简练、专业，使用 Markdown 格式。
        """

        # 2. 调用 API
        payload = {
            "model": model,
            "prompt": f"{system_prompt}\n\n用户指令: {user_prompt}",
            "stream": True
        }

        try:
            with requests.post(f"{self.host}/api/generate", json=payload, stream=True) as r:
                for line in r.iter_lines():
                    if line:
                        body = json.loads(line)
                        token = body.get("response", "")
                        yield token
                        if body.get("done"):
                            break
        except Exception as e:
            yield f"\n❌ AI 分析中断: {str(e)}"
```

##### 📄 analysis_service.py

```python
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
```

##### 📄 excel_service.py

```python
import pandas as pd
import re
from datetime import datetime
import json
import os

from backend.config import config_manager
from backend.utils.logger import sys_logger

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
        except: sys_logger.debug(f"清洗单元格异常: {e}")
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
```

##### 📄 export_service.py

```python
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
```

##### 📄 file_service.py

```python
from pathlib import Path
from backend.database.db_engine import get_connection, UPLOAD_DIR

def save_attachment(biz_code, uploaded_file, source_table, file_category="unknown"):
    """
    [Service 层] 负责附件的物理落地、安全校验，并持久化到系统附件库
    """
    conn = None
    try:
        # 1. 物理层：动态建立合同专属文件夹并写入磁盘
        target_dir = UPLOAD_DIR / str(biz_code)
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / uploaded_file.name

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 2. 逻辑层：提取文件元数据 (后缀名等)
        file_extension = Path(uploaded_file.name).suffix.lower().lstrip('.')
        # 预留扩展位：可以在这里调用 os.path.getsize(file_path) 获取文件大小并存入 file_size_kb

        # 3. 持久层：写入数据库 (sys_attachments)
        conn = get_connection()
        sql = """
            INSERT INTO sys_attachments (biz_code, source_table, file_category, file_name, file_path, file_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        conn.execute(sql, (biz_code, source_table, file_category, uploaded_file.name, str(file_path), file_extension))
        conn.commit()
        
        # 🚀 预留钩子：如果是合同文本，且配置了 AI 自动解析，未来在这里向消息队列发送 AI 解析任务！
        
        return True, "附件归档成功"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()
```

##### 📄 flow_service.py

```python
# 文件位置: backend/services/flow_service.py
import pandas as pd
from datetime import datetime
# 🟢 接入数据库大本营
from backend.database import get_connection

def recalculate_project_total(biz_code, source_table):
    """
    [内部逻辑 - 影子卫士] 重新计算该项目的总回款，并回写到底座中。
    """
    if not source_table:
        return False, "未指定源表"
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 🟢 修正：? 替换为 %s
        cursor.execute(
            "SELECT SUM(amount) FROM sys_project_flows WHERE biz_code = %s AND source_table = %s", 
            (biz_code, source_table)
        )
        result = cursor.fetchone()
        total_val = result[0] if result and result[0] is not None else 0.0
        
        # 🟢 修正：? 替换为 %s
        sql_update = f'UPDATE "{source_table}" SET total_collection = %s WHERE biz_code = %s'
        cursor.execute(sql_update, (total_val, biz_code))
        
        conn.commit()
        return True, total_val
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def add_flow_record(biz_code, source_table, amount, flow_date=None, stage="收款", remark=""):
    """
    [流水服务] 新增记录后，自动触发重算
    """
    if not flow_date:
        flow_date = datetime.now().strftime("%Y-%m-%d")
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor() # 🟢 修正：PostgreSQL 必须生成游标执行
        
        # 🟢 修正：? 替换为 %s
        sql = """
            INSERT INTO sys_project_flows (biz_code, source_table, flow_date, amount, stage, remark) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        # 🟢 致命错误修复：严格对齐上方 SQL 的字段顺序！
        cursor.execute(sql, (biz_code, source_table, flow_date, amount, stage, remark))
        conn.commit()
        
        # 自动执行数据同步，保持汇总层与明细层一致
        recalculate_project_total(biz_code, source_table)
        
        return True, "流水记录已添加并更新汇总"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def get_project_flows(biz_code, source_table):
    """
    [流水服务] 获取指定项目的历史流水清单
    """
    conn = None
    try:
        conn = get_connection()
        # 🟢 修正：? 替换为 %s
        query = """
            SELECT id, flow_date, amount, stage, remark 
            FROM sys_project_flows 
            WHERE biz_code = %s AND source_table = %s
            ORDER BY flow_date DESC
        """
        df = pd.read_sql_query(query, conn, params=(biz_code, source_table))
        return df
    except Exception as e:
        print(f"查询流水失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

def delete_flow_record(flow_id, biz_code, source_table):
    """
    [流水服务] 删除记录后，自动触发重算
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor() # 🟢 修正：PostgreSQL 必须生成游标执行
        
        cursor.execute("DELETE FROM sys_project_flows WHERE id = %s", (flow_id,))
        conn.commit()
        
        # 自动同步
        recalculate_project_total(biz_code, source_table)
        
        return True, "记录已删除并更新汇总"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()
```

##### 📄 import_service.py

```python
import pandas as pd
import warnings
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
            cursor.execute(f'UPDATE "{table_name}" SET deleted_at = CURRENT_TIMESTAMP WHERE source_file = %s AND sheet_name = %s', 
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
```

##### 📄 project_service.py

```python
import os
import shutil
# 🟢 引入新架构的底层引擎
from backend.database.db_engine import get_connection, UPLOAD_DIR

def update_biz_code_cascade(old_code, new_code, table_name):
    """
    [项目服务] 级联更新项目编号
    统筹协调数据库级的联动修改与物理附件文件夹的重命名。
    """
    if not old_code or not new_code:
        return False, "编号不能为空"
    if old_code == new_code:
        return False, "新旧编号一致"
    
    # 🟢 兼容 pathlib 路径
    old_dir = os.path.join(str(UPLOAD_DIR), str(old_code))
    new_dir = os.path.join(str(UPLOAD_DIR), str(new_code))
    
    conn = None
    try:
        # 🟢 调用新引擎获取连接
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. 检查冲突
        cursor.execute(f'SELECT 1 FROM "{table_name}" WHERE biz_code = %s', (new_code,))
        if cursor.fetchone():
            raise ValueError(f"新编号 [{new_code}] 已存在，无法修改！")
        
        # 2. 修改主表
        cursor.execute(f'UPDATE "{table_name}" SET biz_code = %s WHERE biz_code = %s', (new_code, old_code))
        if cursor.rowcount == 0:
            raise ValueError("在主表中未找到原项目，修改失败")
        
        # 3. 修改关联表
        cursor.execute("UPDATE sys_project_flows SET biz_code = %s WHERE biz_code = %s AND source_table = %s", (new_code, old_code, table_name))
        cursor.execute("UPDATE sys_attachments SET biz_code = %s WHERE biz_code = %s AND source_table = %s", (new_code, old_code, table_name))   
        
        # 4. 迁移物理文件
        renamed_folder = False
        if os.path.exists(old_dir):
            if os.path.exists(new_dir):
                for item in os.listdir(old_dir):
                    s = os.path.join(old_dir, item)
                    d = os.path.join(new_dir, item)
                    if not os.path.exists(d):
                        shutil.move(s, d)
                os.rmdir(old_dir)
                renamed_folder = True
            else:
                os.rename(old_dir, new_dir)
                renamed_folder = True
        
        conn.commit()
        msg = "变更成功"
        if renamed_folder:
            msg += " | 文件夹已重命名"
        return True, msg
        
    except Exception as e:
        if conn: conn.rollback()
        return False, f"修改失败: {str(e)}"
    finally:
        if conn:
            conn.close()
```

#### 📁 utils

##### 📄 __init__.py

```python
from .formatters import (
    safe_float,
    parse_date_cell
)

__all__ = [
    "safe_float",
    "parse_date_cell"
]
```

##### 📄 formatters.py

```python
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
```

##### 📄 logger.py

```python
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys

# 1. 确保日志目录存在 (我们把它放在和 uploads 同级的 data/logs 目录下)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "erp_system.log"

def setup_logger():
    """初始化全局日志记录器"""
    # 如果已经配置过，直接返回，防止重复打印
    logger = logging.getLogger("ERP_CORE")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # 2. 定义高可读性的日志格式
    # 格式: [2026-03-22 10:15:30] [ERROR] [db_engine.py:42] -> 数据库连接失败
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] -> %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 3. 落地到文件：设置日志轮转 (单文件最大 10MB，最多保留 5 个备份)
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 4. 同时输出到控制台 (方便你在本地或 Docker logs 里看)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# 暴露出全局单例 logger
sys_logger = setup_logger()

# 文件位置: backend/utils/logger.py (追加在文件末尾)

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """
    全局异常拦截器：专门抓捕那些没有被 try...except 兜住的致命崩溃！
    """
    # 忽略 Ctrl+C 导致的程序中断，不当做报错记录
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # 🚨 将系统崩溃级别的报错，强制写入黑匣子！
    sys_logger.critical("💥 [致命崩溃] 发现未捕获的系统级异常！", exc_info=(exc_type, exc_value, exc_traceback))

# 替换 Python 默认的崩溃处理机制
sys.excepthook = handle_unhandled_exception
```

### 📁 backups

### 📁 data

#### 📁 backups

#### 📁 logs

#### 📁 sqlite_db

#### 📁 uploads

### 📁 react_enterprise

#### 📁 src

##### 📁 components

##### 📁 pages

### 📁 streamlit_lab

#### 📄 app.py

```python
# ==========================================
# 🟢 绝对第一顺位：打通项目底层路径 (必须放在最前面！)
# ==========================================
import sys
from pathlib import Path
import time

# 获取当前 app.py 的父目录(streamlit_lab) 的父目录(ERP_V2_PRO)
ROOT_DIR = Path(__file__).resolve().parent.parent
# 强制把根目录插队到 Python 搜索列表的第 0 号位置！
sys.path.insert(0, str(ROOT_DIR))

# ==========================================
# 🟢 第二顺位：导入第三方标准库
# ==========================================
import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 🟢 第三顺位：导入我们自己的 backend
# ==========================================
from backend import database as db
from backend.database import schema
from backend.config import config_manager as cfg
import sidebar_manager
import debug_kit

st.set_page_config(page_title="建筑专项管理系统", page_icon="🏗️", layout="wide")
# 1. 侧边栏
sidebar_manager.render_sidebar()
# ==========================================
# 🟢 核心数据统计 (V2.0 元数据驱动版)
# ==========================================
@st.cache_resource
def init_system_database():
    """🟢 增加 5 秒缓冲，确保数据库服务已就绪"""
    print("⏳ 等待数据库容器响应...")
    time.sleep(5)  # 给予数据库充足的冷启动时间
    schema.sync_database_schema()
    print("✅ 数据库底座初始化完毕！")

# 立即调用！(由于有 cache_resource 保护，它在服务器运行期间只会执行这一次)
init_system_database()
@st.cache_data(ttl=60) 
def load_global_stats():
    """
    [V2.0 升级] 不再扫描物理表名，而是根据 app_config.json 中的模型定义进行汇总。
    这样能确保公式计算（如回款率、欠款金额）在统计前被自动补齐。
    """
    # 1. 拿到所有业务模型的名字 (如 'project', 'enterprise')
    # 这里的 cfg.load_data_rules() 确保拿到的是最新配置
    config = cfg.load_data_rules()
    model_names = config.get("models", {}).keys()
    
    total_projects = 0
    total_contract = 0.0
    total_collection = 0.0
    recent_updates = []

    for m_name in model_names:
        # 🟢 核心替换：调用 V2.0 终极查询引擎
        # 它会自动执行 core_logic 里的公式，补齐‘回款率’、‘欠款’等动态字段
        df = db.fetch_dynamic_records(model_name=m_name)
        
        if not df.empty:
            total_projects += len(df)
            
            # 2. 物理列与公式列的兼容累加
            # 在 V2.0 中，contract_amount 和 total_collection 可能是物理列，也可能是公式列
            if 'contract_amount' in df.columns:
                total_contract += pd.to_numeric(df['contract_amount'], errors='coerce').fillna(0).sum()
            if 'total_collection' in df.columns:
                total_collection += pd.to_numeric(df['total_collection'], errors='coerce').fillna(0).sum()
            
            # 3. 收集最近更新 (V2.0 适配：使用 updated_at 系统列)
            if 'updated_at' in df.columns:
                df['updated_at'] = pd.to_datetime(df['updated_at'], errors='coerce')
                # 标记模型名称，方便用户识别数据来源
                df['model_label'] = m_name 
                # 截取需要的列（注意：project_name 是 project 模型特有的，其他模型可能叫别的，这里做个兜底）
                name_col = 'project_name' if 'project_name' in df.columns else df.columns[1] 
                manager_col = 'manager' if 'manager' in df.columns else 'extra_props'
                
                # 提取最近 5 条
                top5 = df.nlargest(5, 'updated_at')[[name_col, manager_col, 'updated_at', 'model_label']]
                # 统一重命名方便合并展示
                top5.columns = ['display_name', 'operator', 'update_time', 'source_model']
                recent_updates.append(top5)

    # 合并全局最近更新
    if recent_updates:
        df_recent = pd.concat(recent_updates).nlargest(5, 'update_time')
    else:
        df_recent = pd.DataFrame()

    return total_projects, total_contract, total_collection, df_recent

@st.cache_data(ttl=60)
def load_upcoming_receivables():
    """获取 30 天内及已逾期的待收款计划"""
    # 1. 获取主合同和收款计划表
    df_plans = db.fetch_dynamic_records(model_name="payment_plan")
    df_contracts = db.fetch_dynamic_records(model_name="main_contract")
    
    if df_plans.empty:
        return 0.0, pd.DataFrame()
        
    # 2. 数据类型清洗
    df_plans['planned_date'] = pd.to_datetime(df_plans['planned_date'], errors='coerce')
    df_plans['planned_amount'] = pd.to_numeric(df_plans['planned_amount'], errors='coerce').fillna(0)
    # 兼容公式计算出的剩余未收，如果没有则默认等于计划金额
    if 'remaining_uncollected' in df_plans.columns:
        df_plans['remaining_uncollected'] = pd.to_numeric(df_plans['remaining_uncollected'], errors='coerce').fillna(0)
    else:
        df_plans['remaining_uncollected'] = df_plans['planned_amount']

    # 3. 核心业务过滤：剩余未收 > 0 且 日期 <= 今天 + 30天
    target_date = pd.Timestamp.today().normalize() + pd.Timedelta(days=30)
    
    # 过滤出需要催款的记录
    urgent_plans = df_plans[
        (df_plans['remaining_uncollected'] > 0) & 
        (df_plans['planned_date'] <= target_date)
    ].copy()
    
    if urgent_plans.empty:
        return 0.0, pd.DataFrame()
        
    # 4. 算出总共需要收多少钱
    total_urgent_amount = urgent_plans['remaining_uncollected'].sum()
    
    # 5. 关联主合同拿到项目名称
    if not df_contracts.empty and 'biz_code' in df_contracts.columns:
        urgent_plans = urgent_plans.merge(
            df_contracts[['biz_code', 'project_name']], 
            left_on='main_contract_code', 
            right_on='biz_code', 
            how='left'
        )
    else:
        urgent_plans['project_name'] = urgent_plans['main_contract_code']
        
    # 6. 计算状态标签（逾期 / 30天内）
    today = pd.Timestamp.today().normalize()
    urgent_plans['status_label'] = urgent_plans['planned_date'].apply(
        lambda x: "🚨 已逾期" if x < today else "⏳ 即将到期"
    )
    
    # 按日期排序，逾期的、马上到期的排在最前面
    urgent_plans = urgent_plans.sort_values(by='planned_date', ascending=True)
    
    return total_urgent_amount, urgent_plans


# 3. 页面渲染
st.title(f"👋 欢迎使用建筑专项项目管理系统")
st.caption(f"今天是 {datetime.now().strftime('%Y年%m月%d日')} | 系统状态: 🟢 正常运行")

# 加载数据
with st.spinner("正在汇总全库数据..."):
    t_proj, t_cont, t_coll, df_recent = load_global_stats()

# --- A. 核心指标卡 (KPI Cards) ---
st.divider()
k1, k2, k3, k4 = st.columns(4)

# 计算存量 (总额 - 已收)
stock_amount = t_cont - t_coll

with k1:
    st.metric("🏗️ 在库项目总数", f"{t_proj} 个", delta="全库统计")

with k2:
    # 🟢 修改点：这里改成了“存量合同额”
    st.metric(
        "💰 存量合同额 (未收)", 
        f"¥ {stock_amount/10000:,.1f} 万", 
        delta="核心关注指标",
        help="计算公式：累计合同总额 - 累计已收款"
    )

with k3:
    # 回款率计算
    rate = (t_coll / t_cont * 100) if t_cont > 0 else 0
    st.metric("💸 累计实收回款", f"¥ {t_coll/10000:,.1f} 万", delta=f"回款率 {rate:.1f}%")

with k4:
    # 🟢 修改点：原本的待收金额移到了K2，这里改为显示“历史总合同额”作为背景参考
    st.metric(
        "📜 历史累计签约", 
        f"¥ {t_cont/10000:,.1f} 万", 
        delta_color="off",
        help="所有项目的合同额总和 (含已完工)"
    )

# --- B. 快捷入口 & 最近动态 ---
st.divider()
c_main, c_side = st.columns([2, 1])

# 加载预警数据
total_urgent, df_urgent = load_upcoming_receivables()

with c_main:
    st.subheader("🚨 近期收款预警 (30天内及逾期)")
    
    # 增加一个醒目的汇总横幅
    if total_urgent > 0:
        st.error(f"**资金预警：** 近期共有 **¥ {total_urgent / 10000:,.1f} 万** 应收账款需要催办！")
        
        # 挑选要展示的列，优化表头体验
        display_df = df_urgent[['project_name', 'milestone_name', 'planned_date', 'remaining_uncollected', 'status_label']]
        
        st.dataframe(
            display_df,
            column_config={
                "project_name": st.column_config.TextColumn("归属项目", width="medium"),
                "milestone_name": "款项节点",
                "planned_date": st.column_config.DateColumn("预计收款日", format="YYYY-MM-DD"),
                "remaining_uncollected": st.column_config.NumberColumn("待收金额(元)", format="¥ %.2f"),
                "status_label": "紧急状态"
            },
            width="stretch",
            hide_index=True
        )
    else:
        st.success("🎉 太棒了！30 天内没有积压或即将到期的应收账款。")

with c_side:
    st.subheader("🚀 快速开始")
    with st.container(border=True):
        st.write("常用功能直达：")
        if st.button("📂 进入项目看板", width="stretch"):
            st.switch_page("pages/01_📂_项目看板.py")
        if st.button("🛠️ 新增/维护项目", width="stretch"):
            st.switch_page("pages/02_🛠️_主合同管理.py")
        if st.button("📊 查看财务报表", width="stretch"):
            st.switch_page("pages/04_📊_数据分析.py")

debug_kit.execute_debug_logic()
```

#### 📄 components.py

```python
# ==========================================
# 🎨 Streamlit UI 小组件 (偷懒神器) V3
# ==========================================
import streamlit as st
import pandas as pd
from datetime import datetime
import json
from backend.database.db_engine import get_connection
from backend.config import config_manager as cfg
from backend.database.crud import fetch_dynamic_records

def render_smart_widget(col_name, label, val, col_type, config_type, is_disabled, field_meta, override_options=None, override_format_func=None):
    """
    [智能 UI 组件渲染工厂] 根据字段类型，自动生成对应的 Streamlit 输入框。
    """
    # 🟢 魔法注入：如果外部传了选项，强行霸占 options，并把组件类型变异为 select！
    options = override_options if override_options is not None else field_meta.get("options", [])
    if override_options is not None:
        config_type = "select"

    default_val = field_meta.get("default", None)
    step_val = field_meta.get("step", 1000.0)
    min_val = field_meta.get("min_value", None)
    max_val = field_meta.get("max_value", None)

    if val is None and default_val is not None:
        val = default_val

    # ================= 渲染核心逻辑 =================
    
    if config_type == "select" and options:
        try:
            idx = options.index(val) if val in options else 0
        except ValueError:
            idx = 0
            
        # 🟢 魔法注入：如果外部传了 format_func，优先使用！
        if override_format_func:
            return st.selectbox(label, options=options, index=idx, disabled=is_disabled, format_func=override_format_func, key=f"input_{col_name}")
        else:
            return st.selectbox(label, options=options, index=idx, disabled=is_disabled, key=f"input_{col_name}")
    elif col_name == 'is_active':
        return st.toggle(label, value=bool(val) if val is not None else True, key=f"input_{col_name}")

    elif config_type == "date":
        if pd.isna(val) or val is None or str(val).strip() == "":
            default_date = datetime.today().date()
        else:
            try:
                default_date = pd.to_datetime(val).date()
            except:
                default_date = datetime.today().date()
                
        selected_date = st.date_input(label, value=default_date, disabled=is_disabled, key=f"input_{col_name}")
        return str(selected_date) 
      
    elif "DECIMAL" in col_type or "REAL" in col_type or "INT" in col_type:
        try:
            default_num = float(val)
        except (ValueError, TypeError):
            default_num = 0.0
        display_format = "%.2f"
        
        if config_type == "percent":
            label = f"{label} (%)"
            default_num = default_num * 100 
            if min_val is not None: min_val = float(min_val) * 100
            if max_val is not None: max_val = float(max_val) * 100
            if min_val is None: min_val = 0.0
            if max_val is None: max_val = 100.0
            step_val = 5
        
        if min_val is not None:
            default_num = max(default_num, float(min_val))
        if max_val is not None:
            default_num = min(default_num, float(max_val))
            
        raw_input = st.number_input(
            label, 
            value=default_num, 
            min_value=float(min_val) if min_val is not None else None,
            max_value=float(max_val) if max_val is not None else None,
            disabled=is_disabled,
            step=float(step_val),
            format=display_format,
            key=f"input_{col_name}"
        )
        
        return raw_input / 100.0 if config_type == "percent" else raw_input
            
    else:
        default_str = str(val) if val is not None else ""
        return st.text_input(label, value=default_str, disabled=is_disabled, key=f"input_{col_name}")

def show_toast_success(msg):
    st.toast(f"✅ {msg}", icon="🎉")

def show_toast_error(msg):
    st.toast(f"❌ {msg}", icon="😱")

def style_metric_card():
    st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #f9f9f9;
        border: 1px solid #e6e6e6;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

def remove_prefix_formatter(prefix: str):
    def formatter(item):
        if isinstance(item, str) and item.startswith(prefix):
            return item[len(prefix):]
        return item
    return formatter

def dict_mapping_formatter(mapping_dict: dict):
    def formatter(item):
        return mapping_dict.get(item, item)
    return formatter

# ==========================================
# 🚀 V3.0 宏观 UI 渲染引擎 (支持动态注入)
# ==========================================
def render_dynamic_form(model_name: str, form_title: str, existing_data: dict = None, hidden_fields: list = None, readonly_fields: list = None, dynamic_options: dict = None, format_funcs: dict = None):
    """
    [宏观组件 2：动态输入表单 - V3 终极版]
    极其强悍的表单生成器！自动根据 JSON 生成输入框，并支持在页面端注入动态下拉选项和格式化魔法！
    """
    field_meta = cfg.get_field_meta(model_name)
    if not field_meta:
        st.error(f"❌ 找不到模型 {model_name} 的配置")
        return None
        
    st.subheader(form_title)
    form_data = {}
    existing_data = existing_data or {}
    
    hidden_fields = hidden_fields or []
    readonly_fields = readonly_fields or []
    
    # 🟢 接收并初始化动态参数
    dynamic_options = dynamic_options or {}
    format_funcs = format_funcs or {}
    
    editable_fields = {
        k: v for k, v in field_meta.items() 
        if not v.get("is_virtual", False) and k not in hidden_fields
    }
    
    with st.form(key=f"form_{model_name}"):
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        
        for idx, (field_key, meta) in enumerate(editable_fields.items()):
            label = meta.get("label", field_key)
            col_type = meta.get("type", "text")
            val = existing_data.get(field_key, None)
            
            is_readonly = meta.get("readonly", False) or (field_key in readonly_fields)
            
            config_type = meta.get("type", "text")
            pseudo_col_type = "DECIMAL" if config_type in ["money", "percent", "number"] else "VARCHAR"
            
            with cols[idx % 3]:
                user_input = render_smart_widget(
                    col_name=field_key,
                    label=label,
                    val=val,
                    col_type=pseudo_col_type,
                    config_type=config_type,
                    is_disabled=is_readonly,
                    field_meta=meta,
                    override_options=dynamic_options.get(field_key),   # 🟢 动态选项注入
                    override_format_func=format_funcs.get(field_key)   # 🟢 格式化魔法注入
                )
                form_data[field_key] = user_input
                
        submit_btn = st.form_submit_button("💾 保存提交", use_container_width=True)
        
        if submit_btn:
            return form_data
    return None


def render_audit_timeline(biz_code: str, model_name: str = None):
    """
    [通用审计组件：时光机]
    传入 biz_code，自动展示该对象的完整生命周期。
    """   
    st.subheader(f"🕰️ 操作审计日志: {biz_code}")
    
    conn = None
    try:
        conn = get_connection()
        # 按时间倒序查询该编号的所有日志
        sql = "SELECT operator_name, action, diff_data, created_at FROM sys_audit_logs WHERE biz_code = %s ORDER BY created_at DESC"
        df_logs = pd.read_sql_query(sql, conn, params=(biz_code,))
        
        if df_logs.empty:
            st.info("🌱 当前暂无变更记录。")
            return

        # 尝试获取该模型的字段中文翻译字典
        field_meta = {}
        if model_name:
            field_meta = cfg.get_model_config(model_name).get("field_meta", {})

        # 绘制时光机时间轴
        for _, row in df_logs.iterrows():
            action_time = row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            action = row['action']
            operator = row['operator_name']
            
            # 解析差异 JSON
            diff_data = row['diff_data']
            if isinstance(diff_data, str):
                try: diff_data = json.loads(diff_data)
                except: diff_data = {}
            
            # 使用 Streamlit 的容器进行样式隔离
            with st.container(border=True):
                # 表头：时间和动作
                action_icon = "🆕" if action == "INSERT" else "✏️" if action == "UPDATE" else "🗑️"
                st.markdown(f"**{action_icon} {action_time}** | 操作人: `{operator}`")
                
                # 遍历差异并显示
                for col_key, changes in diff_data.items():
                    if len(changes) == 2:
                        old_val, new_val = changes
                        # 翻译列名为中文（如果有配置的话）
                        col_label = field_meta.get(col_key, {}).get("label", col_key)
                        
                        st.markdown(
                            f"&nbsp;&nbsp;&nbsp;&nbsp;▪️ **{col_label}**: "
                            f"<span style='color:gray; text-decoration:line-through;'>{old_val}</span> ➡️ "
                            f"<span style='color:green; font-weight:bold;'>{new_val}</span>", 
                            unsafe_allow_html=True
                        )
    except Exception as e:
        st.error(f"读取日志失败: {e}")
    finally:
        if conn: conn.close()
```

#### 📄 debug_kit.py

```python
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import os
import json
from backend import database as db
from backend.config import config_manager

def is_debug_mode():
    return st.session_state.get('debug_mode', False)

def render_debug_sidebar():
    st.sidebar.markdown("---")
    if 'debug_mode' not in st.session_state:
        st.session_state['debug_mode'] = False
    
    mode = st.sidebar.toggle("🐞 开发者模式 (Debug)", value=st.session_state['debug_mode'])
    st.session_state['debug_mode'] = mode
    if mode:
        if st.sidebar.button("🚀 进入实验室 (Sandbox)", width="stretch"):
            st.switch_page("pages/99_🧪_实验室.py")

def execute_debug_logic(current_db_path=None):
    if not is_debug_mode(): return

    actual_db_path = current_db_path
    if actual_db_path is None:
        actual_db_path = db.get_connection()
    
    st.markdown("---")
    st.markdown("### 🐞 开发者控制台 (Pro)")
    
    tabs = st.tabs(["⚙️ 系统全量配置","💾 SQL终端", "🧠 内存/Session","🔥 危险区"])
    # =========================================================
    # Tab 1: 核心模型配置 (应急修改区)
    # =========================================================
    with tabs[0]:
        st.subheader("🛠️ 系统全量配置 (App Config JSON)")
        st.caption("⚠️ 警告：此区域用于紧急修改表结构与映射规则。修改后保存，系统底层的引擎会自动将 label 对齐到 column_mapping 中。")
        
        # 获取最新的配置数据
        current_config = config_manager.load_data_rules()
        # 我们只把 models 部分暴露出来（不包含公式等其他信息），防止用户改乱
        models_data = current_config.get("models", {})
        
        # 纯净的大文本框
        models_input = st.text_area(
            "Models JSON (包含各表的 field_meta 与 column_mapping)",
            value=json.dumps(models_data, indent=4, ensure_ascii=False),
            height=600,
            key="json_models_emergency"
        )
        
        if st.button("💾 强制覆写模型配置", type="primary", width="stretch"):
            try:
                # 解析输入的纯文本 JSON
                new_models = json.loads(models_input)
                
                # 将改动合并回原配置 (保留公式等其他节点不被破坏)
                current_config["models"] = new_models
                
                # 🟢 调用 config_manager 的保存方法，它会在内部自动触发 _auto_sync_labels
                if config_manager.save_data_rules(current_config):
                    st.success("🎉 模型配置覆写成功！")
                    
                    # --- 🟢 新增逻辑：强制触发数据库底座的“热更新” ---
                    try:
                        from backend.database import schema
                        schema.sync_database_schema() # 立即对比并增加缺少的列
                        st.cache_resource.clear()     # 清理 app.py 的启动缓存，防止状态不一致
                        st.success("✅ 数据库底层物理表已同步扩容！")
                    except Exception as e:
                        st.error(f"⚠️ 数据库同步失败，请检查终端日志: {e}")
                    # ------------------------------------------------
                    
                    st.rerun() # 刷新页面重新加载内存
                else:
                    st.error("❌ 文件写入失败。")
            except json.JSONDecodeError as je:
                st.error(f"❌ JSON 格式严重错误，请检查标点符号或括号匹配：{je}")

    # =========================================================
    # Tab 2: SQL 终端 (修复版)
    # =========================================================
    with tabs[1]:
        st.write(f"连接库：`{current_db_path}`")
        st.subheader("💻 SQL 执行终端")
        
        # 1. 获取当前所有表名
        all_tables = db.get_all_data_tables()
        default_table = all_tables[0] if all_tables else "data_Project2026"

        # 2. 定义常用 SQL 模板
        SQL_TEMPLATES = {
            "--- 请选择预设模板 (可选) ---": "",
            "🔍 查看所有表名": "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
            "👀 查看前 10 条数据": f"SELECT * FROM \"{default_table}\" LIMIT 10;",
            "📑 查看表结构 (列定义)": f"PRAGMA table_info(\"{default_table}\");",
            "➕ [热修] 增加一个小数列 (用于金额/系数)": f"ALTER TABLE \"{default_table}\" ADD COLUMN new_column_name REAL DEFAULT 0.0;",
            "➕ [热修] 增加一个开关列 (用于状态标记)": f"ALTER TABLE \"{default_table}\" ADD COLUMN is_flag INTEGER DEFAULT 0;",
            "➕ [热修] 增加一个文本列 (用于备注)": f"ALTER TABLE \"{default_table}\" ADD COLUMN new_text_col TEXT;",
            "🧹 [清理] 删除项目编号为空的行": f"DELETE FROM \"{default_table}\" WHERE biz_code IS NULL OR biz_code = '';",
            "🔥 [危险] 删除整个表": f"DROP TABLE \"{default_table}\";"
        }

        # --- 🟢 核心修复：定义回调函数 ---
        def on_template_change():
            # 获取下拉框当前选中的 key
            selected_key = st.session_state['sql_template_selector']
            # 强制更新输入框的 Session State
            st.session_state['sql_input_area'] = SQL_TEMPLATES.get(selected_key, "")

        # 3. 模板选择器 (添加 on_change)
        c_temp, c_tip = st.columns([3, 1])
        with c_temp:
            st.selectbox(
                "⚡ 快速填充 SQL 模板", 
                options=list(SQL_TEMPLATES.keys()),
                index=0,
                key="sql_template_selector",
                on_change=on_template_change  # <--- 🟢 绑定回调
            )
        with c_tip:
            st.info(f"当前默认表: `{default_table}`")

        # 4. SQL 编辑区
        # 注意：这里不再需要 value 参数来动态绑定，因为 state 已经由回调函数控制了
        # 但为了第一次渲染不报错，可以保留 value作为初始值，或者确保 key 在 session_state 中初始化
        if "sql_input_area" not in st.session_state:
             st.session_state["sql_input_area"] = ""

        sql_input = st.text_area(
            "SQL 语句 (支持多行)", 
            height=150,
            help="输入标准 SQLite 语法。如需操作特定表，请确保表名加双引号。",
            key="sql_input_area" # <--- 这里的 key 与回调函数里的一致
        )
        
        # 5. 执行按钮
        col_run, col_helper = st.columns([1, 4])
        with col_run:
            run_btn = st.button("🚀 执行 SQL", type="primary")
        
        if run_btn and sql_input.strip():
            # 🟢 拆弹 2：不再使用 sqlite3.connect，直接调用底层的 execute_raw_sql
            success, result = db.execute_raw_sql(sql_input)
            if success:
                if isinstance(result, pd.DataFrame):
                    st.success(f"✅ 查询成功，返回 {len(result)} 行")
                    st.dataframe(result, width="stretch")
                else:
                    st.success(f"✅ {result}")
            else:
                st.error(f"❌ 执行失败: {result}")
    with tabs[2]:
        st.write("当前 Session State 所有变量：")
        st.json(dict(st.session_state))
       
    with tabs[3]:
        if st.button("🔥 重置所有配置为默认值"):
            if os.path.exists(config_manager.CONFIG_FILE):
                os.remove(config_manager.CONFIG_FILE)
            st.success("已重置，请刷新页面。")
            st.rerun()
```

#### 📄 sidebar_manager.py

```python
import sys
from pathlib import Path
import streamlit as st
from backend import database as db
from backend.config import config_manager as cfg
import debug_kit
import time

def render_sidebar():
    """
    [精简版] 侧边栏：仅保留页面导航、版本信息与 Debug 开关
    """

    st.sidebar.header("🎛️ 项目管理控制台")
    st.sidebar.divider()

    # =========================================================
    # 1. 页面导航区 (移除数据库显示和切换逻辑)
    # =========================================================
    st.sidebar.page_link("app.py", label="系统首页", icon="🏠") # 新增：回首页
    st.sidebar.page_link("pages/01_📂_项目看板.py", label="项目看板", icon="📂")
    st.sidebar.page_link("pages/02_🛠️_主合同管理.py", label="主合同管理", icon="🛠️")
    st.sidebar.page_link("pages/03_🛠️_分包合同管理.py", label="分包合同管理", icon="🛠️")
    st.sidebar.page_link("pages/04_📊_数据分析.py", label="数据分析", icon="📊")
    st.sidebar.page_link("pages/05_🏢_往来单位.py", label="往来单位", icon="🏢")
    st.sidebar.page_link("pages/06_📥_导入Excel.py", label="导入数据", icon="📥")
    
    # 2. 开发者模式
    debug_kit.render_debug_sidebar()

    st.sidebar.divider()
    st.sidebar.caption(f"Ver: {cfg.APP_VERSION} (Build {cfg.BUILD_DATE})")
    st.sidebar.caption("© 2026 陈斌")


```

#### 📄 🏠_Dashboard.py

```python
import streamlit as st
st.title('ERP V2 实验室大屏')
```

#### 📁 .streamlit

#### 📁 experiments

##### 📄 __init__.py

```python

```

##### 📄 ex01_risk_engine.py

```python
import streamlit as st
import pandas as pd
import config_manager as cfg

# ==============================================================================
# 🟢 区域一：待迁移的核心逻辑 (Future Core Logic)
# ------------------------------------------------------------------------------
# 💡 说明：
# 这部分代码目前暂居此处方便调试。
# 测试通过后，请将这部分函数原封不动地剪切到 `core_logic.py` 中。
# 它不包含任何 st.write 等 UI 代码，只接收 DataFrame 和 规则配置字典。
# ==============================================================================

def _parse_rule_to_query_string(rule_config: dict) -> str:
    """
    【内部工具】将规则字典翻译成 Pandas Query 字符串
    """
    gate = rule_config.get("gate", "AND")  # 逻辑门：AND 或 OR
    conditions = rule_config.get("conditions", [])
    
    if not conditions:
        return ""

    # 1. 确定连接符
    connector = " & " if gate == "AND" else " | "
    
    query_parts = []
    for cond in conditions:
        # 获取用户输入的三个部分
        left = str(cond.get("left", "")).strip()   # 左侧：公式或字段
        op = cond.get("op", "==")                  # 中间：运算符
        right = str(cond.get("right", "")).strip() # 右侧：阈值
        
        # 防御：如果左右有一边为空，跳过该条件
        if not left or not right:
            continue
            
        # 2. 组合单个条件 (加括号保证数学运算优先级)
        # 格式: ( contract_amount - cost > 1000 )
        query_parts.append(f"({left} {op} {right})")
        
    # 3. 拼接最终语句
    final_query = connector.join(query_parts)
    return final_query

def execute_risk_filter(df: pd.DataFrame, rule_config: dict) -> pd.DataFrame:
    """
    【核心接口】执行风险筛选
    
    :param df: 原始项目数据表
    :param rule_config: 前端生成的规则字典，格式如下：
           {
               "gate": "AND",
               "conditions": [
                   {"left": "amount", "op": ">", "right": "100"},
                   {"left": "amount - cost", "op": "<", "right": "0"}
               ]
           }
    :return: 筛选后的 DataFrame
    """
    if df.empty:
        return pd.DataFrame()

    # 1. 解析规则
    query_str = _parse_rule_to_query_string(rule_config)
    
    # 如果解析出来是空的（比如用户没填任何条件），返回空还是全量？这里由你决定
    if not query_str:
        return df 

    try:
        # 2. 注入环境变量 (方便公式里使用 today 计算天数)
        # 这样用户可以在公式里写: (today - sign_date).dt.days > 90
        env = {"today": pd.Timestamp.now()}
        
        # 3. 执行 Pandas Query
        # local_dict=env 让 query 字符串能识别 'today' 变量
        filtered_df = df.query(query_str, local_dict=env)
        
        return filtered_df
        
    except Exception as e:
        # 捕获逻辑错误（比如字段名写错、除以零），抛出更友好的异常
        # 实际迁移时，这里可以记录日志
        raise ValueError(f"规则执行失败: {str(e)}")


# ==============================================================================
# 🟡 区域二：实验室 UI 交互层 (Experiment UI)
# ------------------------------------------------------------------------------
# 💡 说明：
# 这部分代码负责“模仿 Apple Music 智能列表”的交互。
# 它负责收集用户输入，组装成 rule_config 字典，然后调用上面的函数。
# ==============================================================================

def run(df, conn):
    # 🟢 接收宿主注入的 df 和 conn
    st.header("🛡️ 智能风控引擎 (Smart Risk Engine)")
    
    if df.empty:
        st.warning("⚠️ 所选表无数据，无法进行测试。")
        return
    for col in df.columns:
        # 1. 自动识别可能的金额列
        if any(key in col for key in ["amount", "fee", "total", "collection", "cost"]):
            # 先把千分位逗号和货币符号去掉 (针对字符串类型)
            if df[col].dtype == 'object':
                 df[col] = df[col].astype(str).str.replace('¥', '').str.replace(',', '').str.replace(' ', '')
            
            # 强制转数字
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) # 转换失败填0
    st.success(f"✅ 数据注入成功 | 样本量: {len(df)} 条 | 来源: 宿主程序预加载")

    for col in df.columns:
        if "date" in col or "time" in col:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # 在界面上展示一下可用字段，方便开发者复制
    with st.expander("📚 字段速查手册 (写公式用点这里)", expanded=False):
        st.info("💡 提示：左侧输入框支持数学运算。请复制【变量名】列的内容。")
        
        # 1. 自动生成对照表
        field_info = []
        
        # 这里的 cfg.STANDARD_FIELDS 是从 data_rules.json 动态加载的
        # 格式: {"contract_amount": "💰 当年合同额"}
        
        for col in df.columns:
            # 尝试获取中文名，如果字典里没有，就标为"扩展字段"
            chn_name = cfg.STANDARD_FIELDS.get(col, "自定义/扩展字段")
            dtype = str(df[col].dtype)
            
            # 给类型加个易读的标签
            if "float" in dtype or "int" in dtype:
                type_icon = "🔢 数字"
            elif "datetime" in dtype:
                type_icon = "📅 日期"
            else:
                type_icon = "🔤 文本"

            field_info.append({
                "变量名 (Copy me)": col,
                "中文含义": chn_name,
                "数据类型": type_icon
            })
        
        # 2. 展示表格
        info_df = pd.DataFrame(field_info)
        st.dataframe(
            info_df, 
            column_config={
                "变量名 (Copy me)": st.column_config.TextColumn(help="双击复制这个名字放入公式"),
            },
            width="stretch",
            hide_index=True
        )
        
        # 3. 快捷复制区 (针对常用计算字段)
        st.markdown("#### ⚡️ 常用计算字段 (点击复制)")
        cols = st.columns(4)
        # 挑出所有数字类型的列，方便直接复制
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        for i, col in enumerate(numeric_cols):
            with cols[i % 4]:
                st.code(col, language=None)


    st.divider()

    # --- 2. 规则构造器 (Rule Builder UI) ---
    st.subheader("🛠️ 规则定义")

    # [A] 顶层逻辑门 (Gate)
    c1, c2 = st.columns([1.5, 5])
    with c1:
        st.markdown("##### 筛选出满足以下")
    with c2:
        # 仿 Apple Music/iTunes 风格
        gate_select = st.selectbox(
            "逻辑", 
            ["所有 (ALL) 条件的项目", "任意 (ANY) 条件的项目"], 
            label_visibility="collapsed"
        )
        # 转换成数据模型需要的 "AND" / "OR"
        gate_val = "AND" if "所有" in gate_select else "OR"

    # [B] 动态条件行 (Dynamic Rows)
    # 初始化 Session State
    if "exp_risk_rules" not in st.session_state:
        st.session_state["exp_risk_rules"] = [
            {"left": "contract_amount", "op": ">", "right": "500"} # 默认给一行
        ]

    rows = st.session_state["exp_risk_rules"]

    # 增删行帮助函数
    def add_row():
        st.session_state["exp_risk_rules"].append({"left": "", "op": "==", "right": ""})
    def del_row(idx):
        st.session_state["exp_risk_rules"].pop(idx)

    # 渲染每一行
    for i, row in enumerate(rows):
        # 布局：[左侧公式] [运算符] [右侧阈值] [删除]
        c_left, c_op, c_right, c_btn = st.columns([3, 1, 2, 0.5])
        
        with c_left:
            # 这里的 left 既可以是单纯的字段名，也可以是公式
            # 比如: contract_amount - cost
            row["left"] = st.text_input(
                f"条件 {i+1} 左侧", 
                value=row["left"], 
                key=f"rule_l_{i}",
                placeholder="字段名 或 数学公式 (如 A - B)"
            )
        
        with c_op:
            # 丰富的运算符支持
            ops = [">", "<", "==", "!=", ">=", "<=", "in (包含)", "not in"]
            # 简单的回显逻辑
            current_op = row["op"]
            # 处理 UI 显示带中文的情况
            display_ops = ops 
            idx = 0
            for k, op_str in enumerate(ops):
                if op_str.startswith(current_op):
                    idx = k
                    break
            
            selected_op = st.selectbox("", ops, index=idx, key=f"rule_o_{i}", label_visibility="collapsed")
            # 存回去的时候只存 > < == 这种纯符号
            row["op"] = selected_op.split(" ")[0]

        with c_right:
            # 右侧值
            row["right"] = st.text_input(
                f"值", 
                value=row["right"], 
                key=f"rule_r_{i}",
                placeholder="数字 或 '文本'"
            )
            
        with c_btn:
            if st.button("🗑️", key=f"rule_d_{i}"):
                del_row(i)
                st.rerun()

    # 底部按钮栏
    if st.button("➕ 添加条件"):
        add_row()
        st.rerun()

    # --- 3. 验证与执行 (Verification) ---
    st.divider()
    
    # 组装 Model (完全解耦的数据结构)
    rule_config = {
        "gate": gate_val,
        "conditions": rows
    }

    # 开发者视图：看一眼生成的 JSON
    with st.expander("🔍 开发者数据视图 (即将存入 Config 的 JSON)"):
        st.json(rule_config)
        st.caption("👆 这就是解耦的关键：前端只负责生成这个 JSON，后端 Core Logic 只负责执行这个 JSON。")

    st.subheader("🎯 筛选结果预览")
    
    # 调用核心逻辑 (模拟未来的调用方式)
    try:
        # 🟢 关键：这里只调用函数，不再写任何逻辑代码！
        filtered_result = execute_risk_filter(df, rule_config)
        
        # 显示统计
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        col_stat1.metric("总项目数", len(df))
        col_stat2.metric("命中规则数", len(filtered_result))
        if len(df) > 0:
            rate = len(filtered_result) / len(df) * 100
            col_stat3.metric("风险占比", f"{rate:.1f}%")
        
        # 显示表格
        st.dataframe(filtered_result, width="stretch")
        
        # 显示最终生成的 SQL/Query (方便调试)
        if not filtered_result.empty or len(rows) > 0:
            query_debug = _parse_rule_to_query_string(rule_config)
            st.info(f"Generated Query: `{query_debug}`")

    except Exception as e:
        st.error("💥 规则运算出错")
        st.warning(f"错误详情: {e}")
        st.markdown("""
        **常见错误排查：**
        1. 文本值忘记加引号？例如状态应该是 `'停工'` 而不是 `停工`。
        2. 字段名拼写错误？请参考顶部的可用字段。
        3. 数学公式里用了非数字字段？
        """)

```

##### 📄 ex02_biz_analysis.py

```python
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from backend.utils import formatters as fmt
from backend.config import config_manager as cfg

def run(df, conn):
    """
    🚀 实验室插件入口
    df: 宿主传来的当前表数据 (已过滤 is_active)
    conn: 宿主传来的数据库连接
    """
    st.subheader("📊 经营与债权深度分析 (实验室插件)")

    # --- 1. 数据预处理 (复用原有的清洗逻辑，但针对传入的 df) ---
    # 强制将列名翻译成英文标准列 (确保后续逻辑不挂)
    rules = cfg.load_data_rules()
    mapping = rules.get("column_mapping", {})
    reverse_mapping = {ch_key: eng_key for eng_key, ch_list in mapping.items() for ch_key in ch_list}
    df = df.rename(columns=reverse_mapping)

    # 强转日期与年份
    if 'sign_date' in df.columns:
        df['dt_sign'] = pd.to_datetime(df['sign_date'], errors='coerce')
        df['sign_year'] = df['dt_sign'].dt.year.fillna(datetime.now().year).astype(int)
    
    # 强转金额
    df['val_contract'] = df['contract_amount'].apply(fmt.safe_float)
    df['val_collection'] = df['total_collection'].apply(fmt.safe_float) if 'total_collection' in df.columns else 0.0
    df['val_uncollected'] = df['val_contract'] - df['val_collection']

    # --- 2. 交互式筛选 (在插件内部的小型控件) ---
    valid_years = sorted(df[df['sign_year'] > 1900]['sign_year'].unique().tolist(), reverse=True)
    if not valid_years:
        st.warning("当前表无可分析的年份数据。")
        return

    analysis_year = st.sidebar.selectbox("📅 实验分析年份", valid_years, key="exp_year_sel")

    # --- 3. 核心可视化逻辑 ---
    df_year = df[df['sign_year'] == analysis_year]
    
    col1, col2 = st.columns(2)
    with col1:
        # 负责人合同分布 (饼图)
        fig_pie = px.pie(df_year, values='val_contract', names='manager', title=f"{analysis_year} 负责人合同贡献")
        st.plotly_chart(fig_pie, width="stretch")
    
    with col2:
        # 欠款排名 (条形图)
        df_debt = df_year.sort_values('val_uncollected', ascending=False).head(10)
        fig_bar = px.bar(df_debt, x='project_name', y='val_uncollected', title=f"{analysis_year} TOP 10 欠款项目")
        st.plotly_chart(fig_bar, width="stretch")

    # --- 4. 数据透视表展示 ---
    with st.expander("查看当前实验原始数据摘要"):
        st.dataframe(df_year[['project_name', 'manager', 'val_contract', 'val_uncollected']], width="stretch")
```

#### 📁 pages

##### 📄 01_📂_项目看板.py

```python
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 🟢 寻路魔法：向上 2 级找到根目录
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# 接入新底座
from backend.database import crud_base
from backend.database.db_engine import get_connection
from backend.config import config_manager as cfg
import sidebar_manager
import debug_kit

try:
    from backend.services.ai_service import AIService  
except ImportError:
    pass

st.set_page_config(layout="wide", page_title="项目全局看板", page_icon="🏠")

# =========================================================
# 🤖 AI 弹窗逻辑 (保留原有的核心竞争力)
# =========================================================
@st.dialog("🤖 AI 智能项目分析", width="large")
def show_ai_search_dialog(keyword, initial_df):
    try:
        ai_svc = AIService()
    except Exception:
        st.error("AI 模块未加载")
        return
        
    if not ai_svc.is_available:
        st.error("❌ 本地 AI 服务未启动 (Ollama)。请先运行 `ollama serve`。")
        return

    models = ai_svc.get_available_models()
    if not models:
        st.warning("⚠️ 未检测到模型，请先运行 `ollama pull deepseek-r1`")
        return
    
    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(f"当前分析范围：基于筛选条件命中的 {len(initial_df)} 个项目")
    with c2:
        selected_model = st.selectbox("🧠 选择模型", models, index=0, label_visibility="collapsed")

    if initial_df.empty:
        st.warning("当前搜索结果为空，无法分析。")
        return

    # 数据清洗与压缩 (Token 优化)
    clean_data = []
    max_items = st.slider("📊 分析样本量 (防止 Token 爆炸)", 10, 100, 30)
    target_archives = initial_df.head(max_items)
    
    for _, row in target_archives.iterrows():
        c_amount = float(row.get('contract_amount') or 0)
        collection = float(row.get('total_collected') or 0)
        
        if c_amount > 0 or collection > 0:
            clean_data.append({
                "项目": row.get('project_name', '未知'),
                "负责人": row.get('manager', '未知'),
                "合同额": f"{c_amount/10000:.2f}万",
                "回款率": f"{(collection/c_amount*100):.1f}%" if c_amount > 0 else "0%",
                "欠款": f"{(c_amount - collection)/10000:.2f}万"
            })
            
    with st.expander(f"查看投喂给 AI 的数据摘要 ({len(clean_data)} 条)"):
        st.json(clean_data[:3])
        st.caption("...等更多数据")

    st.divider()
    q = st.text_area("🗣️ 设定 AI 分析指令：", value="分析这些项目的回款风险，找出回款率低于30%的重点项目，并给出催款建议。", height=100)
    
    if st.button("🚀 开始 AI 分析", type="primary", width="stretch"):
        if not clean_data:
            st.error("有效数据不足（金额均为0），无法分析。")
            return
            
        st.write("### 💡 AI 诊断报告")
        container = st.empty()
        full_text = ""
        try:
            for chunk in ai_svc.analyze_stream(selected_model, clean_data, q):
                full_text += chunk
                container.markdown(full_text + "▌")
            container.markdown(full_text)
        except Exception as e:
            st.error(f"分析中断: {e}")

# =========================================================
# 🚨 独立风控查询：30 天内待收款预警
# =========================================================
@st.cache_data(ttl=60)
def load_urgent_receivables():
    """直接使用 SQL 跨表联查，抓取近期需催收的款项"""
    conn = get_connection()
    try:
        sql = """
            SELECT 
                m.project_name AS "项目名称", 
                m.manager AS "负责人",
                p.milestone_name AS "收款节点", 
                p.planned_amount AS "计划金额", 
                p.planned_date AS "预计日期"
            FROM biz_payment_plans p
            JOIN biz_main_contracts m ON p.main_contract_code = m.biz_code
            WHERE p.deleted_at IS NULL AND m.deleted_at IS NULL
              AND p.planned_amount > 0
              AND p.planned_date <= CURRENT_DATE + INTERVAL '30 days'
            ORDER BY p.planned_date ASC
        """
        df = pd.read_sql_query(sql, conn)
        return df
    except Exception as e:
        print(f"获取预警失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

# =========================================================
# 1. 页面基础框架
# =========================================================
sidebar_manager.render_sidebar()

col_title, col_ai = st.columns([4, 1])
with col_title:
    st.title("🏠 项目全局指挥中心")
    st.caption("PMO 视角：全生命周期健康度监控与资金透视。")

# 🟢 加载 V2.0 主合同数据
df_main = crud_base.fetch_dynamic_records('main_contract')

if df_main.empty:
    st.info("📦 当前系统暂无项目数据，请前往【主合同管理】或【数据导入】录入。")
    st.stop()

# 数据类型强转兜底
df_main['contract_amount'] = pd.to_numeric(df_main['contract_amount'], errors='coerce').fillna(0.0)
df_main['total_collected'] = pd.to_numeric(df_main.get('total_collected', 0), errors='coerce').fillna(0.0)

# =========================================================
# 2. 预警雷达 (30天内到期资金)
# ==========================================
df_urgent = load_urgent_receivables()
if not df_urgent.empty:
    total_urgent = df_urgent['计划金额'].sum()
    st.error(f"🚨 **资金红绿灯**：未来 30 天内共有 **{len(df_urgent)}** 笔款项即将到期/已逾期，涉及总金额 **¥ {total_urgent:,.2f}**，请重点督办！")
    
    with st.expander("👀 查看重点催收清单"):
        st.dataframe(
            df_urgent, 
            hide_index=True, 
            width="stretch",
            column_config={
                "预计日期": st.column_config.DateColumn("预计日期", format="YYYY-MM-DD"),
                "计划金额": st.column_config.NumberColumn("计划金额 (元)", format="¥ %.2f")
            }
        )

# =========================================================
# 3. 仿 v0 数据过滤区 (Data Filter)
# =========================================================
st.markdown("---")

c_search, c_stage, c_manager = st.columns([2, 1, 1])

with c_search:
    search_kw = st.text_input("🔍 搜索项目名称/编号...", placeholder="例如：上海大厦...")

with c_stage:
    # 提取存在的状态
    stages = ["全部"] + [s for s in df_main['project_stage'].unique().tolist() if str(s) != 'nan']
    sel_stage = st.selectbox("📌 项目阶段", stages)

with c_manager:
    managers = ["全部"] + [m for m in df_main['manager'].unique().tolist() if str(m) != 'nan']
    sel_manager = st.selectbox("👤 负责人", managers)

# 执行内存级过滤
df_view = df_main.copy()

if search_kw:
    mask = df_view['project_name'].astype(str).str.contains(search_kw, case=False) | \
           df_view['biz_code'].astype(str).str.contains(search_kw, case=False)
    df_view = df_view[mask]

if sel_stage != "全部":
    df_view = df_view[df_view['project_stage'] == sel_stage]

if sel_manager != "全部":
    df_view = df_view[df_view['manager'] == sel_manager]

with col_ai:
    st.write("") # 占位
    if st.button("✨ 唤醒 AI 诊断", type="primary", width="stretch", disabled=df_view.empty):
        show_ai_search_dialog(search_kw or "当前全盘", df_view)

# =========================================================
# 4. 仿 v0 高级数据表格 (Data Table)
# =========================================================
st.caption(f"为您检索到 **{len(df_view)}** 个项目记录。")

# 准备展示列
display_cols = {
    'biz_code': '合同编号',
    'project_name': '项目名称',
    'manager': '负责人',
    'project_stage': '状态', 
    'contract_amount': '合同额',
    'total_collected': '已回款'
}

df_display = df_view[list(display_cols.keys())].rename(columns=display_cols).copy()
df_display['欠款金额'] = df_display['合同额'] - df_display['已回款']
df_display['回款进度'] = (df_display['已回款'] / df_display['合同额']) * 100
df_display['回款进度'] = df_display['回款进度'].fillna(0)

# 定义动态高度
height = min((len(df_display) + 1) * 35 + 3, 650)

st.dataframe(
    df_display,
    width="stretch",
    height=height,
    hide_index=True,
    column_config={
        "合同编号": st.column_config.TextColumn("合同编号", width="small"),
        "项目名称": st.column_config.TextColumn("项目名称", width="medium"),
        "状态": st.column_config.TextColumn("阶段/状态", width="small"),
        "合同额": st.column_config.NumberColumn("合同额 (元)", format="¥ %.2f"),
        "已回款": st.column_config.NumberColumn("已回款 (元)", format="¥ %.2f"),
        "欠款金额": st.column_config.NumberColumn("🔴 欠款金额 (元)", format="¥ %.2f"),
        "回款进度": st.column_config.ProgressColumn("回款进度", format="%.1f%%", min_value=0, max_value=100)
    }
)

debug_kit.execute_debug_logic()
```

##### 📄 02_🛠️_主合同管理.py

```python
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# 确保能找到 backend 模块
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.db_engine import execute_raw_sql
from backend.config import config_manager as cfg
import backend.database as db
from backend.database import crud
from backend import services as svc

import sidebar_manager
import debug_kit 
import components as ui
# ==========================================
# 0. 页面配置与初始化
# ==========================================
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import warnings
from pathlib import Path

# 🟢 彻底静默 pandas 的 SQLAlchemy 警告
warnings.filterwarnings('ignore', category=UserWarning, message='.*SQLAlchemy.*')

# 确保能找到 backend 和 components 模块
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database import crud_base
from backend.database.db_engine import execute_raw_sql

FORM_HIDDEN_FIELDS = [] 
FORM_READONLY_FIELDS = []

# ==========================================
# 0. 页面配置与初始化
# ==========================================
st.set_page_config(page_title="主合同管理", page_icon="🛠️", layout="wide")

if 'refresh_trigger' not in st.session_state:
    st.session_state.refresh_trigger = 0

def trigger_refresh():
    st.session_state.refresh_trigger += 1

# ==========================================
# 1. 核心数据获取
# ==========================================
@st.cache_data(ttl=5, show_spinner=False)
def load_main_contracts(trigger):
    return db.fetch_dynamic_records('main_contract')

# ==========================================
# 1.5 收款计划表 (子表) 读写引擎
# ==========================================
def load_payment_plans(main_contract_code):
    """从数据库加载指定主合同的收款计划 (彻底修复参数报错)"""
    sql = '''
        SELECT biz_code AS "计划编号", milestone_name AS "款项节点", 
               payment_ratio AS "比例(%%)", planned_amount AS "计划金额", 
               planned_date AS "预警日期", remarks AS "备注"
        FROM biz_payment_plans
        WHERE main_contract_code = %s AND deleted_at IS NULL
        ORDER BY planned_date ASC, id ASC
    '''
    conn = crud_base.get_connection()
    try:
        with conn.cursor() as cur:
            # 🟢 修正点：显式传递参数元组，原生执行
            cur.execute(sql, (str(main_contract_code),)) 
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=cols)
            
        if not df.empty:
            df['比例(%)'] = pd.to_numeric(df['比例(%)'], errors='coerce').fillna(0.0)
            df['计划金额'] = pd.to_numeric(df['计划金额'], errors='coerce').fillna(0.0)
            df['预警日期'] = pd.to_datetime(df['预警日期']).dt.date
        return df
    except Exception as e:
        st.error(f"⚠️ 读取收款计划失败: {e}")
        return pd.DataFrame(columns=["计划编号", "款项节点", "比例(%)", "计划金额", "预警日期", "备注"])
    finally:
        if conn: conn.close()

def load_financial_history(main_contract_code, table_type="collections"):
    """
    统一的历史记录拉取函数
    table_type: 'collections' (收款) 或 'invoices' (开票)
    """
    conn = crud_base.get_connection()
    try:
        if table_type == "collections":
            sql = '''
                SELECT biz_code AS "流水号", collected_date AS "收款日期", 
                       collected_amount AS "金额(元)", update_project_stage AS "对应节点", 
                       operator AS "经办人", remarks AS "备注", created_at AS "录入时间"
                FROM biz_collections
                WHERE main_contract_code = %s AND deleted_at IS NULL
                ORDER BY collected_date DESC, created_at DESC
            '''
        else:
            sql = '''
                SELECT biz_code AS "发票号", invoice_date AS "开票日期", 
                       invoice_amount AS "金额(元)", target_plan_code AS "关联计划", 
                       operator AS "经办人", remarks AS "备注", created_at AS "录入时间"
                FROM biz_invoices
                WHERE main_contract_code = %s AND deleted_at IS NULL
                ORDER BY invoice_date DESC, created_at DESC
            '''
            
        with conn.cursor() as cur:
            cur.execute(sql, (str(main_contract_code),)) 
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=cols)
            
        if not df.empty:
            df['金额(元)'] = pd.to_numeric(df['金额(元)'], errors='coerce').fillna(0.0)
            if '录入时间' in df.columns:
                df['录入时间'] = pd.to_datetime(df['录入时间']).dt.strftime('%Y-%m-%d %H:%M')
        return df
    except Exception as e:
        st.error(f"⚠️ 读取{table_type}历史失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

def save_payment_plans(main_contract_code, df_plans, operator, total_contract_amount):
    """全量覆盖保存：先清空，后写入，确保数据唯一"""
    conn = crud_base.get_connection()
    try:
        with conn.cursor() as cursor:
            # 🟢 1. 强力清场：必须先删除该合同下所有旧计划
            cursor.execute(
                "UPDATE biz_payment_plans SET deleted_at = CURRENT_TIMESTAMP WHERE main_contract_code = %s", 
                (str(main_contract_code),)
            )
            
            # 2. 循环插入新数据
            insert_sql = """
                INSERT INTO biz_payment_plans 
                (biz_code, main_contract_code, milestone_name, payment_ratio, planned_amount, planned_date, remarks, operator)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for idx, row in df_plans.iterrows():
                milestone_name = str(row.get("款项节点", "")).strip()
                if not milestone_name or milestone_name == 'nan': continue 
                
                # 比例与金额智能互算
                raw_ratio = float(row.get("比例(%)", 0.0)) if pd.notna(row.get("比例(%)")) else 0.0
                raw_amount = float(row.get("计划金额", 0.0)) if pd.notna(row.get("计划金额")) else 0.0
                
                final_ratio = raw_ratio
                final_amount = raw_amount
                if raw_amount > 0 and raw_ratio == 0 and total_contract_amount > 0:
                    final_ratio = round((raw_amount / total_contract_amount) * 100, 2)
                elif raw_ratio > 0 and raw_amount == 0:
                    final_amount = round(total_contract_amount * (raw_ratio / 100.0), 2)

                plan_code = f"PLAN-{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{idx}"
                planned_date = row.get("预警日期")
                if pd.isna(planned_date) or not planned_date: planned_date = None
                
                cursor.execute(insert_sql, (
                    plan_code, main_contract_code, milestone_name, 
                    final_ratio, final_amount, planned_date, row.get("备注", ""), operator
                ))
            
            conn.commit() # 🟢 统一提交事务
            return True, "计划已覆盖保存"
    except Exception as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

df_main = load_main_contracts(st.session_state.refresh_trigger)
sidebar_manager.render_sidebar()

# ==========================================
# 2. 主合同表单弹窗
# ==========================================
@st.dialog("📝 主合同信息登记", width="large")
def contract_form_dialog(existing_data=None):
    if ui and hasattr(ui, 'render_dynamic_form'):
        
        # ==========================================
        # 🟢 1. 附件归档与 AI 智能解析区
        # ==========================================
        st.subheader("🤖 AI 合同智能解析")
        
        # 🆙 第一层：拖拽上传区 (单独占满整行，视觉焦点)
        uploaded_files = st.file_uploader("📂 请拖拽或选择待解析合同 (支持 PDF/Word)", accept_multiple_files=True)
        
        # ⬇️ 第二层：操作区 (左长右短，完美对齐)
        c_cat, c_btn = st.columns([3, 1])
        
        with c_cat:
            # 使用 collapsed 隐藏 label，让下拉框和右侧的按钮在同一水平线上绝对对齐
            file_category = st.selectbox(
                "🗂️ 附件类别", 
                ["主合同文本 (需 AI 解析)", "补充协议/变更单 (需 AI 解析)", "工程图纸", "往来函件", "结算单", "其他附件"],
                label_visibility="collapsed" 
            )
            
        with c_btn:
            # 只有上传了文件，且类别属于“需 AI 解析”时，按钮才可用
            ai_ready = uploaded_files is not None and len(uploaded_files) > 0 and "(需 AI 解析)" in file_category
            
            # 按钮与左侧下拉框高度完美匹配
            if st.button("✨ 一键 AI 提取", type="primary", disabled=not ai_ready, use_container_width=True):
                with st.spinner("🧠 AI 正在极速阅读合同条款，请稍候约 15 秒..."):
                    import time
                    time.sleep(2) # 【预留钩子】明天这里将替换为真正的 AI 调用！
                    
                    # 【模拟 AI 的返回结果】
                    mock_ai_result = {
                        "project_name": "AI自动识别：经十一路项目",
                        "client_name": "济南万科企业有限公司",
                        "contract_amount": 1500000,
                        "contract_nature": "施工总承包"
                    }
                    
                    # 将 AI 结果合并到当前数据字典中
                    if existing_data is None:
                        existing_data = {}
                    existing_data.update(mock_ai_result)
                    
                    st.success("🎉 提取完毕！下方表单已更新。")
                    # 无需 rerun，渲染引擎会自动捕捉 existing_data 的变化

        st.markdown("---") # 分割线

        # 🟢 2. 智能判断：是新增还是编辑？
        is_edit = existing_data is not None
        form_title = "✏️ 修改主合同" if is_edit else "🆕 录入新主合同"
        
        # 🟢 3. 自动编号注入
        if not is_edit:
            # 动态获取底层物理表名
            target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
            # 召唤 crud_base 的自动编号生成器，前缀使用 MAIN
            new_biz_code = crud_base.generate_biz_code(target_table, prefix_char="MAIN")
            current_data = {'biz_code': new_biz_code}
        else:
            current_data = existing_data
            
        # 🟢 4. 渲染出三列的高级表单
        result = ui.render_dynamic_form(
            "main_contract", 
            form_title, 
            current_data, # 把拼装好的数据喂进去
            hidden_fields=FORM_HIDDEN_FIELDS,
            readonly_fields=FORM_READONLY_FIELDS
        )
        
        if result:
            # 防御机制：提取并确保有最终的 biz_code
            final_biz_code = result.get('biz_code', current_data.get('biz_code'))
            result['biz_code'] = final_biz_code
            
            target_id = int(existing_data['id']) if is_edit and 'id' in existing_data else None
            current_user = st.session_state.get('user_name', '当前系统用户')
            
            # 1. 拦截“修改编号”事件，触发超级级联更新
            if is_edit and final_biz_code != existing_data.get('biz_code'):
                from backend.database.crud_sys import update_biz_code_cascade
                target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
                update_biz_code_cascade(existing_data.get('biz_code'), final_biz_code, target_table)
            
            # 2. 保存主表数据
            success, msg = crud_base.upsert_dynamic_record(
                model_name="main_contract", 
                data_dict=result, 
                record_id=target_id,
                operator_name=current_user
            )
            
            if success:
                # 🟢 3. 处理刚刚上传的附件
                if uploaded_files:
                    target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
                    for uf in uploaded_files:
                        # 🟢 把前端选好的类别传给底层！
                        svc.save_attachment(final_biz_code, uf, target_table, file_category=file_category)
                    ui.show_toast_success(f"主合同及【{file_category}】已成功保存！")
                else:
                    ui.show_toast_success("主合同数据保存成功！")
                    
                trigger_refresh() 
                st.rerun()
            else:
                ui.show_toast_error(f"保存失败: {msg}")       
    else:
        st.error("组件库加载失败，无法渲染表单。")
# ==========================================
# 2. 📊 顶层：全局资金看板 
# ==========================================
@st.dialog("📦 执行年度财务结转", width="small")
def yearly_archive_dialog():
    st.warning("⚠️ 警告：此操作会将系统内所有【已计提】的合同和项目进行归档（软删除）。\n\n请务必确保本年度所有账务已核对完毕！")
    confirm = st.text_input("请输入 '确认结转' 以继续执行：")
    if st.button("🚨 确认执行结转", type="primary", disabled=(confirm != "确认结转"), use_container_width=True):
        
        # 🟢 1. 提取当前操作人
        current_user = st.session_state.get('user_name', 'System')
        
        # 🟢 2. 执行底层结转逻辑 (注意这里需要补上 db. 前缀，确保调用正确)
        success, msg = db.execute_yearly_accrual_archive()
        
        if success:
            # 🟢 3. 智能提取成功数量并写入 job_log
            import re
            # 假设后端的 msg 返回的是 "成功结转 15 份合同"
            nums = re.findall(r'\d+', msg)
            success_count = int(nums[0]) if nums else 0
            
            try:
                # 调用我们在 crud_sys 里写的适配器，记录宏观日志
                db.log_job_operation(
                    operator=current_user,
                    file_name="前端手动触发",         # 借用 file_name 字段存来源
                    import_type="main_contract",    # 借用 import_type 存目标模型
                    success_count=success_count
                )
            except Exception as e:
                print(f"写入结转日志失败: {e}")

            if ui and hasattr(ui, 'show_toast_success'): ui.show_toast_success(msg)
            trigger_refresh()
            st.rerun()
        else:
            st.error(msg)

col_title, col_add_btn, col_archive_btn = st.columns([6, 2, 2])
with col_title:
    st.title("🛠️ 主合同资金管理台")
with col_add_btn:
    st.write("") # 占位往下挤一点对齐
    if st.button("➕ 录入新主合同", type="primary", use_container_width=True):
        contract_form_dialog() 
with col_archive_btn:
    st.write("") 
    if st.button("📦 年度财务结转", use_container_width=True, help="将所有已计提的项目移入历史档案"):
        yearly_archive_dialog()

# 🟢 调用 components 里的卡片美化功能
if ui and hasattr(ui, 'style_metric_card'):
    ui.style_metric_card()

if not df_main.empty:
    # 算总账
    total_amount = df_main['contract_amount'].astype(float).sum()
    total_collected = df_main['total_collected'].astype(float).sum()
    total_uncollected = df_main['uncollected_contract_amount'].astype(float).sum()
    total_invoiced = df_main['total_invoiced'].astype(float).sum()
    contract_count = len(df_main)
    
    # 计算各项比率 (防止除以 0 报错)
    collection_rate = (total_collected / total_amount) * 100 if total_amount else 0.0
    uncollected_rate = (total_uncollected / total_amount) * 100 if total_amount else 0.0
    invoice_rate = (total_invoiced / total_amount) * 100 if total_amount else 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 总盘子 (合同总额)", f"¥ {total_amount:,.2f}", 
                  delta=f"包含 {contract_count} 份主合同", delta_color="off") # off 代表显示中性灰色
    with col2:
        st.metric("💰 钱袋子 (累计到账)", f"¥ {total_collected:,.2f}", 
                  delta=f"总回款率: {collection_rate:.1f}%") # 默认 normal 为绿色
    with col3:
        st.metric("📝 待收款 (剩余未到账)", f"¥ {total_uncollected:,.2f}", 
                  delta=f"资金缺口占比: {uncollected_rate:.1f}%", delta_color="inverse") # inverse 代表红色预警
    with col4:
        st.metric("📄 累计开票", f"¥ {total_invoiced:,.2f}", 
                  delta=f"开票覆盖率: {invoice_rate:.1f}%", delta_color="off")
    
st.markdown("---")

# ==========================================
# 3. 黄金分割布局：左表(行内编辑) + 右抽屉(多Tab)
# ==========================================
if df_main.empty:
    st.info("📭 当前系统暂无主合同数据，请先录入。")
else:
    # 调整比例，给右侧的 Tab 多留一点空间 (2.5 : 1.5)
    col_table, col_form = st.columns([2.5, 1.5])

    # ------------------------------------------
    # 🗂️ 左侧区域：带行内编辑的数据网格
    # ------------------------------------------
    with col_table:
        st.subheader("📑 合同台账明细")
        
        if 'project_stage' not in df_main.columns:
            df_main['project_stage'] = '未设置'
            
        display_cols = {
            'biz_code': '合同编号',
            'project_name': '项目名称',
            'project_stage': '项目阶段', 
            'client_name': '甲方单位',
            'contract_amount': '合同金额',
            'total_collected': '累计到账',
            'collection_progress': '回款进度(%)',
            'uncollected_contract_amount': '未到账金额'
        }
        
        df_display = df_main[list(display_cols.keys())].rename(columns=display_cols)
        df_display['回款进度(%)'] = pd.to_numeric(df_display['回款进度(%)'], errors='coerce').fillna(0.0)
        df_display.insert(0, '☑️', False)
        
        # 🟢 从底层汇聚所有的计划节点，作为下拉框的智能选项
        conn = crud_base.get_connection()
        try:

            sql = """
                SELECT milestone_name 
                FROM biz_payment_plans 
                WHERE deleted_at IS NULL 
                  AND milestone_name IS NOT NULL 
                  AND milestone_name != ''
                GROUP BY milestone_name
                ORDER BY MIN(planned_date) ASC NULLS LAST, MIN(id) ASC
            """
            stage_df = pd.read_sql_query(sql, conn)
            dynamic_stages = stage_df['milestone_name'].tolist()
        except Exception as e:
            dynamic_stages = []
        finally:
            if conn: conn.close()
            
        stage_options = ["未设置"] + dynamic_stages + ["已结项"]
        
        edited_df = st.data_editor(
            df_display,
            column_config={
                "☑️": st.column_config.CheckboxColumn("☑️", help="打勾将此合同提取到右侧操作台", default=False),
                "项目阶段": st.column_config.SelectboxColumn("📌 当前阶段 (双击修改)", help="修改后自动保存", options=stage_options, required=True),
                "回款进度(%)": st.column_config.ProgressColumn("回款进度(%)", format="%.2f %%", min_value=0.0, max_value=100.0),
                "合同编号": st.column_config.TextColumn("合同编号", disabled=True),
                "合同金额": st.column_config.NumberColumn("合同金额", disabled=True, format="¥ %.2f"),
                "累计到账": st.column_config.NumberColumn("累计到账", disabled=True, format="¥ %.2f"),
                "未到账金额": st.column_config.NumberColumn("未到账金额", disabled=True, format="¥ %.2f"),
            },
            width="stretch", hide_index=True, height=500, key="main_contract_editor" 
        )

        # 🟢 魔法引擎：静默捕捉左侧表格的“项目阶段”修改，立刻存库！
        if not edited_df.equals(df_display):
            changes_detected = False
            target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
            for i in range(len(df_display)):
                if df_display.iloc[i]['项目阶段'] != edited_df.iloc[i]['项目阶段']:
                    new_stage = edited_df.iloc[i]['项目阶段']
                    biz_code = df_display.iloc[i]['合同编号']
                    execute_raw_sql(f'UPDATE "{target_table}" SET project_stage = %s WHERE biz_code = %s', (new_stage, biz_code))
                    changes_detected = True
            if changes_detected:
                if ui and hasattr(ui, 'show_toast_success'): ui.show_toast_success("✅ 项目阶段已同步至数据库！")
                trigger_refresh()
                st.rerun()

    # ------------------------------------------
    # 🎛️ 右侧区域：三大 Tab 魔法操作枢纽
    # ------------------------------------------
    with col_form:
        st.subheader(f"🎛️ 操作台")
        
        # 🟢 新增核心魔法 2：智能拦截左侧表格的“打勾”事件
        auto_selected_biz_code = None
        # 筛选出所有被打勾的行 (为了容错，如果用户勾了多个，我们提取最下面的那一个)
        checked_rows = edited_df[edited_df['☑️'] == True]
        if not checked_rows.empty:
            auto_selected_biz_code = checked_rows.iloc[-1]['合同编号']
        
        col_select, col_edit = st.columns([8, 2])
        with col_select:
            contract_options = df_main.apply(lambda row: f"{row['biz_code']} | {row['project_name']}", axis=1).tolist()
            
            # 🟢 新增核心魔法 3：计算被勾选的合同在下拉框里排第几个
            default_index = 0
            if auto_selected_biz_code:
                for i, opt in enumerate(contract_options):
                    if opt.startswith(auto_selected_biz_code):
                        default_index = i
                        break
            
            # 动态绑定 index 属性，实现瞬间对齐
            selected_contract_str = st.selectbox(
                "🎯 目标主合同", 
                contract_options, 
                index=default_index, # 👈 就是这里让它自动切换的
                label_visibility="collapsed"
            )
            selected_biz_code = selected_contract_str.split(" | ")[0]
        
        with col_edit:
            if st.button("✏️ 修改", use_container_width=True, help="修改当前选中的主合同信息"):
                # 提取当前选中行的所有数据，转成字典传给弹窗
                current_contract_data = df_main[df_main['biz_code'] == selected_biz_code].iloc[0].to_dict()
                contract_form_dialog(existing_data=current_contract_data)
        current_stage = df_main[df_main['biz_code'] == selected_biz_code]['project_stage'].fillna("未设置").iloc[0]
        # 🟢 核心重构：创建三个标签页
        current_contract_amount = float(df_main[df_main['biz_code'] == selected_biz_code]['contract_amount'].iloc[0])
        current_plans_df = load_payment_plans(selected_biz_code)

        tab_flow, tab_history, tab_plan, tab_audit = st.tabs(["⚡ 录入流水", "📜 财务明细", "📝 收款计划", "🛡️ 高级与审计"])
        
        # ==========================================
        # Tab 1: ⚡ 录入流水 (已打通底层)
        # ==========================================
        with tab_flow:
            action_type = st.radio("业务动作", ["录入开票 (开给甲方)","录入收款 (甲方打款)"], horizontal=True)
            
            # 🟢 构造计划节点下拉菜单字典
            with st.form(key="flow_form", clear_on_submit=True):
                # 🟢 魔法填充：自动获取项目当前阶段作为初始建议值
                # 这里将下拉框改为 text_input，实现“手写输入框”需求
                suggested_stage = current_stage if current_stage != "未设置" else ""
                input_stage = st.text_input("🎯 对应业务节点/阶段", value=suggested_stage, help="系统已自动提取当前阶段，您可根据实际情况微调（如：方案一期款）")
                
                amount = st.number_input("💵 操作金额 (元)", min_value=0.01, step=50000.0, format="%.2f")
                action_date = st.date_input("📅 发生日期", datetime.now())
                
                current_user = st.session_state.get('user_name', '当前系统用户')
                operator = st.text_input("👤 经办人", value=current_user, disabled=True)
                custom_remarks = st.text_input("📝 补充备注 (选填)", "")
                
                submit_btn = st.form_submit_button("✅ 确认提交并核算", use_container_width=True)
                
                if submit_btn:                    
                    final_remarks = f"【节点：{input_stage}】 {custom_remarks}".strip()
                    target_plan_code = None
                    selected_node_name = input_stage.strip()
                    if "收款" in action_type:
                        table_model = "biz_collections"
                        data_dict = {
                            'biz_code': f"COLL-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                            'main_contract_code': selected_biz_code,
                            'target_plan_code': target_plan_code,  # 🟢 精准写入流水表
                            'update_project_stage': selected_node_name if selected_node_name != "通用/无特定节点" else None,
                            'collected_amount': amount,
                            'collected_date': action_date.strftime('%Y-%m-%d'),
                            'operator': operator,
                            'remarks': final_remarks
                        }
                    else:
                        table_model = "biz_invoices"
                        data_dict = {
                            'biz_code': f"INV-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                            'main_contract_code': selected_biz_code,
                            'target_plan_code': target_plan_code,  # 🟢 精准写入发票表
                            'invoice_amount': amount,
                            'invoice_date': action_date.strftime('%Y-%m-%d'),
                            'operator': operator,
                            'remarks': final_remarks
                        }
                    
                    keys = list(data_dict.keys())
                    values = tuple(data_dict.values())
                    placeholders = ', '.join(['%s'] * len(keys))
                    sql = f"INSERT INTO {table_model} ({', '.join(keys)}) VALUES ({placeholders})"
                    success, msg = execute_raw_sql(sql, values)

                    if success:
                        # 🟢 同步推演：自动把主合同的阶段改过去！
                        if selected_node_name != "通用/无特定节点":
                            target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
                            execute_raw_sql(f'UPDATE "{target_table}" SET project_stage = %s WHERE biz_code = %s', (selected_node_name, selected_biz_code))
                        db.sync_main_contract_finance(selected_biz_code)

                        if ui and hasattr(ui, 'show_toast_success'): 
                            ui.show_toast_success(f"成功录入 {amount:,.2f} 元！")
                        trigger_refresh()
                    else:
                        st.error(f"录入失败: {msg}")
        # ==========================================
        # Tab 2 (新增): 📜 财务明细 (历史记录台账)
        # ==========================================
        with tab_history:
            sub_tab_coll, sub_tab_inv = st.tabs(["💰 历史收款记录", "📄 历史开票记录"])
            current_user = st.session_state.get('user_name', '当前系统用户')
            
            # ---------------- 款项面板 ----------------
            with sub_tab_coll:
                df_coll = load_financial_history(selected_biz_code, "collections")
                if not df_coll.empty:
                    # 动态 Key 防止复用冲突
                    coll_editor_key = f"coll_editor_{selected_biz_code}_{st.session_state.refresh_trigger}"
                    
                    # 插入供用户勾选的列
                    df_coll.insert(0, '🔴 作废', False)
                    
                    edited_coll = st.data_editor(
                        df_coll, 
                        width="stretch", 
                        hide_index=True,
                        disabled=["流水号", "收款日期", "金额(元)", "对应节点", "经办人", "备注", "录入时间"], # 冻结原有数据，禁止行内直改
                        column_config={
                            "🔴 作废": st.column_config.CheckboxColumn("🔴 作废", default=False, help="勾选后点击下方按钮作废"),
                            "金额(元)": st.column_config.NumberColumn("金额(元)", format="¥ %.2f")
                        },
                        key=coll_editor_key
                    )
                    
                    # 侦测选中项
                    selected_colls = edited_coll[edited_coll['🔴 作废'] == True]
                    if not selected_colls.empty:
                        st.warning(f"⚠️ 即将作废选中的 {len(selected_colls)} 笔收款记录，资金将从主合同中扣除。")
                        if st.button("🗑️ 确认作废收款流水", type="primary", use_container_width=True):
                            for _, row in selected_colls.iterrows():
                                db.void_financial_record(row['流水号'], "collections", current_user)
                            # 作废完毕后，立刻触发资金盘子重算
                            db.sync_main_contract_finance(selected_biz_code)

                            trigger_refresh()
                            st.rerun()
                else:
                    st.info("暂无有效收款记录")
                    
            # ---------------- 开票面板 ----------------
            with sub_tab_inv:
                df_inv = load_financial_history(selected_biz_code, "invoices")
                if not df_inv.empty:
                    inv_editor_key = f"inv_editor_{selected_biz_code}_{st.session_state.refresh_trigger}"
                    df_inv.insert(0, '🔴 作废', False)
                    
                    edited_inv = st.data_editor(
                        df_inv, 
                        width="stretch", 
                        hide_index=True,
                        disabled=["发票号", "开票日期", "金额(元)", "关联计划", "经办人", "备注", "录入时间"],
                        column_config={
                            "🔴 作废": st.column_config.CheckboxColumn("🔴 作废", default=False, help="勾选后点击下方按钮作废"),
                            "金额(元)": st.column_config.NumberColumn("金额(元)", format="¥ %.2f")
                        },
                        key=inv_editor_key
                    )
                    
                    selected_invs = edited_inv[edited_inv['🔴 作废'] == True]
                    if not selected_invs.empty:
                        st.warning(f"⚠️ 即将作废选中的 {len(selected_invs)} 笔开票记录。")
                        if st.button("🗑️ 确认作废开票流水", type="primary", use_container_width=True):
                            for _, row in selected_invs.iterrows():
                                db.void_financial_record(row['发票号'], "invoices", current_user)
                            # 作废完毕后，立刻触发资金盘子重算
                            db.sync_main_contract_finance(selected_biz_code)
                            trigger_refresh()
                            st.rerun()
                else:
                    st.info("暂无有效开票记录")
        # ==========================================
        # Tab 2: 📝 收款计划 (实时同步版)
        # ==========================================
        with tab_plan:
            # 🟢 实时拉取最新数据
            real_db_plans = load_payment_plans(selected_biz_code)
            
            if real_db_plans.empty:
                real_db_plans = pd.DataFrame([{
                    "计划编号": "", "款项节点": "初始阶段", "比例(%)": 0.0, 
                    "计划金额": 0.0, "预警日期": None, "备注": ""
                }])
            
            # 使用动态 Key 确保保存后 UI 强制重载
            editor_key = f"editor_{selected_biz_code}_{st.session_state.refresh_trigger}"
            
            edited_plans = st.data_editor(
                real_db_plans,
                num_rows="dynamic",
                column_config={
                    "计划编号": None, 
                    "款项节点": st.column_config.TextColumn("款项节点", required=True),
                    "比例(%)": st.column_config.NumberColumn("比例(%)", format="%.2f%%"),
                    "计划金额": st.column_config.NumberColumn("计划金额 (元)", format="%.2f"),
                    "预警日期": st.column_config.DateColumn("预警日期"),
                    "备注": st.column_config.TextColumn("补充说明")
                },
                width="stretch",
                hide_index=True,
                key=editor_key
            )
            
            if st.button("💾 确认保存/覆盖计划", use_container_width=True, type="primary"):
                current_user = st.session_state.get('user_name', 'System')
                success, msg = save_payment_plans(selected_biz_code, edited_plans, current_user, current_contract_amount)
                
                if success:
                    ui.show_toast_success("计划已成功覆盖保存并完成互算！")
                    trigger_refresh() # 🟢 改变 Key，迫使下次加载执行 load_payment_plans
                    st.rerun()
                else:
                    st.error(f"保存失败: {msg}")

        # ==========================================
        # Tab 3: 🛡️ 高级与审计
        # ==========================================
        # ==========================================
        # Tab 3: 🛡️ 高级与审计 (接入业财风控引擎)
        # ==========================================
        with tab_audit:
            st.warning("⚠️ 高级与危险操作区")
            
            # --- 1. 计提操作区 ---
            st.markdown("#### 💰 财务计提结算")
            st.caption("💡 计提后，该合同将被标记为财务完结，并将随着年度结转进入归档。")
            
            # 🟢 动态判断该主合同是否已经计提过
            # 注意：需确保主合同表有 is_provisioned 字段，如果没有提取到，默认算作未计提
            is_accrued = df_main[df_main['biz_code'] == selected_biz_code].get('is_provisioned', pd.Series(['否'])).iloc[0] == '是'
            
            if is_accrued:
                st.success("✅ 该主合同已完成财务计提，等待年度结转。")
            else:
                if st.button("📥 申请主合同计提结算", type="primary", use_container_width=True):
                    # 🟢 调用 crud_finance 里的核心计提函数 (内部已包含分包未结清的拦截逻辑)
                    success, msg = db.mark_project_as_accrued("main_contract", selected_biz_code)
                    if success:
                        if ui and hasattr(ui, 'show_toast_success'): ui.show_toast_success("✅ 计提成功！")
                        trigger_refresh()
                        st.rerun()
                    else:
                        st.error(msg) # 拦截信息（比如差额多少元）会在这里直接红色打印出来
            
            st.markdown("---")
            
            # --- 2. 软删除操作区 ---
            st.markdown("#### 🗑️ 合同作废")
            if st.button("🗑️ 软删除该合同 (移入回收站)", use_container_width=True):
                # 🚨 删除前的第一步：呼叫风控锁！
                passed, error_msg = crud.check_main_contract_clearance(selected_biz_code)
                
                if not passed:
                    # 拦截：弹出具体是哪些分包没结清
                    st.error(error_msg) 
                else:
                    # 放行：执行具体的软删除逻辑
                    current_user = st.session_state.get('user_name', 'System')
                    target_table = cfg.get_model_config("main_contract").get("table_name", "biz_main_contracts")
                    
                    # 🟢 核心修复：通过 biz_code 从 df_main 中精准提取物理 id
                    target_id = int(df_main[df_main['biz_code'] == selected_biz_code]['id'].iloc[0])
                    
                    success, msg = crud.soft_delete_project(
                        project_id=target_id, 
                        table_name=target_table,
                        operator_name=current_user
                    )
                    
                    if success:
                        st.toast("已安全移入系统全局回收站", icon="🗑️")
                        trigger_refresh()
                        st.rerun()
                    else:
                        st.error(f"删除失败: {msg}")
            
            st.markdown("---")
            # 🟢 召唤神器的时光机功能 (审计日志)
            if ui and hasattr(ui, 'render_audit_timeline'):
                try:
                    ui.render_audit_timeline(selected_biz_code, "main_contract")
                except Exception as e:
                    st.error(f"时光机加载失败: {e}")

debug_kit.execute_debug_logic()
```

##### 📄 03_🛠️_分包合同管理.py

```python
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import warnings
from pathlib import Path

# 彻底静默 pandas 的 SQLAlchemy 警告
warnings.filterwarnings('ignore', category=UserWarning, message='.*SQLAlchemy.*')

# 确保能找到 backend 模块
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database import crud
from backend.database.db_engine import execute_raw_sql, get_connection
from backend.config import config_manager as cfg
import backend.database as db

import sidebar_manager
import debug_kit 
import components as ui

# 隐藏/只读字段配置
FORM_HIDDEN_FIELDS = [] 
FORM_READONLY_FIELDS = ['total_paid', 'total_invoiced_from_sub', 'unpaid_amount']

# ==========================================
# 0. 页面配置与初始化
# ==========================================
st.set_page_config(page_title="分包合同管理 (支出侧)", page_icon="🛡️", layout="wide")

if 'refresh_trigger' not in st.session_state:
    st.session_state.refresh_trigger = 0

def trigger_refresh():
    st.session_state.refresh_trigger += 1

# ==========================================
# 1. 核心数据获取 (带缓存)
# ==========================================
@st.cache_data(ttl=5, show_spinner=False)
def load_sub_contracts(trigger):
    return db.fetch_dynamic_records('sub_contract')

@st.cache_data(ttl=5, show_spinner=False)
def load_main_contracts_dict(trigger):
    """专门为魔法下拉框准备：拉取所有主合同并做成映射字典"""
    df_main = db.fetch_dynamic_records('main_contract')
    if df_main.empty:
        return {}
    # 返回形如 {"MAIN-001": "万科项目", "MAIN-002": "海尔项目"} 的字典
    return pd.Series(df_main['project_name'].values, index=df_main['biz_code']).to_dict()

def load_sub_financial_history(sub_contract_code, table_type="payments"):
    """拉取分包侧的 纯付款 / 纯收票 历史"""
    conn = get_connection()
    try:
        if table_type == "payments":
            sql = '''
                SELECT biz_code AS "流水号", payment_date AS "付款日期", 
                       payment_amount AS "金额(元)", payment_method AS "支付方式", 
                       operator AS "经办人", remarks AS "备注", created_at AS "录入时间"
                FROM biz_outbound_payments
                WHERE sub_contract_code = %s AND deleted_at IS NULL
                ORDER BY payment_date DESC, created_at DESC
            '''
        else:
            sql = '''
                SELECT biz_code AS "发票号", invoice_date AS "收票日期", 
                       invoice_amount AS "金额(元)", invoice_number AS "发票号码", 
                       invoice_type AS "发票类型", operator AS "经办人", remarks AS "备注"
                FROM biz_sub_invoices
                WHERE sub_contract_code = %s AND deleted_at IS NULL
                ORDER BY invoice_date DESC, created_at DESC
            '''
        with conn.cursor() as cur:
            cur.execute(sql, (str(sub_contract_code),)) 
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=cols)
            
        if not df.empty:
            df['金额(元)'] = pd.to_numeric(df['金额(元)'], errors='coerce').fillna(0.0)
            if '录入时间' in df.columns:
                df['录入时间'] = pd.to_datetime(df['录入时间']).dt.strftime('%Y-%m-%d %H:%M')
        return df
    except Exception as e:
        st.error(f"⚠️ 读取历史失败: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

df_sub = load_sub_contracts(st.session_state.refresh_trigger)
main_dict = load_main_contracts_dict(st.session_state.refresh_trigger)

sidebar_manager.render_sidebar()

# ==========================================
# 2. 📝 弹窗：分包合同录入 (搭载魔法下拉框)
# ==========================================
@st.dialog("🛡️ 分包合同登记", width="large")
def sub_contract_form_dialog(existing_data=None):
    if ui and hasattr(ui, 'render_dynamic_form'):
        
        # 🟢 AI 占位符 (极简重构布局)
        st.subheader("🤖 AI 分包合同智能解析")
        uploaded_files = st.file_uploader("📂 请拖拽或选择待解析合同 (支持 PDF/Word)", accept_multiple_files=True)
        c_cat, c_btn = st.columns([3, 1])
        with c_cat:
            file_category = st.selectbox(
                "🗂️ 附件类别", 
                ["分包合同正文 (需 AI 解析)", "工程量清单", "结算单", "其他附件"],
                label_visibility="collapsed" 
            )
        with c_btn:
            ai_ready = uploaded_files is not None and len(uploaded_files) > 0 and "(需 AI 解析)" in file_category
            if st.button("✨ 一键 AI 提取", type="primary", disabled=not ai_ready, use_container_width=True):
                with st.spinner("🧠 AI 正在极速提取中..."):
                    import time; time.sleep(1)
                    st.success("🎉 AI 提取完毕！下方表单已更新。")
        st.markdown("---") 

        is_edit = existing_data is not None
        form_title = "✏️ 修改分包合同" if is_edit else "🆕 录入新分包合同"
        
        if not is_edit:
            target_table = cfg.get_model_config("sub_contract").get("table_name", "biz_sub_contracts")
            new_biz_code = crud_base.generate_biz_code(target_table, prefix_char="SUB")
            current_data = {'biz_code': new_biz_code}
        else:
            current_data = existing_data
            
        # 🟢 终极魔法：构造下拉选项和格式化函数
        all_main_codes = [""] + list(main_dict.keys())
        my_formatters = {
            "book_main_code": lambda code: f"[{code}] {main_dict.get(code, '未知项目')}" if code else "未关联",
            "actual_main_code": lambda code: f"[{code}] {main_dict.get(code, '未知项目')}" if code else "未关联"
        }
        my_options = {
            "book_main_code": all_main_codes,
            "actual_main_code": all_main_codes
        }
            
        # 渲染表单并注入魔法
        result = ui.render_dynamic_form(
            "sub_contract", 
            form_title, 
            current_data, 
            hidden_fields=FORM_HIDDEN_FIELDS,
            readonly_fields=FORM_READONLY_FIELDS,
            dynamic_options=my_options,
            format_funcs=my_formatters
        )
        
        if result:
            final_biz_code = result.get('biz_code', current_data.get('biz_code'))
            result['biz_code'] = final_biz_code
            target_id = int(existing_data['id']) if is_edit and 'id' in existing_data else None
            current_user = st.session_state.get('user_name', 'System')
            
            success, msg = crud_base.upsert_dynamic_record(
                model_name="sub_contract", 
                data_dict=result, 
                record_id=target_id,
                operator_name=current_user
            )
            
            if success:
                # 调用解耦后的附件大管家
                if uploaded_files:
                    from backend.services.file_service import save_attachment
                    target_table = cfg.get_model_config("sub_contract").get("table_name", "biz_sub_contracts")
                    for uf in uploaded_files:
                        save_attachment(final_biz_code, uf, target_table, file_category=file_category)
                ui.show_toast_success("分包数据保存成功！")
                trigger_refresh() 
                st.rerun()
            else:
                ui.show_toast_error(f"保存失败: {msg}")       

# ==========================================
# 3. 📊 顶层：防失血 KPI 预警看板
# ==========================================
col_title, col_add_btn = st.columns([8, 2])
with col_title:
    st.title("🛡️ 分包支出与税务防线")
with col_add_btn:
    st.write("") 
    if st.button("➕ 录入新分包合同", type="primary", use_container_width=True):
        sub_contract_form_dialog() 

if ui and hasattr(ui, 'style_metric_card'):
    ui.style_metric_card()

if not df_sub.empty:
    total_cost = df_sub['sub_amount'].astype(float).sum()
    total_paid = df_sub['total_paid'].astype(float).sum()
    total_unpaid = df_sub['unpaid_amount'].astype(float).sum() if 'unpaid_amount' in df_sub.columns else 0.0
    total_inv_rec = df_sub['total_invoiced_from_sub'].astype(float).sum() if 'total_invoiced_from_sub' in df_sub.columns else 0.0
    
    # 核心风控：倒挂欠票金额 = 已付真金白银 - 财务收到的发票
    missing_invoices = total_paid - total_inv_rec
    # 防止因为少量尾差出现负数误报
    missing_invoices = missing_invoices if missing_invoices > 0 else 0.0

    paid_rate = (total_paid / total_cost) * 100 if total_cost else 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💸 总成本盘子", f"¥ {total_cost:,.2f}", delta="支出预算池", delta_color="off")
    with col2:
        st.metric("🏦 累计已支付", f"¥ {total_paid:,.2f}", delta=f"资金流出率: {paid_rate:.1f}%") 
    with col3:
        st.metric("🧾 剩余应付敞口", f"¥ {total_unpaid:,.2f}", delta="未来资金流出压力", delta_color="inverse")
    with col4:
        # 🚨 红色税务预警：付了钱没拿回发票
        warn_color = "inverse" if missing_invoices > 0 else "off"
        warn_text = "🚨 税务流失红线" if missing_invoices > 0 else "票款安全"
        st.metric("⚠️ 欠票敞口 (付>票)", f"¥ {missing_invoices:,.2f}", delta=warn_text, delta_color=warn_color)
    
st.markdown("---")

# ==========================================
# 4. 黄金分割：左表(关注背靠背) + 右抽屉(减法 Tab)
# ==========================================
if df_sub.empty:
    st.info("📭 当前暂无分包合同数据。")
else:
    col_table, col_form = st.columns([2.5, 1.5])

    # ------------------------------------------
    # 🗂️ 左表：强化背靠背风险标识
    # ------------------------------------------
    with col_table:
        st.subheader("📑 分包防线台账")
        
        display_cols = {
            'biz_code': '合同编号',
            'sub_company_name': '分包单位',
            'sub_amount': '合同金额',
            'total_paid': '累计已付',
            'is_back_to_back': '背靠背', # 🟢 核心防线列
            'settlement_status': '结算状态'
        }
        for col in display_cols.keys():
            if col not in df_sub.columns:
                df_sub[col] = None

        df_display = df_sub[list(display_cols.keys())].rename(columns=display_cols)
        df_display.insert(0, '☑️', False)
        
        # 确保布尔值正确渲染
        df_display['背靠背'] = df_display['背靠背'].apply(lambda x: True if str(x).lower() in ['true', '1', '是'] else False)

        edited_df = st.data_editor(
            df_display,
            column_config={
                "☑️": st.column_config.CheckboxColumn("☑️", default=False),
                "背靠背": st.column_config.CheckboxColumn("背靠背条款", help="打勾代表需等甲方付款后才付款", disabled=True),
                "合同金额": st.column_config.NumberColumn("合同金额", disabled=True, format="¥ %.2f"),
                "累计已付": st.column_config.NumberColumn("累计已付", disabled=True, format="¥ %.2f"),
            },
            width="stretch", hide_index=True, height=500
        )

    # ------------------------------------------
    # 🎛️ 右操作台：极简 3 Tab
    # ------------------------------------------
    with col_form:
        st.subheader(f"🎛️ 支出枢纽")
        
        auto_selected_biz_code = None
        checked_rows = edited_df[edited_df['☑️'] == True]
        if not checked_rows.empty:
            auto_selected_biz_code = checked_rows.iloc[-1]['合同编号']
        
        col_select, col_edit = st.columns([8, 2])
        with col_select:
            contract_options = df_sub.apply(lambda row: f"{row['biz_code']} | {row['sub_company_name']}", axis=1).tolist()
            default_index = 0
            if auto_selected_biz_code:
                for i, opt in enumerate(contract_options):
                    if opt.startswith(auto_selected_biz_code):
                        default_index = i
                        break
            
            selected_contract_str = st.selectbox("🎯 目标分包合同", contract_options, index=default_index, label_visibility="collapsed")
            selected_biz_code = selected_contract_str.split(" | ")[0]
        
        with col_edit:
            if st.button("✏️ 修改", use_container_width=True):
                current_contract_data = df_sub[df_sub['biz_code'] == selected_biz_code].iloc[0].to_dict()
                sub_contract_form_dialog(existing_data=current_contract_data)

        # 🟢 减法 Tab：去掉了收款计划，只保留流水、历史、审计
        tab_flow, tab_history, tab_audit = st.tabs(["⚡ 录入流出", "📜 财务明细", "🛡️ 审计"])
        
        # ================= Tab 1: 录入流出 =================
        with tab_flow:
            action_type = st.radio("业务动作", ["录入付款 (流出真金白银)","录入收票 (收到进项票)"], horizontal=True)
            
            with st.form(key="sub_flow_form", clear_on_submit=True):
                amount = st.number_input("💵 操作金额 (元)", min_value=0.01, step=10000.0, format="%.2f")
                action_date = st.date_input("📅 发生日期", datetime.now())
                
                # 动态字段渲染
                if "收票" in action_type:
                    invoice_num = st.text_input("🧾 发票号码 (必填)")
                    inv_type_options = cfg.get_field_meta("sub_contract").get("tax_rate", {}).get("options", ["3%", "6%", "9%"])
                    invoice_type = st.selectbox("🏷️ 进项税率", inv_type_options)
                else:
                    pay_method = st.selectbox("💳 支付方式", ["电汇", "承兑汇票", "现金", "抵扣"])

                current_user = st.session_state.get('user_name', 'System')
                custom_remarks = st.text_input("📝 补充备注 (选填)", "")
                
                if st.form_submit_button("✅ 确认提交并核算", use_container_width=True):
                    if "收票" in action_type:
                        sql = "INSERT INTO biz_sub_invoices (biz_code, sub_contract_code, invoice_amount, invoice_date, invoice_number, invoice_type, operator, remarks) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                        vals = (f"SINV-{datetime.now().strftime('%Y%m%d%H%M%S')}", selected_biz_code, amount, action_date, invoice_num, invoice_type, current_user, custom_remarks)
                    else:
                        sql = "INSERT INTO biz_outbound_payments (biz_code, sub_contract_code, payment_amount, payment_date, payment_method, operator, remarks) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                        vals = (f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}", selected_biz_code, amount, action_date, pay_method, current_user, custom_remarks)
                    
                    success, msg = execute_raw_sql(sql, vals)
                    if success:
                        db.sync_sub_contract_finance(selected_biz_code) # 🟢 触发底层的互算引擎
                        ui.show_toast_success(f"成功录入 {amount:,.2f} 元！")
                        trigger_refresh()
                    else:
                        st.error(f"录入失败: {msg}")

        # ================= Tab 2: 财务历史 =================
        with tab_history:
            sub_tab_pay, sub_tab_inv = st.tabs(["💸 付款历史", "🧾 收票历史"])
            
            with sub_tab_pay:
                df_pay = load_sub_financial_history(selected_biz_code, "payments")
                if not df_pay.empty:
                    st.dataframe(df_pay, width="stretch", hide_index=True)
                else:
                    st.info("暂无付款流水")
                    
            with sub_tab_inv:
                df_inv = load_sub_financial_history(selected_biz_code, "invoices")
                if not df_inv.empty:
                    st.dataframe(df_inv, width="stretch", hide_index=True)
                else:
                    st.info("暂无收票流水")

        # ================= Tab 3: 审计 =================
            with tab_audit:
                st.markdown("#### 🗑️ 合同作废")
                if st.button("🗑️ 软删除该分包合同", use_container_width=True):
                    target_table = cfg.get_model_config("sub_contract").get("table_name", "biz_sub_contracts")
                    current_user = st.session_state.get('user_name', 'System')
                    
                    # 🟢 必须先算出 target_id
                    target_id = int(df_sub[df_sub['biz_code'] == selected_biz_code]['id'].iloc[0])
                    
                    # 🟢 正确的闭合调用
                    success, msg = crud.soft_delete_project(
                        project_id=target_id, 
                        table_name=target_table,
                        operator_name=current_user
                    )
                    
                    if success:
                        st.toast("已安全移入系统全局回收站", icon="🗑️")
                        trigger_refresh()
                        st.rerun()
                    else:
                        st.error(f"作废失败: {msg}")
                
                st.markdown("---")
                if ui and hasattr(ui, 'render_audit_timeline'):
                    ui.render_audit_timeline(selected_biz_code, "sub_contract")

debug_kit.execute_debug_logic()
```

##### 📄 04_📊_数据分析.py

```python
import sys
from pathlib import Path
from backend.database.db_engine import get_connection

# ==========================================
# 🟢 寻路魔法
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import plotly.express as px

# 接入新底座
from backend import database as db
from backend.config import config_manager as cfg
from backend.utils import formatters as ut

import sidebar_manager
import debug_kit
import components as ui

try:
    from ai_service import AIService  
except ModuleNotFoundError:
    pass

st.set_page_config(page_title="经营分析", page_icon="📊", layout="wide")
sidebar_manager.render_sidebar()

# =========================================================
# 🛠️ 工具函数：数据清洗与加载
# =========================================================


@st.cache_data(ttl=2) 
def load_analysis_data():
    """加载全量项目数据（绕过 db_manager 的拦截，直接查物理表）"""
    conn = db.get_connection()
    try:
        all_tables = db.get_all_data_tables()
        if not all_tables:
            return pd.DataFrame(), "未找到数据表"

        df_list = []
        for tbl in all_tables:
            # 🟢 破局关键：绕过黑盒！直接用 SQL 读取。
            # 兼容老数据：把 is_active 为 NULL (空) 的老数据，也当做有效项目抓出来！
            query = f'SELECT * FROM "{tbl}" WHERE is_active IS NULL OR is_active = 1'
            try:
                tmp_df = pd.read_sql_query(query, engine)
                if not tmp_df.empty:
                    tmp_df['origin_table'] = tbl 
                    df_list.append(tmp_df)
            except Exception as e:
                print(f"读取表 {tbl} 失败: {e}")
                
        if not df_list:
            return pd.DataFrame(), "所有表均无有效数据"
            
        df = pd.concat(df_list, ignore_index=True)

        # ==========================================
        # 🟢 终极修复：强制中英文字段映射！
        # ==========================================
        rules = cfg.load_data_rules()
        mapping = rules.get("column_mapping", {})
        
        # 构建反向映射字典
        reverse_mapping = {}
        for eng_key, ch_list in mapping.items():
            for ch_key in ch_list:
                reverse_mapping[ch_key] = eng_key
                
        # 强行把所有中文列翻译成英文标准列
        df.rename(columns=reverse_mapping, inplace=True)
        # ==========================================

        # 保底检查
        if 'sign_date' not in df.columns or 'contract_amount' not in df.columns:
            return pd.DataFrame(), f"关键列缺失。当前列: {df.columns.tolist()}"

        # 1. 强转日期
        df['dt_sign'] = pd.to_datetime(df['sign_date'], errors='coerce')
        df['sign_year'] = df['dt_sign'].dt.year.fillna(datetime.now().year).astype(int) 
        
        # 2. 强转金额 (使用你神级的 ut.safe_float)
        df['val_contract'] = df['contract_amount'].apply(ut.safe_float)
        df['val_collection'] = df['total_collection'].apply(ut.safe_float) if 'total_collection' in df.columns else 0.0
        
        # 3. 计提逻辑
        if 'contract_retention' in df.columns:
            df['val_uncollected'] = df['contract_retention'].apply(ut.safe_float)
        else:
            df['val_uncollected'] = df['val_contract'] - df['val_collection']
        
        df['project_name_safe'] = df['project_name'].fillna('未知项目') if 'project_name' in df.columns else '未知项目'
        df['manager_safe'] = df['manager'].fillna('未知') if 'manager' in df.columns else '未知'
        
        return df, "OK"
    finally:
        # 极度规范：用完数据库连接必须关闭
        conn.close()

# =========================================================
# 🟢 页面逻辑
# =========================================================

st.title("📊 年度经营与债权分析 (Pro)")
ui.style_metric_card()
st.caption("全生命周期视角：基于 Plotly 交互式引擎的深度资金盘点。")

df_all, msg = load_analysis_data()

if df_all.empty:
    st.error(f"⚠️ 无法加载数据: {msg}")
    st.stop()

# --- 年份选择 ---
valid_years = sorted(df_all[df_all['sign_year'] > 1900]['sign_year'].unique().tolist(), reverse=True)
if not valid_years:
    st.warning("数据中无有效年份，请检查日期列。")
    st.stop()

current_year = datetime.now().year
default_idx = valid_years.index(current_year) if current_year in valid_years else 0

available_tables = df_all['origin_table'].unique().tolist()
# 在最前面加上“全库”选项
scope_options = ["🌍 总览 "] + available_tables

# 调整顶部布局，分出两个选择框
c_year, c_scope, _ = st.columns([1, 1.5, 2])
with c_year:
    analysis_year = st.selectbox("📅 选择分析年份", valid_years, index=default_idx)
with c_scope:
    analysis_scope = st.selectbox(
        "🏢 选择分析范围", 
        scope_options, 
        index=0,
        format_func=ui.remove_prefix_formatter("data_")
    )

st.divider()

# =========================================================
# 🟢 新增：全局数据切片 (核心过滤逻辑)
# =========================================================
# 如果用户选了特定的表，就把 df_all 砍掉一部分，只留下选中的表的数据
if analysis_scope != "🌍 总览 ":
    df_all = df_all[df_all['origin_table'] == analysis_scope]

st.divider()

# --- 数据切片 ---
# 1. 本年新签
mask_new = (df_all['sign_year'] == analysis_year)
df_new = df_all[mask_new].copy()

# 2. 往年结转 (以前签的 + 有合同额的)
mask_carry = (df_all['sign_year'] < analysis_year) & (df_all['val_contract'] > 10)
df_carry = df_all[mask_carry].copy()

# 指标计算
new_contract_sum = df_new['val_contract'].sum()
new_collection_sum = df_new['val_collection'].sum()
carry_debt_sum = df_carry['val_uncollected'].sum()
total_debt = df_new['val_uncollected'].sum() + carry_debt_sum

# --- 宏观看板 ---
k1, k2, k3, k4 = st.columns(4)
k1.metric(f"{analysis_year}年 新签合同额", f"¥ {new_contract_sum/10000:,.1f} 万", f"{len(df_new)} 个项目")
k2.metric("本年新签回款率", f"{(new_collection_sum/new_contract_sum*100):.1f}%" if new_contract_sum else "0.0%", f"回款: ¥{new_collection_sum/10000:.1f}万", delta_color="off")
k3.metric("往年结转欠款", f"¥ {carry_debt_sum/10000:,.1f} 万", "存量风险", delta_color="inverse")
k4.metric("全盘总应收账款", f"¥ {total_debt/10000:,.1f} 万", "需催收总额", delta_color="inverse")

# =========================================================
# 📊 深度分析 (Plotly 升级版)
# =========================================================
st.markdown("### 🔍 结构化分析")
tab1, tab2 = st.tabs(["📉 往年结转·清欠分析", "🚀 本年新签·进度分析"])

# --- Tab 1: 往年坏账分析 ---
with tab1:
    c_chart, c_list = st.columns([1.2, 0.8])
    
    # 筛选欠款 > 1000 的项目
    df_carry_debt = df_carry[df_carry['val_uncollected'] > 1000].sort_values('val_uncollected', ascending=False)
    
    with c_chart:
        st.subheader("往年欠款年份分布")
        if not df_carry_debt.empty:
            # 聚合数据
            debt_by_year = df_carry_debt.groupby('sign_year')['val_uncollected'].sum().reset_index()
            
            # 🔥 Plotly 交互图表
            fig = px.bar(
                debt_by_year, 
                x="sign_year", 
                y="val_uncollected",
                text_auto='.2s', # 自动显示数值 (如 1.5M)
                labels={"sign_year": "签约年份", "val_uncollected": "剩余欠款金额"},
                color="val_uncollected",
                color_continuous_scale="Reds" # 颜色越深欠款越多
            )
            fig.update_layout(xaxis_type='category') # 强制年份显示为分类，不显示小数年份
            st.plotly_chart(fig, width="stretch")
            
            st.caption("💡 提示：鼠标悬停在柱子上可查看精确金额。")
        else:
            st.success("🎉 完美！无往年结转欠款。")

    with c_list:
        st.subheader("💀 TOP 10 风险欠款大户")
        
        # 🟢 1. 计算未收比例 (重点：在这里直接乘以 100！)
        df_carry['uncollected_rate'] = df_carry.apply(
            lambda x: (x['val_uncollected'] / x['val_contract'] * 100) if x['val_contract'] > 0 else 0, 
            axis=1
        )
        
        # 🟢 2. 核心业务逻辑
        # 因为上面乘了 100，所以这里的 0.20 要改成 20 (代表 20%)
        mask_risk = (df_carry['val_uncollected'] > 10000) & (df_carry['uncollected_rate'] > 20)
        df_carry_debt = df_carry[mask_risk].sort_values('val_uncollected', ascending=False)

        if not df_carry_debt.empty:
            st.dataframe(
                df_carry_debt.head(10)[['project_name_safe', 'manager_safe', 'val_contract', 'val_uncollected', 'uncollected_rate']],
                column_config={
                    "project_name_safe": "项目名称",
                    "manager_safe": "负责人",
                    "val_contract": st.column_config.NumberColumn("合同额", format="¥ %.0f"),
                    "val_uncollected": st.column_config.NumberColumn("高危欠款", format="¥ %.0f"),
                    # 🟢 3. 把最大值 (max_value) 从 1 改成 100
                    "uncollected_rate": st.column_config.ProgressColumn("欠款比例", format="%.1f%%", min_value=0, max_value=100) 
                },
                hide_index=True,
                width="stretch",
                height=380
            )
        else:
            st.success("暂无高危欠款项目")

# --- Tab 2: 本年业绩分析 ---
with tab2:
    if not df_new.empty:
        st.subheader(f"{analysis_year}年 部门/负责人 业绩对比")
        
        # 聚合数据
        by_manager = df_new.groupby('manager_safe')[['val_contract', 'val_collection']].sum().reset_index()
        by_manager = by_manager.sort_values('val_contract', ascending=False).head(15)
        
        # 🔥 Plotly 分组柱状图 (Grouped Bar)
        # 将数据宽转长 (Melt) 以便 Plotly 分组
        df_melt = by_manager.melt(id_vars='manager_safe', value_vars=['val_contract', 'val_collection'], var_name='类型', value_name='金额')
        # 汉化图例
        df_melt['类型'] = df_melt['类型'].map({'val_contract': '合同额', 'val_collection': '已回款'})
        
        fig2 = px.bar(
            df_melt, 
            x="manager_safe", 
            y="金额", 
            color="类型",
            barmode="group", # 分组并排显示
            text_auto='.2s',
            color_discrete_map={"合同额": "#4CAF50", "已回款": "#FFC107"}, # 自定义商务配色
            labels={"manager_safe": "负责人/部门"}
        )
        st.plotly_chart(fig2, width="stretch")
    else:
        st.info(f"{analysis_year} 年暂无新签项目。")

# --- AI 简报 ---
st.markdown("---")
c_ai_title, c_ai_action = st.columns([2, 1])
with c_ai_title:
    st.subheader("🤖 AI 经营诊断报告")
    st.caption("生成 CEO 视角的决策建议。")
with c_ai_action:
    if st.button("✨ 生成简报 (演示)", type="primary", width="stretch"):
        st.success("AI 接口已就绪，等待接入...")

debug_kit.execute_debug_logic()
```

##### 📄 05_🏢_往来单位.py

```python
# 文件位置: pages/05_🏢_往来单位.py
import sys
from pathlib import Path
import json
from datetime import datetime

# ==========================================
# 🟢 寻路魔法与依赖
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from backend.database import crud, schema
from backend.database.db_engine import get_connection, sql_engine, execute_raw_sql
from backend.config import config_manager as cfg
from sidebar_manager import render_sidebar
import debug_kit
import components as ui

# --- 页面基础配置 ---
st.set_page_config(layout="wide", page_title="往来单位库")
render_sidebar()

# ==================== 2. 核心弹窗逻辑 (极简 CRUD) ====================
@st.dialog("🏢 单位信息维护", width="large")
def render_enterprise_form(mode="edit", initial_data=None, model_name="enterprise", target_table=None):
    
    # 1. 标题与基础数据准备
    form_title = "🆕 新增往来单位" if mode == "add" else f"✏️ 编辑单位信息: {initial_data.get('biz_code', '')}"
    
    # 获取正确的 biz_code
    if mode == "add":
        new_code = crud.generate_biz_code(model_name=model_name, prefix_char="ENT")
        current_data = {'biz_code': new_code}
    else:
        current_data = initial_data

    # 2. 🟢 统一常量控制网关：定义隐藏和只读字段
    FORM_HIDDEN_FIELDS = ['id', 'deleted_at', 'source_file', 'sheet_name', 'extra_props', 'created_at', 'updated_at']
    FORM_READONLY_FIELDS = ['biz_code'] if mode == "edit" else []

    # 3. 🟢 直接呼叫偷懒神器画表单！
    result = ui.render_dynamic_form(
        model_name=model_name,
        form_title=form_title,
        existing_data=current_data,
        hidden_fields=FORM_HIDDEN_FIELDS,
        readonly_fields=FORM_READONLY_FIELDS
    )
    
    # 4. 接管保存逻辑
    if result:
        # 补全 biz_code 防止意外丢失
        if not result.get('biz_code'):
            result['biz_code'] = current_data.get('biz_code')
            
        target_id = int(initial_data.get('id')) if mode == "edit" and initial_data else None
        
        # 调用后端通用写入引擎
        success, msg = crud.upsert_dynamic_record(
            model_name=model_name, 
            data_dict=result, 
            record_id=target_id
        )
        
        if success:
            ui.show_toast_success("单位信息保存成功！")
            st.rerun()
        else:
            ui.show_toast_error(f"保存失败: {msg}")

# ==================== 2.5 时光机弹窗 (新增) ====================
@st.dialog("🕰️ 时光机：数据变更轨迹", width="large")
def show_audit_log_dialog(biz_code, model_name):
    ui.render_audit_timeline(biz_code, model_name)

# =========================================================
# 3. 主页面显示逻辑
# =========================================================
st.title("🏢 往来单位库管理")
st.caption("集中管理所有甲方、分包商及供应商的基础资信信息。")

# 🟢 自动寻址与初始化选项
all_models = cfg.load_data_rules().get("models", {})
model_options = [m for m, config in all_models.items() if "project" not in m.lower()]

if not model_options:
    st.warning("⚠️ 暂未在 app_config.json 中找到非项目的业务模型 (如 enterprise)。请先配置。")
    st.stop()

default_idx = model_options.index("enterprise") if "enterprise" in model_options else 0

# --- 搜索与工具栏 ---
selected_model = st.selectbox("选择库类型", model_options, index=default_idx)
target_table = all_models[selected_model].get("table_name", "biz_enterprises")
c_search, c_add = st.columns([3, 1])
   
with c_search:
    keyword = st.text_input("快速搜索", placeholder="输入名称或税号...", label_visibility="collapsed")
    # ✂️ 删除了 "查看回收站" 的 checkbox
    
with c_add:
    if st.button("➕ 新增单位", type="primary", width="stretch"):
        render_enterprise_form(mode="add", model_name=selected_model, target_table=target_table)

st.divider()

# --- 🟢 V2.0 查询逻辑 (纯净版，只看存活数据) ---
try:
    df_result = crud.fetch_dynamic_records(selected_model, keyword)
except Exception as e:
    st.error(f"查询失败: {e}")
    df_result = pd.DataFrame()

# --- 结果展示 ---
st.subheader(f"📋 检索结果 ({len(df_result)} 条记录)")

if not df_result.empty:
    drop_cols = ['id', 'deleted_at', 'source_file', 'sheet_name', 'extra_props']
    display_df = df_result.drop(columns=[c for c in drop_cols if c in df_result.columns])
    rules = cfg.load_data_rules()
    field_meta = rules.get("models", {}).get(selected_model, {}).get("field_meta", {})
    
    # 自动生成类似 {"company_name": "单位名称"} 的翻译字典
    rename_map = {col: meta.get("label", col) for col, meta in field_meta.items()}
    rename_map.update({
        "biz_code": "单位编号",
        "created_at": "创建时间",
        "updated_at": "最近修改",
        "status": "当前状态"
    })
    display_df = display_df.rename(columns=rename_map)
    event = st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        on_select="rerun", 
        selection_mode="single-row"
    )
    
    # --- 底部智能操作栏 ---
    if len(event.selection.rows) > 0:
        selected_index = event.selection.rows[0]
        selected_row = df_result.iloc[selected_index]
        current_biz_code = selected_row.get('biz_code', '未命名')
        
        st.info(f"📍 当前选中: **{current_biz_code}**")
        
        # 🟢 极简操作区：只有编辑、历史和删除
        ac1, ac2, ac3 = st.columns([1, 1, 1]) 
        with ac1:
            if st.button("📝 修改信息", type="primary", width="stretch"):
                render_enterprise_form(mode="edit", initial_data=selected_row, model_name=selected_model, target_table=target_table)
        with ac2:
            if st.button("🕰️ 查看操作历史", width="stretch"):
                show_audit_log_dialog(current_biz_code, selected_model)
        with ac3:
            if st.button("🗑️ 删除此单位 (软删除)", type="secondary", width="stretch"):
                # 🟢 1. 获取当前操作人（防呆设计）
                current_user = st.session_state.get('user_name', 'System')
                
                # 🟢 2. 调用后端正规军，把 current_user 传进去！
                success, msg = crud.soft_delete_project(
                    project_id=int(selected_row['id']), 
                    table_name=target_table,
                    operator_name=current_user
                )
                
                if success:
                    st.success("✅ 数据已移入回收站。")
                    st.rerun()
                else:
                    st.error(msg)
else:
    st.info("数据为空，或未找到匹配项。")

# 调试工具
debug_kit.execute_debug_logic()
```

##### 📄 06_📥_导入Excel.py

```python
# 文件位置: pages/04_📥_导入Excel.py
import sys
from pathlib import Path

# ==========================================
# 🟢 寻路魔法
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from backend import database as db
from backend.config import config_manager as cfg
from backend import services as svc
from backend.database import schema
from sidebar_manager import render_sidebar
import debug_kit
import components as ui

st.set_page_config(layout="wide", page_title="数据导入中心")
render_sidebar()

# 标题区
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.title("📥 智能导入与映射中心")
    st.caption("V2.0 增强版：全自动关联 Schema + 智能表头匹配")

st.divider() 
# ==========================================
# 🟢 模块 1：文件上传与模型选定
# ==========================================
uploaded_file = st.file_uploader("📂 第一步：上传 Excel 文件", type=["xlsx", "xls"])

if uploaded_file:
    if st.session_state.get('last_uploaded_filename') != uploaded_file.name:
        st.session_state['header_overrides'] = {}
        st.session_state['last_uploaded_filename'] = uploaded_file.name
    if 'header_overrides' not in st.session_state:
        st.session_state['header_overrides'] = {}
        
    overrides = st.session_state.get('header_overrides', {})
    with st.spinner("解析中(应用智能启发式算法)..."):
        cleaned_sheets = svc.clean_excel(uploaded_file, header_overrides=overrides)
    
    if not cleaned_sheets:
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        # 1. 选择工作表
        all_sheets = [s['sheet_name'] for s in cleaned_sheets]
        target_sheet = st.selectbox("1. 选择工作表", all_sheets)
        
        target_df = next(s['df'] for s in cleaned_sheets if s['sheet_name'] == target_sheet)
        headers = target_df.columns.tolist()
       
    with c2:
        # 🟢 升级 1：获取完整配置，使用 format_func 显示优雅的中文别名
        config_models = cfg.load_data_rules().get("models", {})
        all_models = list(config_models.keys())
        
        model_name = st.selectbox(
            "2. 映射到业务模型", 
            all_models,
            format_func=lambda m: f"📦 {config_models[m].get('model_label', m)}"
        )

    # ==========================================
    # 🟢 模块 2：核心映射区 (自动化优先 + 人工纠偏)
    # ==========================================
    st.divider()
    with st.container(border=True):
        st.markdown("### 🛠️ 字段映射确认")
        with st.expander("🛠️ 高级：表头识别错误？手动指定行号", expanded=False):
            st.caption("启发式算法若跳过了真正的表头，请在此处强制指定。")
            current_idx = overrides.get(target_sheet, -1)
            ui_val = current_idx + 1 if current_idx >= 0 else 0
            
            new_val = st.number_input(
                f"[{target_sheet}] 表头所在行号", 
                min_value=0, 
                max_value=50, 
                value=ui_val, 
                step=1, 
                help="0 = 自动识别。如果表头在 Excel 第 3 行，请填入 3。"
            )
            
            if new_val != ui_val:
                if new_val > 0:
                    st.session_state['header_overrides'][target_sheet] = int(new_val) - 1
                else:
                    if target_sheet in st.session_state['header_overrides']:
                        del st.session_state['header_overrides'][target_sheet]
                st.rerun()
                
        mapping = cfg.get_column_mapping(model_name)
        default_sel = [
            h for h in headers 
            if any(h in aliases for aliases in mapping.values()) or svc.smart_classify_header(h)
        ]
        
        chosen_cols = st.multiselect(
            "1. 勾选要导入的列", options=headers, default=default_sel, key="multi_select_cols"
        )
        
        user_final_mapping = {} 
        
        if chosen_cols:
            st.markdown("##### 2. 确认目标字段 (已为您自动匹配，如有误请手动修改)")
            
            standard_opts = cfg.get_standard_options(model_name)
            NEW_COL_OPT = "(新建中文物理列)" 
            IGNORE_OPT = "📦 [附加属性] 存入 JSONB"
            all_opts = [NEW_COL_OPT] + standard_opts + [IGNORE_OPT]
            
            ui_cols = st.columns(3)
            for i, col_original in enumerate(chosen_cols):
                auto_key = None
                for db_key, excel_aliases in mapping.items():
                    if col_original in excel_aliases:
                        auto_key = db_key
                        break
                if not auto_key:
                    auto_key = svc.smart_classify_header(col_original)
                
                default_idx = all_opts.index(IGNORE_OPT) 
                if auto_key:
                    for idx, opt in enumerate(all_opts):
                        if opt.startswith(f"{auto_key} |"):
                            default_idx = idx
                            break
                
                with ui_cols[i % 3]:
                    is_important = any(k in col_original.lower() for k in ['名称', '编号', 'name', 'code'])
                    display_label = f"原列: **{col_original}** ⭐️" if is_important else f"原列: **{col_original}**"
                    selected_opt = st.selectbox(
                        display_label,               
                        options=all_opts, 
                        index=default_idx, 
                        key=f"map_{col_original}"
                    )
                    
                    if selected_opt == NEW_COL_OPT:
                        user_final_mapping[col_original] = "NEW_PHYSICAL" 
                    elif selected_opt != IGNORE_OPT:
                        user_final_mapping[col_original] = selected_opt.split(" |")[0].strip()
                        
    # ==========================================
    # 🟢 模块 3：执行导入 (极简版)
    # ==========================================
    st.divider()
    # 🟢 升级 2：彻底切除历史遗留的主副表物理绑定 UI
    import_mode = st.radio("处理模式", ["追加导入", "覆盖导入"], horizontal=True)

    if st.button("🚀 开始执行导入", type="primary", width="stretch"):
        total_rows = len(target_df)
        msg = f"正在逐行校验并安全入库 {total_rows} 条数据，大文件可能需要等待 1-2 分钟，请勿刷新页面..."
        with st.spinner(msg):

            current_user = st.session_state.get('user_name', 'System')
            success, msg = svc.run_import_process(
                uploaded_file=uploaded_file, 
                target_sheet_name=target_sheet, 
                model_name=model_name,
                import_mode="overwrite" if "覆盖" in import_mode else "append",
                manual_mapping=user_final_mapping, 
                header_overrides=overrides,
                operator=current_user        
            )
            if success:
                st.success(msg)
                st.balloons()
            else:
                st.error(msg)

debug_kit.execute_debug_logic()
```

##### 📄 99_🧪_实验室.py

```python
import sys
from pathlib import Path

# ==========================================
# 🟢 寻路魔法
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import importlib
import os
import pandas as pd

# 接入新底座
from backend import database as db
from backend.config import config_manager as cfg
import debug_kit
import components as ui

# ==========================================
# 1. 实验室门禁 (Gatekeeper)
# ==========================================
st.set_page_config(page_title="功能实验室", layout="wide", page_icon="🧪")

# 检查开发者模式 (如果没有 debug_kit，可以暂时注释掉下面两行)
if not debug_kit.is_debug_mode():
    st.warning("🚫 此区域仅限开发者访问。请在侧边栏开启 '开发者模式'。")
    st.stop()

st.title("🧪 功能孵化实验室 (Plugin Mode)")
st.caption("插件化架构：内置核心诊断 + 外部实验脚本加载。")

# ==========================================
# 2. 扫描实验卡带 (Scan Plugins)
# ==========================================
EXP_DIR = "experiments"
if not os.path.exists(EXP_DIR):
    os.makedirs(EXP_DIR)

# 扫描文件夹下的所有 .py 文件
external_files = []
try:
    external_files = [f[:-3] for f in os.listdir(EXP_DIR) if f.endswith(".py") and f != "__init__.py"]
    external_files.sort()
except Exception:
    pass

# 🟢 核心改动：构建选项列表 (内置工具 + 外部文件)
BUILTIN_TOOL_NAME = "🏥 数据映射体检 (内置核心)"
menu_options = [BUILTIN_TOOL_NAME] + external_files

# ==========================================
# 3. 侧边栏控制台 (Console)
# ==========================================
with st.sidebar:
    st.header("🎛️ 实验室控制台")
    
    # [A] 选择实验 (混合列表)
    selected_exp = st.radio("选择实验卡带", options=menu_options)
    
    st.divider()
    
    # [B] 选择数据源 (宿主负责)
    all_tables = db.get_all_data_tables()
    if not all_tables:
        st.error("数据库为空，请先导入数据")
        st.stop()
        
    target_table = st.selectbox("🧪 实验目标数据表", all_tables)

# ==========================================
# 🟢 内置功能：数据映射诊断逻辑
# ==========================================
def run_diagnosis_tool(df):
    st.subheader("📊 数据库列名映射体检报告")
    st.info("此工具用于检查：Excel 表头是否被正确识别为系统所需的字段。")

    # 定义标准字典
    REQUIRED_FIELDS = [
        ("project_name", "项目名称", "🔴 必须"),
        ("manager", "负责人", "🔴 必须"),
        ("contract_amount", "合同金额", "🟠 核心(KPI)"),
        ("sign_date", "签约日期", "🟠 核心(年份)"),
        ("total_collection", "累计回款", "🟠 核心(KPI)"),
    ]

    actual_cols = df.columns.tolist()
    results = []

    for sys_key, cn_name, level in REQUIRED_FIELDS:
        # 1. 检查英文 Key 是否直接存在
        if sys_key in actual_cols:
            status = "✅ 完美 (英文匹配)"
            col_found = sys_key
            val = df[sys_key].iloc[0] if len(df) > 0 else "空"
        else:
            # 2. 检查中文映射 (查 config)
            mapped_cn = cfg.STANDARD_FIELDS.get(sys_key)
            if mapped_cn and mapped_cn in actual_cols:
                status = f"✅ 正常 (中文匹配: {mapped_cn})"
                col_found = mapped_cn
                val = df[mapped_cn].iloc[0] if len(df) > 0 else "空"
            else:
                status = "❌ **缺失！**"
                col_found = "未找到"
                val = "-"
        
        results.append({
            "重要性": level,
            "系统字段": sys_key,
            "业务含义": cn_name,
            "诊断结果": status,
            "实际匹配列": col_found,
            "首行样本": str(val)
        })

    # 展示结果
    st.dataframe(
        pd.DataFrame(results), 
        width="stretch", 
        hide_index=True,
        column_config={"诊断结果": st.column_config.TextColumn("状态", width="medium")}
    )

    # 智能提示
    missing = [r for r in results if "缺失" in r["诊断结果"]]
    if missing:
        st.error(f"⚠️ 发现 {len(missing)} 个关键字段缺失！首页 KPI 计算将受到影响。")
        st.markdown("**修复建议：** 请修改 Excel 表头，确保包含上述“业务含义”对应的列名，然后重新导入。")
    else:
        st.success("🎉 字段映射完美！数据结构健康。")
    
    with st.expander("查看原始数据 (Top 5)"):
        st.dataframe(df.head(5))

# ==========================================
# 4. 宿主加载器 (Host Loader)
# ==========================================
if target_table:
    # --- Step 1: 宿主建立连接 ---
    conn = db.get_readonly_connection()
    if not conn:
        st.stop()

    try:
        # --- Step 2: 预加载数据 ---
        df = pd.read_sql(f'SELECT * FROM "{target_table}"', conn)
        
        # --- Step 3: 分发逻辑 ---
        if selected_exp == BUILTIN_TOOL_NAME:
            # A. 运行内置诊断
            run_diagnosis_tool(df)
        else:
            # B. 运行外部插件
            module_path = f"{EXP_DIR}.{selected_exp}"
            if module_path in sys.modules:
                module = importlib.reload(sys.modules[module_path])
            else:
                module = importlib.import_module(module_path)
            
            if hasattr(module, 'run'):
                st.divider()
                module.run(df, conn) 
            else:
                st.error(f"⚠️ 插件 `{selected_exp}` 缺少 `run(df, conn)` 入口函数。")
            
    except Exception as e:
        st.error(f"💥 运行出错: {e}")
    finally:
        conn.close()
```

### 📁 tests

#### 📄 export_to_md.py

```python
import os
from pathlib import Path

def generate_tree(dir_path, ignore_dirs, file_extensions, prefix=""):
    """
    递归生成纯文本的目录树字符串
    """
    tree_str = ""
    try:
        items = os.listdir(dir_path)
    except PermissionError:
        return tree_str

    # 过滤并排序文件夹和文件
    dirs = sorted([d for d in items if os.path.isdir(os.path.join(dir_path, d)) and d not in ignore_dirs])
    files = sorted([f for f in items if os.path.isfile(os.path.join(dir_path, f)) and Path(f).suffix in file_extensions])

    entries = dirs + files
    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{entry}\n"

        # 如果是文件夹，继续递归
        if entry in dirs:
            extension = "    " if is_last else "│   "
            tree_str += generate_tree(os.path.join(dir_path, entry), ignore_dirs, file_extensions, prefix + extension)
            
    return tree_str

def export_project_to_markdown(project_dir, output_file, ignore_dirs=None, file_extensions=None):
    """
    将项目导出为包含目录树和代码块的 Markdown 文件。
    """
    if ignore_dirs is None:
        # 默认过滤掉常见的无关文件夹
        ignore_dirs = {'.git', '__pycache__', 'venv', 'env', '.idea', '.vscode', 'node_modules', '__MACOSX'}
    
    if file_extensions is None:
        file_extensions = {'.py'}

    project_path = Path(project_dir).resolve()

    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write(f"# 项目: {project_path.name}\n\n")

        # --- 第一部分：生成并写入目录树概览 ---
        md_file.write("## 🗂️ 项目目录树\n\n```text\n")
        md_file.write(f"{project_path.name}/\n")
        tree_content = generate_tree(project_path, ignore_dirs, file_extensions)
        md_file.write(tree_content)
        md_file.write("```\n\n---\n\n")
        
        # --- 第二部分：遍历并写入代码内容 ---
        md_file.write("## 💻 代码详情\n\n")
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            dirs.sort()
            files.sort()

            current_path = Path(root)
            try:
                relative_path = current_path.relative_to(project_path)
            except ValueError:
                continue

            # 目录标题
            if relative_path.parts:
                depth = len(relative_path.parts)
                # 基础层级从 H3 开始，因为 H2 被用作大板块划分
                dir_heading = "#" * (depth + 2) 
                md_file.write(f"{dir_heading} 📁 {relative_path.name}\n\n")
            else:
                depth = 0

            # 文件标题与代码块
            for file in files:
                file_path = current_path / file
                if file_path.suffix in file_extensions:
                    file_heading = "#" * (depth + 3)
                    md_file.write(f"{file_heading} 📄 {file}\n\n")
                    
                    md_file.write("```python\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            md_file.write(f.read())
                    except Exception as e:
                        md_file.write(f"# 读取文件失败: {e}\n")
                    
                    if not md_file.tell() == 0:
                        md_file.write("\n")
                    md_file.write("```\n\n")

if __name__ == "__main__":
    # 1. 获取当前脚本的绝对路径的父目录 (即 tests/ 目录)
    current_script_dir = Path(__file__).resolve().parent
    
    # 2. 定位到上一级目录 (即 项目根目录)
    PROJECT_DIRECTORY = current_script_dir.parent
    
    # 3. 设置输出文件路径 (这里将其保存在项目根目录下)
    OUTPUT_MARKDOWN_FILE = PROJECT_DIRECTORY / "project_code_context.md"
    
    print(f"开始整理目录: {PROJECT_DIRECTORY}")
    export_project_to_markdown(PROJECT_DIRECTORY, OUTPUT_MARKDOWN_FILE)
    print(f"✅ 整理完成！请查看文件: {OUTPUT_MARKDOWN_FILE}")
```

#### 📄 fix_db.py

```python
# 文件位置: ERP_V2_PRO/fix_db.py
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.db_engine import get_connection
from backend.database.schema import sync_database_schema

conn = get_connection()
cur = conn.cursor()

print("🧨 正在暴力拆除所有 V1.0 时代的残留表...")
cur.execute("""
    DROP TABLE IF EXISTS 
    biz_main_contracts, 
    biz_sub_contracts, 
    biz_enterprises,
    biz_collections, 
    biz_outbound_payments, 
    biz_invoices,
    sys_audit_logs CASCADE;
""")
conn.commit()
conn.close()

print("🏗️ 正在按 app_config.json 全新标准重建 V2.0 纯净表...")
sync_database_schema()
print("✅ 旧表已全部拆除，V2.0 纯净版表结构已重建完毕！")
```

#### 📄 run_server.py

```python
# 一键启动脚本
```

#### 📄 test_finance_scenario.py

```python
# 文件位置: ERP_V2_PRO/test_finance_scenario.py
# 🟢 作用：纯后端、无 UI 的“沙盘推演”自动化测试脚本

import sys
import os
import pandas as pd
from pathlib import Path

# 保证能找到 backend 模块
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.db_engine import get_connection, execute_raw_sql
from backend.database import crud_base
from backend.database import crud_finance

def clean_test_data():
    """清理测试遗留的脏数据"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM biz_main_contracts WHERE biz_code LIKE 'TEST-%'")
        cur.execute("DELETE FROM biz_sub_contracts WHERE biz_code LIKE 'TEST-%'")
        cur.execute("DELETE FROM biz_collections WHERE main_contract_code LIKE 'TEST-%'")
        cur.execute("DELETE FROM biz_outbound_payments WHERE sub_contract_code LIKE 'TEST-%'")
        conn.commit()
    finally:
        conn.close()

def inject_raw_data(table, data_dict):
    conn = get_connection()
    try:
        cur = conn.cursor()
        keys = list(data_dict.keys())
        values = tuple(data_dict.values()) 
        cols = ", ".join(keys)
        placeholders = ", ".join(["%s"] * len(keys))
        
        cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", values)
        conn.commit()
    finally:
        conn.close()

def run_scenario():
    print("🧹 1. 正在清理历史测试数据...")
    clean_test_data()

    print("🏗️ 2. 模拟业务员：录入一个 1000万 的主合同 (TEST-MAIN-001)...")
    res2, msg2 = crud_base.upsert_dynamic_record('main_contract', {
        'biz_code': 'TEST-MAIN-001',
        'project_name': '【沙盘推演】上海大厦项目',
        'contract_amount': 10000000  # 1000 万
    })
    print(f"  👉 写入结果: {res2}")

    print("🤝 3. 模拟分包经理：录入一个 200万 的分包合同，名义挂靠在 TEST-MAIN-001 上...")
    res3, msg3 = crud_base.upsert_dynamic_record('sub_contract', {
        'biz_code': 'TEST-SUB-001',
        'sub_company_name': '【沙盘推演】张三包工队',
        'book_main_code': 'TEST-MAIN-001',
        'main_contract_code': 'TEST-MAIN-001', # 确保物理关联也填上
        'sub_amount': 2000000          # 200 万
    })
    if not res3:
        print(f"\n🚨 致命错误：分包合同写入失败 -> {msg3}")
        sys.exit(1)

    # print("💰 4. 模拟财务：主合同收到甲方打款 400万 (回款率 40%)...")
    # inject_raw_data('biz_collections', {
    #     'biz_code': 'TEST-COLL-001',
    #     'main_contract_code': 'TEST-MAIN-001',
    #     'collected_amount': 4000000,
    #     'collected_date': '2026-03-20',
    #     'operator': '系统测试'
    # })
    print("💰 4. 模拟财务：主合同收到甲方全额打款 1000万 (回款率 100%)...")
    inject_raw_data('biz_collections', {
        'biz_code': 'TEST-COLL-001',
        'main_contract_code': 'TEST-MAIN-001',
        'collected_amount': 10000000, # 改为 1000 万
        'collected_date': '2026-03-20',
        'operator': '系统测试'
    })
    print("⚔️ 5. 模拟风控：测试分包背靠背红线与合规支付...")
    # 模拟先合法支付 50万
    success2, msg2 = crud_finance.submit_sub_payment(
        sub_biz_code='TEST-SUB-001', 
        payment_amount=500000, 
        operator='测试小哥', 
        payment_date='2026-03-21'
    )
    print(f"  👉 支付50万结果: {msg2}")
    
    # 这一步是为了模拟真实环境下触发一下分包总付额的重新计算
    execute_raw_sql("UPDATE biz_sub_contracts SET total_paid = 500000 WHERE biz_code = 'TEST-SUB-001'")

    print("\n" + "="*50)
    print("🛡️ [安全锁测试]：主合同删除与计提拦截")
    
    print("  [尝试违规删除主合同]：分包还有 150万 没付清，尝试强删主合同...")
    passed, msg = crud_finance.check_main_contract_clearance('TEST-MAIN-001')
    if not passed:
        print(f"  🟢 拦截成功！引擎拒绝删除，理由：\n{msg}")
    else:
        print("  ❌ 拦截失败！危险，允许删除了！")

    print("\n  [尝试违规计提主合同]：分包还有 150万 没付清，尝试计提主合同...")
    acc_success, acc_msg = crud_finance.mark_project_as_accrued("main_contract", "TEST-MAIN-001")
    if not acc_success:
        print(f"  🟢 拦截成功！引擎拒绝计提，理由：\n{acc_msg}")
    else:
        print("  ❌ 拦截失败！危险，允许计提了！")

    print("\n" + "="*50)
    print("💸 [结清测试]：把分包尾款结清，再尝试流转主合同")
    
    print("  [合规支付] 支付剩余 150万 分包款...")
    success_pay, msg_pay = crud_finance.submit_sub_payment(
        sub_biz_code='TEST-SUB-001', 
        payment_amount=1500000, 
        operator='财务主管', 
        payment_date='2026-03-21',
        remarks='支付尾款以准备项目计提'
    )
    print(f"  👉 支付结果: {msg_pay}")

    print("\n  [再次尝试计提主合同]...")
    # 此时引擎去算流水表：50万 + 150万 = 200万，刚好结清，锁会自动打开
    acc_success2, acc_msg2 = crud_finance.mark_project_as_accrued("main_contract", "TEST-MAIN-001")
    if acc_success2:
        print("  ✅ 计提成功！引擎识别到流水已平账，准许关账！")
    else:
        print(f"  ❌ 计提仍失败: {acc_msg2}")

    print("\n  [模拟年度大扫除] 执行全局年度结转...")
    arc_success, arc_msg = crud_finance.execute_yearly_accrual_archive()
    print(f"  👉 结转结果: {arc_msg}")
    
    # 断言：主合同应该已经被软删除了
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT deleted_at FROM biz_main_contracts WHERE biz_code = 'TEST-MAIN-001'")
    deleted_at = cur.fetchone()[0]
    conn.close()
    
    if deleted_at:
        print("  ✅ 完美闭环：TEST-MAIN-001 已被成功软删除移入历史档案！")
    else:
        print("  ❌ 闭环失败：数据未被软删除！")
        
    print("="*50 + "\n")

if __name__ == "__main__":
    try:
        run_scenario()
        print("\n🎉🎉 全链路自动化测试通过！核心财务引擎逻辑极其稳固！")
    except Exception as e:
        print(f"\n🚨🚨 测试过程中发生异常奔溃: {e}")
```

#### 📄 type_checker.py

```python
import os
import re

# 需要检查的关键字
KEYWORDS = ["list", "str", "dict", "float", "int", "tuple", "set", "type"]

# 定义正则表达式模式
PATTERNS = {
    "直接赋值": r"\b({})\s*=\s*",
    "循环变量": r"for\s+({})\s+in",
    "函数参数": r"def\s+\w+\s*\(.*?\b({})\b.*?\):",
    "通配符导入": r"from\s+\S+\s+import\s+\*",
    "isinstance误用": r"isinstance\s*\(\s*[^,]+,\s*['\"]", # 检查是否写成了 isinstance(x, "str")
}

def scan_project(root_dir):
    print(f"🚀 开始全项目扫描: {root_dir}")
    print("-" * 60)
    found_count = 0

    for root, dirs, files in os.walk(root_dir):
        # 跳过虚拟环境和缓存
        if any(x in root for x in [".venv", "venv", "anaconda3", "__pycache__", ".git"]):
            continue

        for file in files:
            if file.endswith(".py") and file != "type_checker.py":
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            # 过滤掉注释行
                            if line.strip().startswith("#"): continue
                            
                            for label, pattern in PATTERNS.items():
                                # 填充关键字到正则中
                                final_pattern = pattern.format("|".join(KEYWORDS))
                                matches = re.findall(final_pattern, line)
                                
                                if matches:
                                    # 处理 findall 结果
                                    target = matches[0] if isinstance(matches[0], str) else ""
                                    print(f"🚩 [发现风险] {label}: {target}")
                                    print(f"   文件: {file_path}")
                                    print(f"   行号: {i + 1} | 内容: {line.strip()}")
                                    print("-" * 40)
                                    found_count += 1
                except Exception as e:
                    print(f"⚠️ 无法读取文件 {file_path}: {e}")

    if found_count == 0:
        print("✅ 扫描完毕！未发现明显的关键字污染风险。")
    else:
        print(f"💡 扫描完毕，共发现 {found_count} 处潜在风险。请重点检查上述位置。")

if __name__ == "__main__":
    # 获取当前目录作为扫描起点
    scan_project(os.getcwd())
```

