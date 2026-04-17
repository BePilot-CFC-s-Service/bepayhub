from flask import Blueprint, jsonify, request

from api.application.validators import require_json_body, validate_customer_payload
from api.infrastructure import gateway

customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/customers", methods=["POST"])
def create_customer():
    data = require_json_body(request)
    validate_customer_payload(data)

    payload = {
        "name": data["name"],
        "cpfCnpj": data["cpf_cnpj"],
        "email": data["email"],
    }

    response, status_code = gateway.create_customer(payload)
    return jsonify(response), status_code
