"""
Models - Representa as tabelas/entidades do Asaas
"""
from typing import Any, Dict, Optional


class Customer:
    """Modelo de Cliente do Asaas"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id: str = data.get("id")
        self.name: str = data.get("name")
        self.email: str = data.get("email")
        self.cpf_cnpj: str = data.get("cpfCnpj")
        self.phone: str = data.get("phone")
        self.external_reference: Optional[str] = data.get("externalReference")
        self.address: Optional[str] = data.get("address")
        self.address_number: Optional[str] = data.get("addressNumber")
        self.city: Optional[str] = data.get("city")
        self.state: Optional[str] = data.get("state")
        self.postal_code: Optional[str] = data.get("postalCode")
        self.created_at: Optional[str] = data.get("createdAt")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte modelo para dicionário"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "cpf_cnpj": self.cpf_cnpj,
            "phone": self.phone,
            "external_reference": self.external_reference,
            "address": self.address,
            "address_number": self.address_number,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "created_at": self.created_at,
        }


class Payment:
    """Modelo de Pagamento do Asaas"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id: str = data.get("id")
        self.customer_id: str = data.get("customer")
        self.value: float = data.get("value")
        self.due_date: str = data.get("dueDate")
        self.billing_type: str = data.get("billingType")
        self.status: str = data.get("status")
        self.external_reference: Optional[str] = data.get("externalReference")
        self.description: Optional[str] = data.get("description")
        self.created_at: Optional[str] = data.get("createdAt")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte modelo para dicionário"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "value": self.value,
            "due_date": self.due_date,
            "billing_type": self.billing_type,
            "status": self.status,
            "external_reference": self.external_reference,
            "description": self.description,
            "created_at": self.created_at,
        }


class Subscription:
    """Modelo de Assinatura do Asaas"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id: str = data.get("id")
        self.customer_id: str = data.get("customer")
        self.value: float = data.get("value")
        self.next_due_date: str = data.get("nextDueDate")
        self.billing_type: str = data.get("billingType")
        self.status: str = data.get("status")
        self.cycle: str = data.get("cycle")
        self.external_reference: Optional[str] = data.get("externalReference")
        self.description: Optional[str] = data.get("description")
        self.created_at: Optional[str] = data.get("createdAt")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte modelo para dicionário"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "value": self.value,
            "next_due_date": self.next_due_date,
            "billing_type": self.billing_type,
            "status": self.status,
            "cycle": self.cycle,
            "external_reference": self.external_reference,
            "description": self.description,
            "created_at": self.created_at,
        }
