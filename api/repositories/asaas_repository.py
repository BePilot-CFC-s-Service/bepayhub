import requests
from config import Settings
from errors import IntegrationError

class AsaasRepository:
    BASE_URL = Settings.ASAAS_API_URL
    API_KEY = Settings.ASAAS_API_KEY
    TIMEOUT = Settings.ASAAS_REQUEST_TIMEOUT

    @staticmethod
    def _headers() -> dict:
        return {
            "Content-Type": "application/json",
            "access_token": AsaasRepository.API_KEY,
        }

    @classmethod
    def _request(cls, method: str, endpoint: str, data: dict = None, params: dict = None):
        url = f"{cls.BASE_URL}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=cls._headers(),
                json=data,
                params=params,
                timeout=cls.TIMEOUT,
            )
            if response.status_code >= 400:
                error_data = response.json()
                raise IntegrationError(
                    message=f"Erro Asaas: {error_data.get('message', 'Erro desconhecido')}",
                    status_code=response.status_code,
                    details=error_data.get("errors"),
                )
            return response.json()
        except requests.Timeout:
            raise IntegrationError("Timeout na integração com Asaas", status_code=504)
        except requests.RequestException as e:
            raise IntegrationError(f"Falha na comunicação com Asaas: {str(e)}", status_code=500)

    @classmethod
    def create_customer(cls, payload: dict) -> dict:
        return cls._request("POST", "/customers", data=payload)

    @classmethod
    def get_customer(cls, customer_id: str) -> dict:
        return cls._request("GET", f"/customers/{customer_id}")

    @classmethod
    def create_payment(cls, payload: dict) -> dict:
        return cls._request("POST", "/payments", data=payload)

    @classmethod
    def get_payment(cls, payment_id: str) -> dict:
        return cls._request("GET", f"/payments/{payment_id}")

    @classmethod
    def create_transfer(cls, payload: dict) -> dict:
        return cls._request("POST", "/transfers", data=payload)

    @classmethod
    def get_balance(cls) -> dict:
        return cls._request("GET", "/balance")