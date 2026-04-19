from __future__ import annotations

from typing import Any, Dict


def _obj(
    *,
    properties: Dict[str, Any],
    required: list[str] | None = None,
    additional_properties: bool = False,
    description: str | None = None,
) -> Dict[str, Any]:
    schema: Dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": additional_properties,
    }
    if required:
        schema["required"] = required
    if description:
        schema["description"] = description
    return schema


def _str(*, description: str | None = None, example: Any | None = None, fmt: str | None = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "string"}
    if description:
        schema["description"] = description
    if example is not None:
        schema["example"] = example
    if fmt:
        schema["format"] = fmt
    return schema


def _num(*, description: str | None = None, example: Any | None = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "number"}
    if description:
        schema["description"] = description
    if example is not None:
        schema["example"] = example
    return schema


def _int(*, description: str | None = None, example: Any | None = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "integer"}
    if description:
        schema["description"] = description
    if example is not None:
        schema["example"] = example
    return schema


def openapi_component_schemas() -> Dict[str, Any]:
    # JSON Schemas (OpenAPI 3.0) definidos manualmente, sem depender de Pydantic.

    customer_external_reference = {
        "description": "Use exatamente um: instructor_id OU student_id",
        "oneOf": [
            _obj(
                properties={"instructor_id": _int(description="ID do instrutor")},
                required=["instructor_id"],
                additional_properties=False,
            ),
            _obj(
                properties={"student_id": _int(description="ID do aluno")},
                required=["student_id"],
                additional_properties=False,
            ),
        ],
    }

    create_customer_request = _obj(
        properties={
            "name": _str(),
            "cpf_cnpj": _str(description="CPF ou CNPJ"),
            "email": _str(fmt="email"),
            "mobile_phone": _str(),
            "address": _str(),
            "address_number": _str(),
            "city": _str(),
            "state": _str(),
            "postal_code": _str(),
            "complement": _str(),
            "observations": _str(),
            "external_reference": {"$ref": "#/components/schemas/CustomerExternalReference"},
        },
        required=["name", "cpf_cnpj", "email", "mobile_phone", "external_reference"],
        additional_properties=False,
    )

    credit_card = _obj(
        properties={
            "holderName": _str(),
            "number": _str(),
            "expiryMonth": _str(example="12"),
            "expiryYear": _str(example="2030"),
            "ccv": _str(example="123"),
        },
        required=["holderName", "number", "expiryMonth", "expiryYear", "ccv"],
        additional_properties=False,
    )

    credit_card_holder_info = _obj(
        properties={
            "name": _str(),
            "email": _str(fmt="email"),
            "cpfCnpj": _str(),
            "postalCode": _str(),
            "addressNumber": _str(description="Numero/identificador do endereco"),
            "phone": _str(),
        },
        required=["name", "email", "cpfCnpj", "postalCode", "addressNumber", "phone"],
        additional_properties=False,
    )

    student_payment_request = _obj(
        properties={
            "customer_id": _str(),
            "value": _num(),
            "due_date": _str(example="2026-04-10"),
            "student_id": _int(),
            "lesson_id": _int(),
            "instructor_id": _int(),
            "creditCard": {"$ref": "#/components/schemas/CreditCard"},
            "creditCardHolderInfo": {"$ref": "#/components/schemas/CreditCardHolderInfo"},
        },
        required=["customer_id", "value", "due_date"],
        additional_properties=False,
    )

    instructor_monthly_fee_request = _obj(
        properties={
            "customer_id": _str(),
            "value": _num(),
            "due_date": _str(example="2026-04-10"),
            "instructor_id": _int(),
            "creditCard": {"$ref": "#/components/schemas/CreditCard"},
            "creditCardHolderInfo": {"$ref": "#/components/schemas/CreditCardHolderInfo"},
        },
        required=[
            "customer_id",
            "value",
            "due_date",
            "creditCard",
            "creditCardHolderInfo",
        ],
        additional_properties=False,
    )

    return {
        "CustomerExternalReference": customer_external_reference,
        "CreateCustomerRequest": create_customer_request,
        "CreditCard": credit_card,
        "CreditCardHolderInfo": credit_card_holder_info,
        "StudentPaymentRequest": student_payment_request,
        "InstructorMonthlyFeeRequest": instructor_monthly_fee_request,
    }
