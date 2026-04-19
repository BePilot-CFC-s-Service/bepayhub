from flask import Blueprint, jsonify, request

from application.validators import validate_origin
from services import payment_service

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/payments/<origin>", methods=["GET"])
def get_payments(origin: str):
    validate_origin(origin)
    query_params = {
        "customer": request.args.get("customer"),
        "status": request.args.get("status"),
        "limit": request.args.get("limit"),
        "offset": request.args.get("offset"),
    }
    response, status_code = payment_service.list_payments(
        origin=origin,
        student_id=request.args.get("student_id"),
        lesson_id=request.args.get("lesson_id"),
        instructor_id=request.args.get("instructor_id"),
        query_params=query_params,
    )
    return jsonify(response), status_code
