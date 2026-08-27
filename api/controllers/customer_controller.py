
from flask import request, jsonify, current_app
from .base_controller import BaseController
from services.customer_service import CustomerService
from errors import ApiError

class CustomerController(BaseController):
    def __init__(self):
        super().__init__("customers", url_prefix="")
        self.service = CustomerService()
        self._register_routes()

    def _register_routes(self):
        self.register_route("/customers", ["POST"], self.create_customer)

    def create_customer(self):
        try:
            data = request.get_json(silent=True)
            if not data:
                raise ApiError("Payload JSON inválido", 400)

            customer_id = self.service.create_customer(data)
            return jsonify({"customer_id": customer_id}), 201
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception as e:
            # Loga o traceback completo no console
            current_app.logger.exception("Erro inesperado em create_customer")
            return jsonify({"error": "Erro interno do servidor"}), 500
