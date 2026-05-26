"""
DTOs (Data Transfer Objects) - Responsáveis por entrada e saída de dados
"""
from typing import Any, Dict, Optional


class PaymentDTO:
    """DTO para dados de pagamento"""
    
    def __init__(
        self,
        customer_id: str,
        value: float,
        due_date: str,
        billing_type: Optional[str] = None,
        credit_card: Optional[Dict[str, Any]] = None,
        credit_card_holder_info: Optional[Dict[str, Any]] = None,
        student_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        instructor_id: Optional[str] = None,
        remote_ip: Optional[str] = None,
    ):
        self.customer_id = customer_id
        self.value = value
        self.due_date = due_date
        self.billing_type = billing_type
        self.credit_card = credit_card
        self.credit_card_holder_info = credit_card_holder_info
        self.student_id = student_id
        self.lesson_id = lesson_id
        self.instructor_id = instructor_id
        self.remote_ip = remote_ip
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte DTO para dicionário"""
        return {
            "customer_id": self.customer_id,
            "value": self.value,
            "due_date": self.due_date,
            "billing_type": self.billing_type,
            "credit_card": self.credit_card,
            "credit_card_holder_info": self.credit_card_holder_info,
            "student_id": self.student_id,
            "lesson_id": self.lesson_id,
            "instructor_id": self.instructor_id,
            "remote_ip": self.remote_ip,
        }


class CustomerDTO:
    """DTO para dados de cliente"""
    
    def __init__(
        self,
        name: str,
        email: str,
        cpf_cnpj: str,
        mobile_phone: str,
        external_reference: Dict[str, Any],
        address: Optional[str] = None,
        address_number: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
    ):
        self.name = name
        self.email = email
        self.cpf_cnpj = cpf_cnpj
        self.mobile_phone = mobile_phone
        self.external_reference = external_reference
        self.address = address
        self.address_number = address_number
        self.city = city
        self.state = state
        self.postal_code = postal_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte DTO para dicionário"""
        return {
            "name": self.name,
            "email": self.email,
            "cpf_cnpj": self.cpf_cnpj,
            "mobile_phone": self.mobile_phone,
            "external_reference": self.external_reference,
            "address": self.address,
            "address_number": self.address_number,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
        }
