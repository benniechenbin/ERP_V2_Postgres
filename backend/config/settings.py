from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = PROJECT_ROOT  # 兼容旧代码中的命名
ENV_PATH = PROJECT_ROOT / ".env"
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
BACKUP_DIR = DATA_DIR / "backups"
LOG_DIR = PROJECT_ROOT / "logs"
MODELS_DIR = PROJECT_ROOT / "backend" / "models"
HOST_DATA_DIR = PROJECT_ROOT / "host_data"
EXPERIMENTS_DIR = HOST_DATA_DIR / "experiments"
APP_CONFIG_FILE = PROJECT_ROOT / "app_config.json"


def resolve_project_path(path_value: str | Path) -> Path:
    """将项目相对路径解析为绝对路径，绝对路径保持不变。"""
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


class Settings(BaseSettings):
    """
    项目全局配置中心。
    Pydantic Settings 会自动读取同级目录下的 .env 文件，
    并进行类型转换和强校验。
    """

    # ================= 1. AI 模型供应商配置 =================
    # 使用 Literal 强制限制只能在这三个选项中选择，拼错即报错
    AI_PROVIDER: Literal["openai", "local_gguf", "ollama"] = Field(default="openai", description="AI API 供应商类型")

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
    DB_TYPE: Literal["postgresql", "sqlite"] = Field(default="postgresql", description="数据库类型")
    SQLITE_DB_PATH: str = Field(default="data/erp_sqlite.db", description="SQLite 数据库文件路径")
    # Pydantic 会自动把字符串 "localhost" 转为 str，把 "5432" 转为 int
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5435)
    DB_USER: str = Field(default="erp_admin")
    DB_PASS: str = Field(default="admin")
    DB_NAME: str = Field(default="erp_core_db")

    @property
    def sqlite_db_file(self) -> Path:
        """当前 SQLite 数据库文件的绝对路径。"""
        return resolve_project_path(self.SQLITE_DB_PATH)

    # Pydantic V2 标准配置
    model_config = SettingsConfigDict(env_file=str(ENV_PATH), env_file_encoding="utf-8", extra="ignore")


# 在别的文件中直接 from backend.config.settings import settings 即可使用
settings = Settings()
