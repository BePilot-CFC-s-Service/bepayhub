from flask import Blueprint, jsonify, request

from api.schemas.validators import require_json_body, validate_subscription_payload
from api.services import gateway
from api.services.payment_payload import build_external_reference, build_subscription_payload

instructor_subscription_bp = Blueprint("instructor_subscription", __name__)


@instructor_subscription_bp.route(
    "/subscriptions/instructor/monthly-fees",
    methods=["POST"],
)
def instructor_subscription():
    data = require_json_body(request)
    validate_subscription_payload(data)
    external_reference = build_external_reference(
        origin="instructorSubscription",
        instructor_id=data.get("instructor_id"),
    )

    payload = build_subscription_payload(
        data=data,
        description="Assinatura Plano Pró",
        external_reference=external_reference,
        remote_ip=request.remote_addr,
    )

    response, status_code = gateway.create_subscription(payload)
    return jsonify(response), status_code
