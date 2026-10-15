"""
VibeFinance configuration
"""
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FILINGS_DIR = DATA_DIR / "filings"
USERS_DIR = DATA_DIR / "users"
MARKET_DIR = DATA_DIR / "market"
METRICS_DIR = DATA_DIR / "metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    # LLM
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_base_url: Optional[str] = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    use_mock_llm: bool = os.getenv("USE_MOCK_LLM", "true").lower() == "true"

    # RAG
    embedding_model: str = "all-MiniLM-L6-v2"
    top_k_docs: int = 3
    similarity_threshold: float = 0.35

    # Agents
    agent_timeout_sec: float = 30.0
    parallel_agents: bool = True

    # Demo
    demo_mode: bool = True
    default_symbols: list[str] = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

settings = Settings()