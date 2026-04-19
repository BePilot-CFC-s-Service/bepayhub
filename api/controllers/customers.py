from flask import Blueprint, jsonify, request

from application.validators import require_json_body, validate_customer_payload
from services import customer_service

customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/customers", methods=["POST"])
def create_customer():
    data = require_json_body(request)
    validate_customer_payload(data)
    response, status_code = customer_service.create_customer(data)
    return jsonify(response), status_code
