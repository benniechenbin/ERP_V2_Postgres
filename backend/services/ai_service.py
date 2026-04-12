import json
import PyPDF2
from docx import Document

from backend.utils.logger import sys_logger
from backend.config import config_manager as cfg

def extract_text_from_upload(uploaded_file):
    """从上传的文件流中提取文本"""
    text = ""
    name = uploaded_file.name.lower()
    try:
        if name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages[:8]: 
                text += page.extract_text() + "\n"
        elif name.endswith('.docx'):
            doc = Document(uploaded_file) #
            for para in doc.paragraphs[:150]: 
                text += para.text + "\n"
        return text[:8000] 
    except Exception as e:
        sys_logger.error(f"AI 文本提取失败: {e}")
        return ""

def extract_contract_elements(uploaded_file, model_name: str, dispatcher):
    """
    [V2 通用终极版] 动态全字段 AI 提取接口
    根据传入的 model_name (如 main_contract, sub_contract) 自动生成 Schema 提取！
    """
    raw_text = extract_text_from_upload(uploaded_file)
    if not raw_text: return {}

    # 🟢 1. 动态加载配置
    model_config = cfg.get_model_config(model_name)
    field_meta = model_config.get("field_meta", {})
    formulas = model_config.get("formulas", {})
    json_schema = {} 

    for k, v in field_meta.items():
        # 🟢 漏斗 2 & 3：虚拟/只读/公式列自动拦截 + JSON 个性化忽略标记拦截
        if v.get('is_virtual') or v.get('readonly') or k in formulas or v.get('ai_ignore'):
            continue
            
        # 智能推导 AI 的默认值提示
        f_type = v.get('type', 'text')
        # 注意适配配置里的 "num", "money", "percent"
        if f_type in ['money', 'number', 'num', 'percent']: 
            json_schema[k] = 0.0
        elif f_type == 'date':
            json_schema[k] = "YYYY-MM-DD(如果没有则填null)"
        elif f_type == 'select' and 'options' in v:
            json_schema[k] = f"从以下选项中选一: {', '.join(v['options'])}"
        else:
            json_schema[k] = f"提取的{v.get('label', k)}"

    model_label = model_config.get("model_label", "合同")
    
    # 🟢 2. 组装终极通用 Prompt
    messages = [
        {
            "role": "system", 
            "content": f"你是一个专业的建筑工程法务与造价分析专家。请从用户提供的{model_label}文本中提取关键信息。\n"
                       f"必须严格按照以下 JSON 格式返回，不要包含任何解释。金额必须为纯数字(不要带逗号或元)。\n"
                       f"需要提取的 JSON 骨架如下：\n{json.dumps(json_schema, ensure_ascii=False, indent=2)}"
        },
        {"role": "user", "content": f"文本内容：\n{raw_text}"}
    ]

    response_text = dispatcher.chat(messages, response_format={"type": "json_object"})
    
    try:
        return json.loads(response_text)
    except Exception as e:
        sys_logger.error(f"AI 解析全字段 JSON 失败: {e}")
        return {}