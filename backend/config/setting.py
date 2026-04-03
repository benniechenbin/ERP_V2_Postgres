from typing import Optional, Literal
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    全局配置中心
    所有的变量名必须与 .env 文件中的保持绝对一致
    """
    AI_PROVIDER: Literal["openai", "local_gguf", "ollama"] = "openai"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    OPENAI_MODEL: str = "deepseek-chat"


    GGUF_MODEL_NAME: Optional[str] = None


    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen2:7b"

    class Config:
       
        env_file = ".env"
       
        env_file_encoding = "utf-8"
       
        extra = "ignore" 

settings = Settings()