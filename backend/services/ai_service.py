# 文件位置: backend/services/ai_service.py
import json
import PyPDF2

from docx import Document
from backend.ai.llm_dispatcher import LLMDispatcher #
from backend.utils.logger import sys_logger
from backend.config import config_manager as cfg

# 实例化调度器
dispatcher = LLMDispatcher()

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

def get_main_contract_elements(uploaded_file):
    """
    [V2 终极版] 动态全字段 AI 提取接口
    直接根据 app_config.json 的配置，让 AI 提取所有可提取的字段！
    """
    raw_text = extract_text_from_upload(uploaded_file)
    if not raw_text: return {}

    # 🟢 1. 恢复你测试脚本中的动态读取逻辑！
    field_meta = cfg.get_field_meta("main_contract")
    json_schema = {}
    
    # 排除一些不需要/不应该由 AI 填写的系统字段
    exclude_keys = [
        # 1. 系统底层与流转状态
        'biz_code', 'remarks', 'project_stage', 'is_provisioned', 'provision_time', 'contract_status', 'archive_date', 'project_code',
        
        # 2. 预测与计划类 (刚签合同不需要这些)
        'est_sign_date', 'est_contract_amount', 'est_invoice_this_year', 'plan_invoice_date',
        
        # 3. 🟢 财务动态执行指标 (本次报错的元凶！纸质合同里绝对没有这些)
        'recognized_revenue',          # 确认收入
        'operating_revenue',           # 营业收入
        'total_ar',                    # 应收账款
        'ar_invoiced_uncollected',     # 应收账款(已开未到)
        'uncollected_contract_amount', # 未到账合同额
        'unbilled_contract_amount',    # 剩余未开票合同额
        'collection_progress'          # 合同收费完成进度 (就是它报的错！)
    ]

    for k, v in field_meta.items():
        if not v.get('is_virtual') and k not in exclude_keys:
            # 智能推导 AI 的默认值提示
            f_type = v.get('type', 'text')
            if f_type in ['money', 'number', 'percent']:
                json_schema[k] = 0.0
            elif f_type == 'date':
                json_schema[k] = "YYYY-MM-DD(如果没有则填null)"
            else:
                json_schema[k] = f"提取的{v.get('label', k)}"

    # 🟢 2. 组装终极 Prompt
    messages = [
        {
            "role": "system", 
            "content": f"你是一个专业的建筑工程法务与造价分析专家。请从用户提供的合同文本中提取关键信息。\n"
                       f"必须严格按照以下 JSON 格式返回，不要包含任何解释。金额必须为纯数字。\n"
                       f"需要提取的 JSON 骨架如下：\n{json.dumps(json_schema, ensure_ascii=False, indent=2)}"
        },
        {"role": "user", "content": f"合同内容：\n{raw_text}"}
    ]

    # 🟢 3. 呼叫大模型
    response_text = dispatcher.chat(messages, response_format={"type": "json_object"})
    try:
        return json.loads(response_text)
    except Exception as e:
        sys_logger.error(f"AI 解析全字段 JSON 失败: {e}")
        return {}