"""
Payload Builders - Constrói payloads para enviar ao Asaas
"""
from typing import Any, Dict, Optional

from errors import ValidationError


BILLING_TYPE_MAP = {
    "pix": "PIX",
    "credit": "CREDIT_CARD",
    "debit": "DEBIT_CARD",
}

ORIGIN_EXTERNAL_REFERENCE_MAP = {
    "student": "studentPayment",
    "instructor": "instructorPayment",
}


def get_billing_type(method: str) -> str:
    """Converte método para tipo de cobrança"""
    billing_type = BILLING_TYPE_MAP.get((method or "").lower())
    if not billing_type:
        raise ValidationError("Método de pagamento inválido", status_code=400)
    return billing_type


def build_payment_payload(
    data: Dict[str, Any],
    billing_type: str,
    description: str,
    external_reference: str,
    remote_ip: Optional[str] = None,
) -> Dict[str, Any]:
    """Constrói payload para criar pagamento"""
    payload = {
        "customer": data["customer_id"],
        "billingType": billing_type,
        "value": data["value"],
        "dueDate": data["due_date"],
        "description": description,
        "externalReference": external_reference,
    }

    if billing_type == "CREDIT_CARD":
        payload["creditCard"] = data["creditCard"]
        payload["creditCardHolderInfo"] = data["creditCardHolderInfo"]
        payload["remoteIp"] = remote_ip

    return payload


def build_subscription_payload(
    data: Dict[str, Any],
    billing_type: str,
    description: str,
    external_reference: str,
    cycle: str,
    remote_ip: Optional[str] = None,
) -> Dict[str, Any]:
    """Constrói payload para criar assinatura"""
    payload = {
        "customer": data["customer_id"],
        "billingType": billing_type,
        "value": data["value"],
        "nextDueDate": data["due_date"],
        "cycle": cycle,
        "description": description,
        "externalReference": external_reference,
    }

    if billing_type == "CREDIT_CARD":
        payload["creditCard"] = data["creditCard"]
        payload["creditCardHolderInfo"] = data["creditCardHolderInfo"]
        payload["remoteIp"] = remote_ip

    return payload


def build_customer_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Constrói payload para criar cliente"""
    payload = {
        "name": data["name"],
        "cpfCnpj": data["cpf_cnpj"],
        "email": data["email"],
        "phone": data["mobile_phone"],
    }
    
    # Adiciona endereço se fornecido
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
    
    # Adiciona referência externa (student_id ou instructor_id)
    external_ref = data.get("external_reference", {})
    ref_parts = []
    if external_ref.get("student_id"):
        ref_parts.append(f"student={external_ref['student_id']}")
    if external_ref.get("instructor_id"):
        ref_parts.append(f"instructor={external_ref['instructor_id']}")
    
    if ref_parts:
        payload["externalReference"] = ":".join(ref_parts)
    
    return payload


def build_external_reference(
    *,
    origin: str,
    student_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    instructor_id: Optional[str] = None,
) -> str:
    """Constrói referência externa para pagamentos"""
    if origin == "studentPayment":
        parts = ["studentPayment"]
        if student_id:
            parts.append(f"student={student_id}")
        if lesson_id:
            parts.append(f"lesson={lesson_id}")
        if instructor_id:
            parts.append(f"instructor={instructor_id}")
        return ":".join(parts)

    if origin == "instructorPayment":
        parts = ["instructorPayment"]
        if instructor_id:
            parts.append(f"instructor={instructor_id}")
        return ":".join(parts)

    raise ValidationError("Origem de pagamento inválida", status_code=400)
