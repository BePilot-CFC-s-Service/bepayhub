import os
from dotenv import load_dotenv

load_dotenv()


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    REQUEST_TIMEOUT_SECONDS = float(os.getenv("ASAAS_REQUEST_TIMEOUT", "10"))
    DEBUG = _to_bool(os.getenv("FLASK_DEBUG"), default=False)
    TESTING = _to_bool(os.getenv("FLASK_TESTING"), default=False)
    PORT = int(os.getenv("PORT", "10000"))
    API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
    ASAAS_API_URL = (os.getenv("ASAAS_API_URL") or "").rstrip("/")
    ASAAS_API_KEY = os.getenv("ASAAS_API_KEY") or ""


def validate_settings() -> None:
    missing = []
    if not Settings.ASAAS_API_URL:
        missing.append("ASAAS_API_URL")
    if not Settings.ASAAS_API_KEY:
        missing.append("ASAAS_API_KEY")

    if missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(f"Variaveis de ambiente obrigatorias ausentes: {missing_str}")
