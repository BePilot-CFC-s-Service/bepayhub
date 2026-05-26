"""
Repository - Camada responsável por comunicação com API Asaas e banco de dados
"""
from typing import Any, Dict, Optional
import requests
from config import Settings
from errors import ApiError


class AsaasRepository:
    """Repository para comunicação com API Asaas"""
    
    BASE_URL = Settings.ASAAS_API_URL
    API_KEY = Settings.ASAAS_API_KEY
    TIMEOUT = Settings.REQUEST_TIMEOUT_SECONDS
    
    @staticmethod
    def _get_headers() -> Dict[str, str]:
        """Retorna headers padrão para requisições Asaas"""
        return {
            "Content-Type": "application/json",
            "access_token": AsaasRepository.API_KEY,
        }
    
    @classmethod
    def create_customer(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria cliente na API Asaas
        
        Args:
            payload: Dados do cliente (name, cpf_cnpj, email, mobile_phone, etc)
            
        Returns:
            Resposta da API Asaas com dados do cliente criado
            
        Raises:
            ApiError: Se houver erro na requisição
        """
        try:
            url = f"{cls.BASE_URL}/customers"
            response = requests.post(
                url,
                headers=cls._get_headers(),
                json=payload,
                timeout=cls.TIMEOUT
            )
            
            if response.status_code >= 400:
                return response.json()
            
            return response.json()
        except requests.Timeout:
            raise ApiError("Timeout na integração com Asaas", status_code=504)
        except requests.RequestException as e:
            raise ApiError(f"Erro ao comunicar com Asaas: {str(e)}", status_code=500)
    
    @classmethod
    def list_customers(cls, **filters) -> Dict[str, Any]:
        """
        Lista clientes da API Asaas
        
        Args:
            **filters: Filtros opcionais (limit, offset, etc)
            
        Returns:
            Resposta da API Asaas com lista de clientes
            
        Raises:
            ApiError: Se houver erro na requisição
        """
        try:
            url = f"{cls.BASE_URL}/customers"
            response = requests.get(
                url,
                headers=cls._get_headers(),
                params=filters,
                timeout=cls.TIMEOUT
            )
            
            if response.status_code >= 400:
                return response.json()
            
            return response.json()
        except requests.Timeout:
            raise ApiError("Timeout na integração com Asaas", status_code=504)
        except requests.RequestException as e:
            raise ApiError(f"Erro ao comunicar com Asaas: {str(e)}", status_code=500)
    
    @classmethod
    def create_payment(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria pagamento na API Asaas
        
        Args:
            payload: Dados do pagamento (customer, value, dueDate, etc)
            
        Returns:
            Resposta da API Asaas com dados do pagamento criado
            
        Raises:
            ApiError: Se houver erro na requisição
        """
        try:
            url = f"{cls.BASE_URL}/payments"
            response = requests.post(
                url,
                headers=cls._get_headers(),
                json=payload,
                timeout=cls.TIMEOUT
            )
            
            if response.status_code >= 400:
                return response.json()
            
            return response.json()
        except requests.Timeout:
            raise ApiError("Timeout na integração com Asaas", status_code=504)
        except requests.RequestException as e:
            raise ApiError(f"Erro ao comunicar com Asaas: {str(e)}", status_code=500)
    
    @classmethod
    def create_subscription(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria assinatura/recorrência na API Asaas
        
        Args:
            payload: Dados da assinatura (customer, value, nextDueDate, etc)
            
        Returns:
            Resposta da API Asaas com dados da assinatura criada
            
        Raises:
            ApiError: Se houver erro na requisição
        """
        try:
            url = f"{cls.BASE_URL}/subscriptions"
            response = requests.post(
                url,
                headers=cls._get_headers(),
                json=payload,
                timeout=cls.TIMEOUT
            )
            
            if response.status_code >= 400:
                return response.json()
            
            return response.json()
        except requests.Timeout:
            raise ApiError("Timeout na integração com Asaas", status_code=504)
        except requests.RequestException as e:
            raise ApiError(f"Erro ao comunicar com Asaas: {str(e)}", status_code=500)
    
    @classmethod
    def list_payments(cls, **filters) -> Dict[str, Any]:
        """
        Lista pagamentos da API Asaas
        
        Args:
            **filters: Filtros opcionais (limit, offset, customer, status, etc)
            
        Returns:
            Resposta da API Asaas com lista de pagamentos
            
        Raises:
            ApiError: Se houver erro na requisição
        """
        try:
            url = f"{cls.BASE_URL}/payments"
            response = requests.get(
                url,
                headers=cls._get_headers(),
                params=filters,
                timeout=cls.TIMEOUT
            )
            
            if response.status_code >= 400:
                return response.json()
            
            return response.json()
        except requests.Timeout:
            raise ApiError("Timeout na integração com Asaas", status_code=504)
        except requests.RequestException as e:
            raise ApiError(f"Erro ao comunicar com Asaas: {str(e)}", status_code=500)
