from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseModel):
    data_path: Path = Field(default=ROOT_DIR / "data" / "support_tickets.csv")
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"
    llm_timeout_seconds: float = 120.0
    max_question_length: int = 500
    max_list_rows: int = 100

    @classmethod
    def from_env(cls) -> "Settings":
        path = Path(os.getenv("DATA_PATH", str(ROOT_DIR / "data" / "support_tickets.csv")))
        if not path.is_absolute():
            path = ROOT_DIR / path
        return cls(
            data_path=path,
            llm_provider=os.getenv("LLM_PROVIDER", "ollama").lower(),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2:latest"),
            llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "120")),
            max_question_length=int(os.getenv("MAX_QUESTION_LENGTH", "500")),
            max_list_rows=int(os.getenv("MAX_LIST_ROWS", "100")),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
