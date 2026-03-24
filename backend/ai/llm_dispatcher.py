import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# ==========================================
# 🟢 终极路径锚点系统 (防呆设计)
# ==========================================
# 1. 找到当前文件 (llm_dispatcher.py) 所在的绝对目录
CURRENT_DIR = Path(__file__).resolve().parent

# 2. 向上找 2 层，精准定位到项目根目录 ERP_V2_Postgres/
ROOT_DIR = CURRENT_DIR.parent.parent

# 3. 显式加载根目录下的 .env 文件 (无论你在哪里运行启动命令，它都能找到！)
env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path)

class LLMDispatcher:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openai") # 'openai', 'ollama', 或 'local_gguf'
        self.client = None
        self.model = None
        
        if self.provider == "openai":
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL")
            )
            self.model = os.getenv("OPENAI_MODEL", "deepseek-chat")
            
        elif self.provider == "ollama":
            self.client = OpenAI(
                api_key="ollama", 
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            )
            self.model = os.getenv("OLLAMA_MODEL", "qwen2:7b")
            
        elif self.provider == "local_gguf":
            try:
                from llama_cpp import Llama
                
                # 🟢 自动寻址：定位到 backend/models/ 目录
                model_filename = os.getenv("GGUF_MODEL_NAME", "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf")
                model_path = ROOT_DIR / "backend" / "models" / model_filename
                
                print(f"⏳ 正在启动内置 AI 引擎，加载模型: {model_path}...")
                self.client = Llama(
                    model_path=str(model_path), # 必须转为字符串给 C++ 引擎
                    n_ctx=8192,        
                    n_threads=8,       
                    verbose=False      
                )
                print("✅ 内置 AI 引擎加载完毕！")
            except ImportError:
                print("❌ 缺少本地 AI 引擎依赖！请执行: pip install llama-cpp-python")
            except Exception as e:
                print(f"❌ 本地模型加载失败，请检查文件是否存在: {e}")

    def chat(self, messages, response_format=None):
        try:
            if self.provider in ["openai", "ollama"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format=response_format
                )
                return response.choices[0].message.content
                
            elif self.provider == "local_gguf":
                if not self.client:
                    return '{"error": "本地 AI 引擎未正确初始化"}'
                
                response = self.client.create_chat_completion(
                    messages=messages,
                    response_format=response_format,
                    temperature=0.1
                )
                return response['choices'][0]['message']['content']
                
        except Exception as e:
            return f"AI 调度异常: {str(e)}"

# 单例模式供全局调用
ai_dispatcher = LLMDispatcher()