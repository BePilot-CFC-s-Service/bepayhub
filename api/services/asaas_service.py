from typing import Any, Dict, Optional, Tuple

import requests

from config import Settings, validate_settings
from errors import ServiceIntegrationError


class AsaasService:
    def __init__(self, base_url: str, api_key: str, timeout: float):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {
            "access_token": self.api_key,
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        json_payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], int]:
        try:
            response = requests.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=self._headers(),
                json=json_payload,
                params=params,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise ServiceIntegrationError(
                "Tempo limite excedido na integracao com Asaas",
                status_code=504,
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ServiceIntegrationError(
                "Falha de comunicacao com Asaas",
                status_code=502,
            ) from exc

        try:
            body = response.json()
        except ValueError:
            body = {
                "error": "Resposta invalida do Asaas",
                "raw": response.text,
            }

        return body, response.status_code

    def create_payment(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        return self._request("POST", "/payments", json_payload=payload)

    def create_subscription(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        return self._request("POST", "/subscriptions", json_payload=payload)

    def get_payment_billing_info(self, payment_id: str) -> Tuple[Dict[str, Any], int]:
        return self._request("GET", f"/payments/{payment_id}/billingInfo")

    def list_payments(
        self,
        external_reference: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], int]:
        params = extra_params.copy() if extra_params else {}
        if external_reference:
            params["externalReference"] = external_reference
        return self._request("GET", "/payments", params=params)

    def create_customer(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        return self._request("POST", "/customers", json_payload=payload)


_asaas_service: Optional[AsaasService] = None


def get_asaas_service() -> AsaasService:
    global _asaas_service
    if _asaas_service is None:
        validate_settings()
        _asaas_service = AsaasService(
            base_url=Settings.ASAAS_API_URL,
            api_key=Settings.ASAAS_API_KEY,
            timeout=Settings.REQUEST_TIMEOUT_SECONDS,
        )
    return _asaas_service
