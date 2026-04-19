from typing import Any, Dict

from repositories import payment_repository


def create_customer(data: Dict[str, Any]) -> Any:
    external_reference = data.get("external_reference") or {}
    if isinstance(external_reference, dict) and external_reference.get("instructor_id") not in (
        None,
        "",
    ):
        external_reference_str = f"instructor={int(external_reference['instructor_id'])}"
    elif isinstance(external_reference, dict) and external_reference.get("student_id") not in (
        None,
        "",
    ):
        external_reference_str = f"student={int(external_reference['student_id'])}"
    else:
        # A validação já garante o formato, mas mantemos fallback seguro
        external_reference_str = None

    payload: Dict[str, Any] = {
        "name": data["name"],
        "cpfCnpj": data["cpf_cnpj"],
        "email": data["email"],
        "mobilePhone": data["mobile_phone"],
        "notificationDisabled": False,
    }

    optional_fields_map = {
        "address": "address",
        "address_number": "addressNumber",
        "city": "city",
        "state": "state",
        "postal_code": "postalCode",
        "complement": "complement",
        "observations": "observations",
    }

    for input_key, output_key in optional_fields_map.items():
        value = data.get(input_key)
        if value not in (None, ""):
            payload[output_key] = value

    if external_reference_str:
        payload["externalReference"] = external_reference_str


    return payment_repository.create_customer(payload)
