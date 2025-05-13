from enum import Enum
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="allow")
    postgres_host: str = Field(..., alias="POSTGRES_HOST", description="PostgreSQL host")
    postgres_port: int = Field(..., alias="POSTGRES_PORT", description="PostgreSQL port")
    postgres_db: str = Field(..., alias="POSTGRES_DB", description="PostgreSQL database name")
    postgres_user: str = Field(..., alias="POSTGRES_USER", description="PostgreSQL username")
    postgres_password: SecretStr = Field(..., alias="POSTGRES_PASSWORD", description="PostgreSQL password")
    llm_api_model: str = Field(default="qwen2.5:7b", description="LLM API model")
    llm_api_token: SecretStr = Field(default="ollama", description="LLM API token")
    llm_api_url: str = Field(default="http://localhost:11434/v1", description="LLM API URI")
    log_level: LogLevel = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    prompt_path: str = Field(
        default=str(PROJECT_ROOT / "resume_parser/config/resume_parser_prompt.txt"), description="Path of txt prompt"
    )
    allowed_min_len_resume: int = Field(default=100, description="Minimal allowed length of resume text in symbols")


settings = Settings()
