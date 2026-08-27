
import os
from dotenv import load_dotenv

load_dotenv()

def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

class Settings:
    DEBUG = _to_bool(os.getenv("FLASK_DEBUG"), default=False)
    TESTING = _to_bool(os.getenv("FLASK_TESTING"), default=False)
    PORT = int(os.getenv("PORT", "10000"))
    API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
    ENV = os.getenv("ENV", "development")

    # Asaas
    ASAAS_API_URL = (os.getenv("ASAAS_API_URL") or "").rstrip("/")
    ASAAS_API_KEY = os.getenv("ASAAS_API_KEY") or ""
    ASAAS_REQUEST_TIMEOUT = float(os.getenv("ASAAS_REQUEST_TIMEOUT", "10"))

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL") or ""
    SUPABASE_KEY = os.getenv("SUPABASE_KEY") or ""
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""

    @classmethod
    def validate(cls) -> None:
        missing = []
        if not cls.ASAAS_API_URL:
            missing.append("ASAAS_API_URL")
        if not cls.ASAAS_API_KEY:
            missing.append("ASAAS_API_KEY")
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if missing:
            raise RuntimeError(f"Variáveis de ambiente obrigatórias ausentes: {', '.join(missing)}")
