from enum import Enum
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
CV_DIR = DATA_DIR / "resumes_pdf"
LATEX_DIR = DATA_DIR / "resumes_latex"
JSON_DIR = DATA_DIR / "resumes_json"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="allow")

    latex_template_path: str = Field(
        default=CONFIG_DIR / "cv_template.tex", description="Path of latex template for cv"
    )
    llm_api_model: str = Field(default="qwen2.5:7b", description="LLM API model")
    llm_api_token: SecretStr = Field(default="ollama", description="LLM API token")
    llm_api_url: str = Field(default="http://localhost:11434/v1", description="LLM API URI")
    log_level: LogLevel = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    max_retries: int = Field(default=3, description="Max retries of generating single cv")
    prompt_path: str = Field(
        default=PROJECT_ROOT / "cv_generator/config/cv_generator_prompt.txt", description="Path of txt with prompt"
    )
    retry_delay: int = Field(default=15, description="Retry delay of generating single cv")
    workers_num: int = Field(default=20, description="Number of workers")


settings = Settings()

DATA_DIR.mkdir(parents=True, exist_ok=True)
CV_DIR.mkdir(parents=True, exist_ok=True)
LATEX_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)
