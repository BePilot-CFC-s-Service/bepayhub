from flask import Blueprint, jsonify, request

from api.application.validators import require_json_body, validate_payment_payload
from api.domain.payment_payload import (
    build_external_reference,
    build_payment_payload,
    get_billing_type,
)
from api.infrastructure import gateway

student_payment_bp = Blueprint("student_payment", __name__)


@student_payment_bp.route(
    "/payments/student/driving-lessons/<method>",
    methods=["POST"],
)
def student_payment(method: str):
    data = require_json_body(request)
    billing_type = get_billing_type(method)
    validate_payment_payload(data, billing_type)
    external_reference = build_external_reference(
        origin="studentPayment",
        student_id=data.get("student_id"),
        lesson_id=data.get("lesson_id"),
    )

    payload = build_payment_payload(
        data=data,
        billing_type=billing_type,
        description="BePilot - Pagamento de Aula de Direcao",
        external_reference=external_reference,
        remote_ip=request.remote_addr,
    )

    response, status_code = gateway.create_payment(payload)
    return jsonify(response), status_code
