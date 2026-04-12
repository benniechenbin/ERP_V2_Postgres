import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    """
    项目全局配置中心。
    Pydantic Settings 会自动读取同级目录下的 .env 文件，
    并进行类型转换和强校验。
    """
    # ================= 1. AI 模型供应商配置 =================
    # 使用 Literal 强制限制只能在这三个选项中选择，拼错即报错
    AI_PROVIDER: Literal["openai", "local_gguf", "ollama"] = Field(
        default="openai", 
        description="AI API 供应商类型"
    )

    # ================= 2. OpenAI / DeepSeek 配置 =================
    # Optional[str] = None 表示如果 .env 里没配，它就是 None，系统不报错
    OPENAI_API_KEY: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    OPENAI_BASE_URL: str = Field(default="https://api.deepseek.com")
    OPENAI_MODEL: str = Field(default="deepseek-chat")

    # ================= 3. 本地 GGUF 配置 =================
    GGUF_MODEL_NAME: Optional[str] = Field(default=None)

    # ================= 4. Ollama 配置 =================
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434/v1")
    OLLAMA_MODEL: str = Field(default="qwen2:7b")

    # ================= 5. 数据库配置 (从 .env.example 补全) =================
    # Pydantic 会自动把字符串 "localhost" 转为 str，把 "5432" 转为 int
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5435) 
    DB_USER: str = Field(default="erp_admin")
    DB_PASS: str = Field(default="admin")
    DB_NAME: str = Field(default="erp_core_db")

    # Pydantic V2 标准配置
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),  
        env_file_encoding="utf-8",
        extra="ignore"
    )

# 在别的文件中直接 from backend.config.setting import settings 即可使用
settings = Settings()