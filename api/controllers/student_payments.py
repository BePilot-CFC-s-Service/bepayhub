from flask import Blueprint, jsonify, request

from application.validators import require_json_body, validate_payment_payload
from domain.payment_payload import get_billing_type
from services import payment_service

student_payment_bp = Blueprint("student_payment", __name__)


@student_payment_bp.route(
    "/payments/student/driving-lessons/<method>",
    methods=["POST"],
)
def student_payment(method: str):
    data = require_json_body(request)
    billing_type = get_billing_type(method)
    validate_payment_payload(data, billing_type)
    response, status_code = payment_service.create_student_payment(
        method, data, request.remote_addr
    )
    return jsonify(response), status_code
