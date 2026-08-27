import requests
import logging
from typing import Any, Dict, List, Optional
from config import Settings
from errors import IntegrationError

logger = logging.getLogger(__name__)

class SupabaseRepository:
    """
    Acesso ao Supabase via API REST (PostgREST).
    Utiliza requests em vez da biblioteca supabase-py.
    """

    @staticmethod
    def _get_headers(use_service_role: bool = False, prefer_return: bool = False) -> Dict[str, str]:
        """
        Retorna headers para as requisições.
        - use_service_role=True: usa a service_role key (escrita)
        - prefer_return=True: adiciona Prefer: return=representation (para INSERT/UPDATE)
        """
        key = Settings.SUPABASE_SERVICE_ROLE_KEY if use_service_role else Settings.SUPABASE_KEY
        if not key:
            raise IntegrationError("Chave do Supabase não configurada", 500)
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if prefer_return:
            headers["Prefer"] = "return=representation"
        return headers

    @staticmethod
    def _build_url(table: str, query: Optional[Dict[str, Any]] = None) -> str:
        """Constrói a URL com filtros no formato PostgREST."""
        base_url = f"{Settings.SUPABASE_URL}/rest/v1/{table}"
        if not query:
            return base_url

        params = []
        for key, value in query.items():
            if isinstance(value, dict) and "neq" in value:
                params.append(f"{key}=neq.{value['neq']}")
            else:
                params.append(f"{key}=eq.{value}")

        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url

    @classmethod
    def _request(
        cls,
        method: str,
        table: str,
        data: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        use_service_role: bool = False,
        prefer_return: bool = False,
    ) -> Any:
        """Executa uma requisição genérica ao Supabase."""
        url = cls._build_url(table, query)
        headers = cls._get_headers(use_service_role, prefer_return)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=10,
            )

            if response.status_code >= 400:
                error_detail = response.text or "Sem detalhes"
                raise IntegrationError(
                    f"Erro Supabase ({response.status_code}): {error_detail}",
                    status_code=response.status_code,
                )

            # Se o conteúdo está vazio, retorna None
            if not response.content or response.content.strip() == b"":
                return None

            try:
                return response.json()
            except ValueError:
                logger.error(f"Supabase response non-JSON (status {response.status_code}): {response.text[:200]}")
                raise IntegrationError(
                    f"Resposta inesperada do Supabase (status {response.status_code})",
                    status_code=response.status_code,
                )

        except requests.Timeout:
            raise IntegrationError("Timeout na integração com Supabase", status_code=504)
        except requests.RequestException as e:
            raise IntegrationError(f"Falha na comunicação com Supabase: {str(e)}", status_code=500)

    @classmethod
    def fetch_one(cls, table: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca um único registro."""
        result = cls._request("GET", table, query=query, use_service_role=False)
        if isinstance(result, list) and result:
            return result[0]
        if isinstance(result, dict):
            return result
        return None

    @classmethod
    def fetch_all(cls, table: str, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Busca todos os registros que atendem aos filtros."""
        result = cls._request("GET", table, query=query, use_service_role=False)
        if isinstance(result, list):
            return result
        return []

    @classmethod
    def insert(cls, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insere um novo registro e retorna o registro inserido.
        Utiliza Prefer: return=representation para obter o recurso criado.
        """
        result = cls._request(
            "POST",
            table,
            data=data,
            use_service_role=True,
            prefer_return=True,
        )
        if isinstance(result, list) and result:
            return result[0]
        if isinstance(result, dict):
            return result
        return None

    @classmethod
    def update(cls, table: str, query: Dict[str, Any], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Atualiza registros que correspondem ao filtro e retorna o registro atualizado.
        Utiliza Prefer: return=representation.
        """
        result = cls._request(
            "PATCH",
            table,
            data=data,
            query=query,
            use_service_role=True,
            prefer_return=True,
        )
        if isinstance(result, list) and result:
            return result[0]
        if isinstance(result, dict):
            return result
        return None

    @classmethod
    def delete(cls, table: str, query: Dict[str, Any]) -> bool:
        """Remove registros que correspondem ao filtro."""
        result = cls._request("DELETE", table, query=query, use_service_role=True)
        return result is None  # 204 retorna None