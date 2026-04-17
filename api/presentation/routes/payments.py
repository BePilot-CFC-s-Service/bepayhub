from flask import Blueprint, jsonify, request

from api.application.validators import get_external_reference_by_origin, validate_origin
from api.domain.payment_payload import build_external_reference
from api.infrastructure import gateway

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/payments/<origin>", methods=["GET"])
def get_payments(origin: str):
    validate_origin(origin)
    external_reference = build_external_reference(
        origin=get_external_reference_by_origin(origin),
        student_id=request.args.get("student_id"),
        lesson_id=request.args.get("lesson_id"),
        instructor_id=request.args.get("instructor_id"),
    )

    query_params = {
        "customer": request.args.get("customer"),
        "status": request.args.get("status"),
        "limit": request.args.get("limit"),
        "offset": request.args.get("offset"),
    }
    sanitized_query_params = {
        key: value for key, value in query_params.items() if value not in (None, "")
    }

    response, status_code = gateway.list_payments(
        external_reference=external_reference,
        extra_params=sanitized_query_params,
    )
    return jsonify(response), status_code
