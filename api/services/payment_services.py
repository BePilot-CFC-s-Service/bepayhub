"""
Services - Camada de lógica de negócio
"""
from typing import Any, Dict, Tuple

from .validators import (
    validate_customer_payload,
    validate_payment_payload,
    validate_origin,
)
from .payload import (
    get_billing_type,
    build_payment_payload,
    build_subscription_payload,
    build_customer_payload,
    build_external_reference,
)
from errors import ApiError
from repositories.asaas_repository import AsaasRepository


class CustomerService:
    """Serviço de gerenciamento de clientes"""
    
    def __init__(self, repository: AsaasRepository = None):
        self.repository = repository or AsaasRepository()
    
    def create_customer(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Cria um novo cliente
        
        Args:
            data: Dados do cliente (name, cpf_cnpj, email, mobile_phone, external_reference, etc)
            
        Returns:
            Tupla (resposta_dict, status_code)
        """
        # Valida dados
        validate_customer_payload(data)
        
        # Prepara payload para Asaas
        payload = {
            "name": data["name"],
            "cpfCnpj": data["cpf_cnpj"],
            "email": data["email"],
            "phone": data["mobile_phone"],
        }
        
        # Adiciona campos opcionais
        if data.get("address"):
            payload["address"] = data["address"]
        if data.get("address_number"):
            payload["addressNumber"] = data["address_number"]
        if data.get("city"):
            payload["city"] = data["city"]
        if data.get("state"):
            payload["state"] = data["state"]
        if data.get("postal_code"):
            payload["postalCode"] = data["postal_code"]
        
        # Chama repository para criar cliente
        response = self.repository.create_customer(payload)
        
        # Verifica se há erro na resposta
        if "errors" in response:
            return response, 400
        
        return response, 201
    
    def list_customers(self, **filters) -> Tuple[Dict[str, Any], int]:
        """
        Lista clientes
        
        Args:
            **filters: Filtros opcionais (limit, offset, etc)
            
        Returns:
            Tupla (resposta_dict, status_code)
        """
        response = self.repository.list_customers(**filters)
        
        # Verifica se há erro na resposta
        if "errors" in response:
            return response, 400
        
        return response, 200


class PaymentService:
    """Serviço de gerenciamento de pagamentos"""
    
    def __init__(self, repository: AsaasRepository = None):
        self.repository = repository or AsaasRepository()
    
    def create_student_payment(
        self, 
        method: str, 
        data: Dict[str, Any], 
        remote_ip: str = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Cria pagamento para estudante (aula particular)
        
        Args:
            method: Método de pagamento (pix, debit, credit)
            data: Dados do pagamento (customer_id, value, due_date, etc)
            remote_ip: IP remoto do cliente
            
        Returns:
            Tupla (resposta_dict, status_code)
        """
        # Valida dados
        billing_type = get_billing_type(method)
        validate_payment_payload(data, billing_type)
        
        # Prepara payload
        payload = build_payment_payload(
            data,
            billing_type,
            description="Aula particular de direção",
            external_reference="studentPayment",
            remote_ip=remote_ip,
        )
        
        # Chama repository para criar pagamento
        response = self.repository.create_payment(payload)
        
        # Verifica se há erro na resposta
        if "errors" in response:
            return response, 400
        
        return response, 201
    
    def create_instructor_subscription(
        self,
        data: Dict[str, Any],
        remote_ip: str = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Cria assinatura/mensalidade para instrutor
        
        Args:
            data: Dados da assinatura (customer_id, value, due_date, creditCard, etc)
            remote_ip: IP remoto do cliente
            
        Returns:
            Tupla (resposta_dict, status_code)
        """
        # Valida dados (credit card é obrigatório)
        validate_payment_payload(data, "CREDIT_CARD")
        
        # Prepara payload
        payload = build_subscription_payload(
            data,
            billing_type="CREDIT_CARD",
            description="Mensalidade instrutor",
            external_reference="instructorPayment",
            cycle="MONTHLY",
            remote_ip=remote_ip,
        )
        
        # Chama repository para criar assinatura
        response = self.repository.create_subscription(payload)
        
        # Verifica se há erro na resposta
        if "errors" in response:
            return response, 400
        
        return response, 201
    
    def list_payments(self, origin: str, **filters) -> Tuple[Dict[str, Any], int]:
        """
        Lista pagamentos por origem (student ou instructor)
        
        Args:
            origin: Origem (student ou instructor)
            **filters: Filtros opcionais (limit, offset, customer, status, etc)
            
        Returns:
            Tupla (resposta_dict, status_code)
        """
        # Valida origem
        validate_origin(origin)
        
        # Adiciona filtro de external_reference
        external_ref = get_external_reference_by_origin(origin)
        filters["externalReference"] = external_ref
        
        response = self.repository.list_payments(**filters)
        
        # Verifica se há erro na resposta
        if "errors" in response:
            return response, 400
        
        return response, 200
