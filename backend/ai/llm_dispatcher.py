from openai import OpenAI

from backend.config.settings import MODELS_DIR, settings
from backend.observability.logger import sys_logger


class LLMDispatcher:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.client = None
        self.model = None

        if self.provider == "openai":
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
            self.model = settings.OPENAI_MODEL

        elif self.provider == "ollama":
            self.client = OpenAI(api_key="ollama", base_url=settings.OLLAMA_BASE_URL)
            self.model = settings.OLLAMA_MODEL

        elif self.provider == "local_gguf":
            try:
                from llama_cpp import Llama

                # 🟢 自动寻址：定位到 backend/models/ 目录
                model_filename = settings.GGUF_MODEL_NAME

                # 防御性编程：检查 GGUF 名字是否配置了
                if not model_filename:
                    raise ValueError("使用本地模型，但 .env 中未配置 GGUF_MODEL_NAME")

                model_path = MODELS_DIR / model_filename

                sys_logger.info(f"⏳ 正在启动内置 AI 引擎，加载模型: {model_path}...")
                self.client = Llama(
                    model_path=str(model_path),
                    n_ctx=8192,
                    n_gpu_layers=-1,  # 👈 核心修改：-1 表示把所有层都交给 GPU
                    n_threads=8,
                    verbose=False,
                )
                sys_logger.info("✅ 内置 AI 引擎加载完毕！")
            except ImportError:
                sys_logger.exception("❌ 缺少本地 AI 引擎依赖！请执行: pip install llama-cpp-python")
            except Exception as e:  # noqa: BLE001 - local model loading is an SDK isolation boundary.
                sys_logger.exception(f"❌ 本地模型加载失败，请检查文件是否存在: {e}")

    def chat(self, messages, response_format=None):
        try:
            if self.provider in ["openai", "ollama"]:
                response = self.client.chat.completions.create(
                    model=self.model, messages=messages, response_format=response_format
                )
                return response.choices[0].message.content

            elif self.provider == "local_gguf":
                if not self.client:
                    return '{"error": "本地 AI 引擎未正确初始化"}'

                response = self.client.create_chat_completion(
                    messages=messages, response_format=response_format, temperature=0.1
                )
                return response["choices"][0]["message"]["content"]

        except Exception as e:  # noqa: BLE001 - provider SDK failures are normalized to the public string contract.
            sys_logger.exception(f"AI 调度异常: {e}")
            return f"AI 调度异常: {e!s}"
