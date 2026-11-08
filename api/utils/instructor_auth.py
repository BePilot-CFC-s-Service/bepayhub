from functools import wraps
from uuid import UUID

import requests
from flask import request

from config import Settings
from errors import ApiError, IntegrationError


def require_instructor_owner(handler):
    """Verify the access token with Supabase Auth before accessing financial data."""
    @wraps(handler)
    def wrapped(instructor_id, *args, **kwargs):
        authorization = request.headers.get("Authorization", "").split()
        if len(authorization) != 2 or authorization[0].lower() != "bearer":
            raise ApiError("Token de acesso necessário", 401)
        if not Settings.SUPABASE_URL or not Settings.SUPABASE_KEY:
            raise IntegrationError("Supabase Auth não configurado", 500)

        try:
            response = requests.get(
                f"{Settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
                headers={
                    "apikey": Settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {authorization[1]}",
                },
                timeout=10,
            )
        except requests.Timeout:
            raise IntegrationError("Timeout na autenticação Supabase", 504)
        except requests.RequestException:
            raise IntegrationError("Falha na autenticação Supabase", 502)

        if response.status_code in (400, 401, 403):
            raise ApiError("Token de acesso inválido", 401)
        if response.status_code != 200:
            raise IntegrationError("Falha na autenticação Supabase", 502)
        try:
            user_id = UUID(response.json()["id"])
        except (ValueError, KeyError, TypeError, AttributeError):
            raise IntegrationError("Resposta inválida do Supabase Auth", 502)
        if user_id != instructor_id:
            raise ApiError("Acesso negado", 403)
        return handler(str(instructor_id), *args, **kwargs)

    return wrapped
