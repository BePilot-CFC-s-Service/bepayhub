"""
Customer Controller - Rotas de gerenciamento de clientes
"""
from flask import request, jsonify
from .base_controller import BaseController
from services.validators import require_json_body
from services.payment_services import CustomerService
from errors import ApiError


class CustomerController(BaseController):
    """Controlador de clientes"""
    
    def __init__(self):
        super().__init__("customers", url_prefix="")
        self.service = CustomerService()
        self._register_routes()
    
    def _register_routes(self):
        """Registra todas as rotas do controlador"""
        self.register_route("/customers", ["POST"], self.create_customer, "create_customer")
        self.register_route("/customers", ["GET"], self.list_customers, "list_customers")
    
    def create_customer(self):
        """
        POST /customers
        Cria um novo cliente
        """
        try:
            data = require_json_body(request)
            response, status_code = self.service.create_customer(data)
            return jsonify(response), status_code
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception as e:
            return jsonify({"error": "Erro interno do servidor"}), 500
    
    def list_customers(self):
        """
        GET /customers
        Lista clientes
        """
        try:
            # Extrai parâmetros de query
            filters = {
                "limit": request.args.get("limit", "100"),
                "offset": request.args.get("offset", "0"),
            }
            
            response, status_code = self.service.list_customers(**filters)
            return jsonify(response), status_code
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception as e:
            return jsonify({"error": "Erro interno do servidor"}), 500
