from pathlib import Path
from openai import OpenAI
from backend.config.settings import settings

# ==========================================
# 🟢 终极路径锚点系统 (防呆设计)
# ==========================================
# 1. 找到当前文件 (llm_dispatcher.py) 所在的绝对目录
CURRENT_DIR = Path(__file__).resolve().parent

# 2. 向上找 2 层，精准定位到项目根目录 ERP_V2_Postgres/
ROOT_DIR = CURRENT_DIR.parent.parent


class LLMDispatcher:
    def __init__(self):
        self.provider = settings.AI_PROVIDER 
        self.client = None
        self.model = None
        
        if self.provider == "openai":
            self.client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            self.model = settings.OPENAI_MODEL
            
        elif self.provider == "ollama":
            self.client = OpenAI(
                api_key="ollama", 
                base_url=settings.OLLAMA_BASE_URL
            )
            self.model = settings.OLLAMA_MODEL
            
        elif self.provider == "local_gguf":
            try:
                from llama_cpp import Llama
                
                # 🟢 自动寻址：定位到 backend/models/ 目录
                model_filename = settings.GGUF_MODEL_NAME
                
                # 防御性编程：检查 GGUF 名字是否配置了
                if not model_filename:
                    raise ValueError("使用本地模型，但 .env 中未配置 GGUF_MODEL_NAME")
                    
                model_path = ROOT_DIR / "backend" / "models" / model_filename
                
                print(f"⏳ 正在启动内置 AI 引擎，加载模型: {model_path}...")
                self.client = Llama(
                    model_path=str(model_path),
                    n_ctx=8192,
                    n_gpu_layers=-1,  # 👈 核心修改：-1 表示把所有层都交给 GPU 
                    n_threads=8,
                    verbose=False
                )
                print("✅ 内置 AI 引擎加载完毕！")
            except ImportError:
                print("❌ 缺少本地 AI 引擎依赖！请执行: pip install llama-cpp-python") [cite: 1]
            except Exception as e:
                print(f"❌ 本地模型加载失败，请检查文件是否存在: {e}") [cite: 1]

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
