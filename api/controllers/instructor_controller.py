"""
Instructor Controller - Rotas de gerenciamento de pagamentos de instrutores
"""
from flask import request, jsonify
from .base_controller import BaseController
from services.validators import require_json_body
from services.payment_services import PaymentService
from errors import ApiError


class InstructorController(BaseController):
    """Controlador de pagamentos de instrutores (assinaturas e consultas)"""
    
    def __init__(self):
        super().__init__("instructors", url_prefix="")
        self.service = PaymentService()
        self._register_routes()
    
    def _register_routes(self):
        """Registra todas as rotas do controlador"""
        # Criar assinatura/mensalidade do instrutor
        self.register_route(
            "/payments/instructor/monthly-fees",
            ["POST"],
            self.create_instructor_subscription,
            "create_instructor_subscription"
        )
        
        # Consultar pagamentos/assinaturas do instrutor
        self.register_route(
            "/payments/instructor",
            ["GET"],
            self.list_instructor_payments,
            "list_instructor_payments"
        )
    
    def create_instructor_subscription(self):
        """
        POST /payments/instructor/monthly-fees
        Cria assinatura/mensalidade para instrutor
        Requer dados de cartão de crédito
        
        Regras de negócio:
        - Apenas cartão de crédito é aceito
        - Valor mínimo definido por política
        """
        try:
            data = require_json_body(request)
            response, status_code = self.service.create_instructor_subscription(
                data,
                remote_ip=request.remote_addr
            )
            return jsonify(response), status_code
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception as e:
            return jsonify({"error": "Erro interno do servidor"}), 500
    
    def list_instructor_payments(self):
        """
        GET /payments/instructor
        Lista pagamentos e assinaturas do instrutor
        
        Permite consultar:
        - Pagamentos que ele vai receber das aulas (em desenvolvimento)
        - Status da assinatura/mensalidade
        - Histórico de pagamentos
        
        Query params: instructor_id, customer, status, limit, offset
        """
        try:
            # Extrai parâmetros de query
            filters = {}
            
            if request.args.get("instructor_id"):
                filters["instructor_id"] = request.args.get("instructor_id")
            if request.args.get("customer"):
                filters["customer"] = request.args.get("customer")
            if request.args.get("status"):
                filters["status"] = request.args.get("status")
            
            filters["limit"] = request.args.get("limit", "100")
            filters["offset"] = request.args.get("offset", "0")
            
            response, status_code = self.service.list_payments("instructor", **filters)
            return jsonify(response), status_code
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception as e:
            return jsonify({"error": "Erro interno do servidor"}), 500
