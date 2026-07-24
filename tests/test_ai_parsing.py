# 文件位置: tests/test_ai_parsing.py
import json
import os

import pandas as pd
import pytest
from docx import Document  # 🟢 新增：用于读取 docx
from dotenv import load_dotenv
from openai import OpenAI


def extract_text_from_docx(file_path):
    """从 docx 文件中提取所有文本内容"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到文件: {file_path}")

    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)


def load_extraction_schema():
    """从主配置中提取需要 AI 填充的字段"""
    with open("app_config.json", encoding="utf-8") as f:
        config = json.load(f)

    fields = config["models"]["main_contract"]["field_meta"]
    target_fields = {
        k: v["label"] for k, v in fields.items() if not v.get("is_virtual") and k not in ["remarks", "project_stage"]
    }
    return target_fields


def ai_extract_contract(contract_text):
    """调用 DeepSeek 进行结构化提取"""
    schema = load_extraction_schema()

    # 延迟加载与实例化，防止 pytest 收集测试时因为缺少环境变量崩溃
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY / OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key, base_url=base_url or "https://api.deepseek.com")

    system_prompt = f"""
    你是一个专业的建筑工程合同分析专家。请从用户提供的合同文本中提取关键信息。
    必须严格按照以下 JSON 格式返回结果，不要包含任何解释或 Markdown 标签。

    需要提取的字段映射如下（Key 为返回键，Value 为描述）：
    {json.dumps(schema, ensure_ascii=False, indent=2)}

    注意：
    1. 金额必须为纯数字（FLOAT）。
    2. 日期格式统一为 YYYY-MM-DD。
    3. 如果文中未提及，请返回 null。
    """

    # 🟢 增加对超长文本的截断保护（虽然 DeepSeek 上下文很大，但保护一下更好）
    if len(contract_text) > 40000:
        print("⚠️ 警告：合同内容过长，已截取前 40,000 个字符进行解析。")
        contract_text = contract_text[:40000]

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"合同文本如下：\n\n{contract_text}"},
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


@pytest.mark.skip(reason="需要消耗真实的 API Token 且强依赖本地 test.docx，仅供本地手动调试")
def test_ai_document_extraction():
    target_file = "test.docx"  # 🟢 读取同目录下的 test.docx

    print(f"📄 正在读取本地文件: {target_file}...")
    # 1. 提取文本
    contract_content = extract_text_from_docx(target_file)
    print(f"✅ 文本提取成功，共 {len(contract_content)} 个字符。")

    # 2. AI 解析
    print("🤖 正在调用 DeepSeek 进行 AI 结构化解析...")
    extracted_data = ai_extract_contract(contract_content)

    # 3. 构造报告
    schema = load_extraction_schema()
    test_results = []
    for key, label in schema.items():
        test_results.append(
            {
                "字段标签": label,
                "内部 Key": key,
                "AI 提取结果": extracted_data.get(key, "未匹配"),
            }
        )

    df_res = pd.DataFrame(test_results)

    print("\n" + "=" * 50)
    print(f"📊 AI 解析报告 (源文件: {target_file})")
    print("=" * 50)
    print(df_res.to_markdown(index=False))
    print("=" * 50)

    assert extracted_data is not None
    assert "contract_amount" in extracted_data


if __name__ == "__main__":
    try:
        test_ai_document_extraction()
    except FileNotFoundError:
        print("❌ 错误：请在当前目录下放置一个名为 'test.docx' 的文档。")
    except Exception as e:  # noqa: BLE001 - manual script entry point reports provider and parser failures.
        print(f"🚨 运行出错: {e}")
