"""
Validators - Validações de entrada de dados
"""
from typing import Any, Dict, Iterable

from flask import Request

from errors import ValidationError


def require_json_body(req: Request) -> Dict[str, Any]:
    """Valida se o corpo da requisição é JSON"""
    if not req.is_json:
        raise ValidationError(
            "Conteúdo da requisição deve ser JSON",
            status_code=400,
        )

    data = req.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Payload JSON inválido", status_code=400)

    return data


def require_fields(data: Dict[str, Any], fields: Iterable[str]) -> None:
    """Valida se campos obrigatórios estão presentes"""
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValidationError(
            "Campos obrigatórios ausentes",
            status_code=400,
            details={"missing": missing},
        )


def validate_payment_payload(data: Dict[str, Any], billing_type: str) -> None:
    """Valida payload de pagamento"""
    require_fields(data, ["customer_id", "value", "due_date"])

    try:
        value = float(data["value"])
    except (TypeError, ValueError) as exc:
        raise ValidationError("Campo value deve ser numérico", status_code=400) from exc

    if value <= 0:
        raise ValidationError("Campo value deve ser maior que zero", status_code=400)

    if billing_type == "CREDIT_CARD":
        require_fields(data, ["creditCard", "creditCardHolderInfo"])


def validate_customer_payload(data: Dict[str, Any]) -> None:
    """Valida payload de cliente"""
    require_fields(data, ["name", "cpf_cnpj", "email", "mobile_phone", "external_reference"])

    external_reference = data.get("external_reference")
    if not isinstance(external_reference, dict):
        raise ValidationError(
            "Campo external_reference deve ser um objeto com student_id ou instructor_id",
            status_code=400,
        )

    has_instructor = external_reference.get("instructor_id") not in (None, "")
    has_student = external_reference.get("student_id") not in (None, "")
    if has_instructor == has_student:
        raise ValidationError(
            "external_reference deve conter exatamente um: instructor_id ou student_id",
            status_code=400,
        )

    # Valida tipos
    try:
        if has_instructor:
            int(external_reference["instructor_id"])
        if has_student:
            int(external_reference["student_id"])
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "external_reference.student_id/instructor_id deve ser inteiro",
            status_code=400,
        ) from exc

    address_fields = ["address", "address_number", "city", "state", "postal_code"]
    if any(data.get(field) not in (None, "") for field in address_fields):
        require_fields(data, address_fields)


def validate_origin(origin: str) -> None:
    """Valida origem de pagamento"""
    if origin not in ("student", "instructor"):
        raise ValidationError(
            "Origem inválida. Use 'student' ou 'instructor'",
            status_code=400,
        )
