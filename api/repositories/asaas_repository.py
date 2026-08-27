import requests
import logging
from config import Settings
from errors import IntegrationError
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AsaasRepository:
    BASE_URL = Settings.ASAAS_API_URL
    API_KEY = Settings.ASAAS_API_KEY
    TIMEOUT = Settings.ASAAS_REQUEST_TIMEOUT
    USER_AGENT = "BePayHub/1.0.0"

    @staticmethod
    def _headers(api_key: Optional[str] = None) -> Dict[str, str]:
        """Headers com access_token customizável (para subcontas)."""
        token = api_key or AsaasRepository.API_KEY
        return {
            "Content-Type": "application/json",
            "accept": "application/json",
            "access_token": token,
            "User-Agent": AsaasRepository.USER_AGENT,
        }

    @classmethod
    def _request(
        cls,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Requisição genérica com suporte a api_key da subconta."""
        url = f"{cls.BASE_URL}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=cls._headers(api_key),
                json=data,
                params=params,
                timeout=cls.TIMEOUT,
            )

            if response.status_code == 204:
                return {}

            try:
                response_data = response.json()
            except ValueError:
                logger.error(f"Asaas response non-JSON (status {response.status_code}): {response.text[:200]}")
                raise IntegrationError(
                    f"Resposta inesperada do Asaas (status {response.status_code})",
                    status_code=response.status_code,
                )

            if response.status_code >= 400:
                # Extrai mensagem e descrição dos erros
                message = response_data.get("message") or "Erro desconhecido"
                errors = response_data.get("errors") or []
                details = None
                if errors:
                    details = [
                        {
                            "code": err.get("code"),
                            "description": err.get("description"),
                        }
                        for err in errors
                    ]
                raise IntegrationError(
                    message=f"Erro Asaas: {message}",
                    status_code=response.status_code,
                    details=details,
                )

            return response_data

        except requests.Timeout:
            raise IntegrationError("Timeout na integração com Asaas", status_code=504)
        except requests.RequestException as e:
            raise IntegrationError(f"Falha na comunicação com Asaas: {str(e)}", status_code=500)

    @classmethod
    def create_customer(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        return cls._request("POST", "/customers", data=payload)

    @classmethod
    def get_customer(cls, customer_id: str) -> Dict[str, Any]:
        return cls._request("GET", f"/customers/{customer_id}")

    @classmethod
    def create_payment(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        return cls._request("POST", "/payments", data=payload)

    @classmethod
    def get_payment(cls, payment_id: str) -> Dict[str, Any]:
        return cls._request("GET", f"/payments/{payment_id}")

    @classmethod
    def get_pix_qr_code(cls, payment_id: str) -> Dict[str, Any]:
        return cls._request("GET", f"/payments/{payment_id}/pixQrCode")

    @classmethod
    def create_subaccount(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        return cls._request("POST", "/accounts", data=payload)

    @classmethod
    def get_subaccount(cls, wallet_id: str) -> Dict[str, Any]:
        """Consulta uma subconta (wallet) pelo ID."""
        return cls._request("GET", f"/accounts/{wallet_id}")

    @classmethod
    def create_transfer(
        cls,
        payload: Dict[str, Any],
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        return cls._request("POST", "/transfers", data=payload, api_key=api_key)

    @classmethod
    def get_balance(cls, api_key: Optional[str] = None) -> Dict[str, Any]:
        return cls._request("GET", "/balance", api_key=api_key)

    @classmethod
    def get_finance_balance(cls, api_key: Optional[str] = None) -> Dict[str, Any]:
        return cls._request("GET", "/finance/balance", api_key=api_key)