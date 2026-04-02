from typing import Any, Dict, Optional

from api.errors import ValidationError

BILLING_TYPE_MAP = {
    "pix": "PIX",
    "credit": "CREDIT_CARD",
    "debit": "DEBIT_CARD",
}


def get_billing_type(method: str) -> str:
    billing_type = BILLING_TYPE_MAP.get((method or "").lower())
    if not billing_type:
        raise ValidationError("Metodo de pagamento invalido", status_code=400)
    return billing_type


def build_payment_payload(
    data: Dict[str, Any],
    billing_type: str,
    description: str,
    external_reference: str,
    remote_ip: Optional[str] = None,
) -> Dict[str, Any]:
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


def build_external_reference(
    *,
    origin: str,
    student_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    instructor_id: Optional[str] = None,
) -> str:
    if origin == "studentPayment":
        parts = ["studentPayment"]
        if student_id:
            parts.append(f"student={student_id}")
        if lesson_id:
            parts.append(f"lesson={lesson_id}")
        return ":".join(parts)

    if origin == "instructorPayment":
        parts = ["instructorPayment"]
        if instructor_id:
            parts.append(f"instructor={instructor_id}")
        return ":".join(parts)

    raise ValidationError("Origem de pagamento invalida", status_code=400)
