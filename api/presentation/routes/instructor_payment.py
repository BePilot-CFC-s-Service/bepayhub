from flask import Blueprint, jsonify, request

from api.application.validators import require_json_body, validate_payment_payload
from api.domain.payment_payload import build_external_reference, build_payment_payload
from api.infrastructure import gateway

instructor_payment_bp = Blueprint("instructor_payment", __name__)


@instructor_payment_bp.route(
    "/payments/instructor/monthly-fees",
    methods=["POST"],
)
def instructor_payment():
    data = require_json_body(request)
    billing_type = "CREDIT_CARD"
    validate_payment_payload(data, billing_type)
    external_reference = build_external_reference(
        origin="instructorPayment",
        instructor_id=data.get("instructor_id"),
    )

    payload = build_payment_payload(
        data=data,
        billing_type=billing_type,
        description="BePilot - Mensalidade Instrutor",
        external_reference=external_reference,
        remote_ip=request.remote_addr,
    )

    response, status_code = gateway.create_payment(payload)
    return jsonify(response), status_code
