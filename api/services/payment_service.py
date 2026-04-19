from typing import Any, Dict, Optional

from application.validators import get_external_reference_by_origin
from domain.payment_payload import (
    build_external_reference,
    build_payment_payload,
    build_subscription_payload,
    get_billing_type,
)
from repositories import payment_repository


def create_student_payment(method: str, data: Dict[str, Any], remote_ip: str) -> Any:
    billing_type = get_billing_type(method)
    external_reference = build_external_reference(
        origin="studentPayment",
        student_id=data.get("student_id"),
        lesson_id=data.get("lesson_id"),
        instructor_id=data.get("instructor_id")
    )

    payload = build_payment_payload(
        data=data,
        billing_type=billing_type,
        description="BePilot - Pagamento de Aula de Direcao",
        external_reference=external_reference,
        remote_ip=remote_ip,
    )

    payment_response, payment_status = payment_repository.create_payment(payload)

    # Para PIX, buscar o billingInfo para retornar apenas os dados essenciais do QRCode.
    if payment_status in (200, 201) and billing_type == "PIX":
        payment_id = (payment_response or {}).get("id")
        if not payment_id:
            return {"error": "Pagamento PIX criado sem id retornado pelo Asaas"}, 502

        billing_info, billing_status = payment_repository.get_payment_billing_info(payment_id)
        if billing_status not in (200, 201):
            return {
                "error": "Falha ao obter dados PIX do Asaas",
                "details": {"payment_id": payment_id, "status": billing_status, "body": billing_info},
            }, 502

        pix = (billing_info or {}).get("pix")
        if not pix:
            return {
                "error": "Resposta do Asaas sem dados PIX",
                "details": {"payment_id": payment_id, "billingInfo": billing_info},
            }, 502

        return {
            "id": payment_id,
            "pix": {
                "encodedImage": pix.get("encodedImage"),
                "payload": pix.get("payload"),
                "expirationDate": pix.get("expirationDate"),
            },
        }, payment_status

    return payment_response, payment_status


def create_instructor_subscription(data: Dict[str, Any], remote_ip: str) -> Any:
    billing_type = "CREDIT_CARD"
    external_reference = build_external_reference(
        origin="instructorPayment",
        instructor_id=data.get("instructor_id"),
    )


    payload = build_subscription_payload(
        data=data,
        billing_type=billing_type,
        cycle="MONTHLY",
        description="Assinatura Plano Inicial",
        external_reference=external_reference,
        remote_ip=remote_ip,
    )

    return payment_repository.create_subscription(payload)


def list_payments(
    origin: str,
    student_id: Optional[str],
    lesson_id: Optional[str],
    instructor_id: Optional[str],
    query_params: Dict[str, Any],
) -> Any:
    external_reference = build_external_reference(
        origin=get_external_reference_by_origin(origin),
        student_id=student_id,
        lesson_id=lesson_id,
        instructor_id=instructor_id,
    )

    sanitized_query_params = {
        key: value for key, value in query_params.items() if value not in (None, "")
    }

    return payment_repository.list_payments(
        external_reference=external_reference,
        extra_params=sanitized_query_params,
    )
