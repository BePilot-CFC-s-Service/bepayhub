from flask import Blueprint, jsonify, request

from application.validators import require_json_body, validate_payment_payload
from services import payment_service

instructor_payment_bp = Blueprint("instructor_payment", __name__)


@instructor_payment_bp.route(
    "/payments/instructor/monthly-fees",
    methods=["POST"],
)
def instructor_payment():
    data = require_json_body(request)
    validate_payment_payload(data, "CREDIT_CARD")
    response, status_code = payment_service.create_instructor_subscription(
        data, request.remote_addr
    )
    return jsonify(response), status_code
