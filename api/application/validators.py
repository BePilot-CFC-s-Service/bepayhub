from typing import Any, Dict, Iterable

from flask import Request

from api.errors import ValidationError


ORIGIN_EXTERNAL_REFERENCE_MAP = {
    "student": "studentPayment",
    "instructor": "instructorPayment",
}


def require_json_body(req: Request) -> Dict[str, Any]:
    if not req.is_json:
        raise ValidationError(
            "Conteudo da requisicao deve ser JSON",
            status_code=400,
        )

    data = req.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Payload JSON invalido", status_code=400)

    return data


def require_fields(data: Dict[str, Any], fields: Iterable[str]) -> None:
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValidationError(
            "Campos obrigatorios ausentes",
            status_code=400,
            details={"missing": missing},
        )


def validate_payment_payload(data: Dict[str, Any], billing_type: str) -> None:
    require_fields(data, ["customer_id", "value", "due_date"])

    try:
        value = float(data["value"])
    except (TypeError, ValueError) as exc:
        raise ValidationError("Campo value deve ser numerico", status_code=400) from exc

    if value <= 0:
        raise ValidationError("Campo value deve ser maior que zero", status_code=400)

    if billing_type == "CREDIT_CARD":
        require_fields(data, ["creditCard", "creditCardHolderInfo"])


def validate_customer_payload(data: Dict[str, Any]) -> None:
    require_fields(data, ["name", "cpf_cnpj", "email"])


def validate_origin(origin: str) -> None:
    if origin not in ORIGIN_EXTERNAL_REFERENCE_MAP:
        raise ValidationError(
            "Origem invalida. Use student ou instructor",
            status_code=400,
        )


def get_external_reference_by_origin(origin: str) -> str:
    return ORIGIN_EXTERNAL_REFERENCE_MAP[origin]
