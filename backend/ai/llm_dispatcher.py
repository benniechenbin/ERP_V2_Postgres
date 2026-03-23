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