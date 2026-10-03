"""
Global runtime configuration for Re:Learn backend.
Reads from environment variables with sensible defaults for local dev.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # project root


class Settings:
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'backend' / 'data' / 'relearn.db'}"

    # Server
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Sandbox
    SANDBOX_TIMEOUT: float = 2.0          # seconds
    BLOCKED_IMPORTS: list = ["os", "sys", "subprocess", "socket", "shutil",
                             "importlib", "ctypes", "multiprocessing"]

    # ML artifacts
    MODEL_PATH: str = str(BASE_DIR / "ml" / "artifacts" / "model.joblib")
    METRICS_PATH: str = str(BASE_DIR / "ml" / "artifacts" / "metrics.json")

    # CORS (allow all for demo)
    CORS_ORIGINS: list = ["*"]


settings = Settings()
