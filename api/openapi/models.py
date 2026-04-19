from __future__ import annotations

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class CustomerExternalReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instructor_id: Optional[int] = Field(
        default=None, description="ID do instrutor (use apenas este OU student_id)"
    )
    student_id: Optional[int] = Field(
        default=None, description="ID do aluno (use apenas este OU instructor_id)"
    )

    @model_validator(mode="after")
    def _xor_student_instructor(self) -> "CustomerExternalReference":
        has_instructor = self.instructor_id is not None
        has_student = self.student_id is not None
        if has_instructor == has_student:
            raise ValueError(
                "external_reference deve conter exatamente um: instructor_id ou student_id"
            )
        return self


class CreateCustomerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    cpf_cnpj: str = Field(..., description="CPF ou CNPJ")
    email: EmailStr
    mobile_phone: str

    # Endereço (opcional; se enviar um, idealmente enviar todos)
    address: Optional[str] = None
    address_number: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

    # Extras
    complement: Optional[str] = None
    observations: Optional[str] = None
    external_reference: CustomerExternalReference


class CreditCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    holderName: str
    number: str
    expiryMonth: str
    expiryYear: str
    ccv: str


class CreditCardHolderInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    email: EmailStr
    cpfCnpj: str
    postalCode: str
    addressNumber: str
    phone: str


class StudentPaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str
    value: float
    due_date: str = Field(..., json_schema_extra={"example": "2026-04-10"})
    student_id: Optional[str] = None
    lesson_id: Optional[str] = None
    instructor_id: Optional[str] = None

    # Obrigatório apenas quando method=credit
    creditCard: Optional[CreditCard] = None
    creditCardHolderInfo: Optional[CreditCardHolderInfo] = None


class InstructorMonthlyFeeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str
    value: float
    due_date: str = Field(..., json_schema_extra={"example": "2026-04-10"})
    instructor_id: Optional[str] = None

    creditCard: CreditCard
    creditCardHolderInfo: CreditCardHolderInfo


def openapi_component_schemas() -> Dict[str, Any]:
    models: tuple[Type[BaseModel], ...] = (
        CustomerExternalReference,
        CreateCustomerRequest,
        CreditCard,
        CreditCardHolderInfo,
        StudentPaymentRequest,
        InstructorMonthlyFeeRequest,
    )

    merged: Dict[str, Any] = {}
    for model in models:
        schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
        defs = schema.pop("$defs", {})
        merged.update(defs)
        merged[model.__name__] = schema

    return merged
