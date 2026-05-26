"""
Student Controller - Rotas de gerenciamento de pagamentos de aulas
"""
from flask import request, jsonify
from .base_controller import BaseController
from services.validators import require_json_body
from services.payment_services import PaymentService
from errors import ApiError


class StudentController(BaseController):
    """Controlador de pagamentos de estudantes (aulas)"""
    
    def __init__(self):
        super().__init__("students", url_prefix="")
        self.service = PaymentService()
        self._register_routes()
    
    def _register_routes(self):
        """Registra todas as rotas do controlador"""
        # Criar pagamento de aula
        self.register_route(
            "/payments/student/driving-lessons/<method>",
            ["POST"],
            self.create_student_payment,
            "create_student_payment"
        )
        
        # Consultar pagamentos de aula
        self.register_route(
            "/payments/student",
            ["GET"],
            self.list_student_payments,
            "list_student_payments"
        )
    
    def create_student_payment(self, method: str):
        """
        POST /payments/student/driving-lessons/<method>
        Cria pagamento para estudante (aula particular)
        Métodos: pix, credit, debit
        """
        try:
            data = require_json_body(request)
            response, status_code = self.service.create_student_payment(
                method,
                data,
                remote_ip=request.remote_addr
            )
            return jsonify(response), status_code
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception as e:
            return jsonify({"error": "Erro interno do servidor"}), 500
    
    def list_student_payments(self):
        """
        GET /payments/student
        Lista todos os pagamentos de aulas de estudantes
        Query params: student_id, lesson_id, customer, status, limit, offset
        """
        try:
            # Extrai parâmetros de query
            filters = {}
            
            if request.args.get("student_id"):
                filters["student_id"] = request.args.get("student_id")
            if request.args.get("lesson_id"):
                filters["lesson_id"] = request.args.get("lesson_id")
            if request.args.get("customer"):
                filters["customer"] = request.args.get("customer")
            if request.args.get("status"):
                filters["status"] = request.args.get("status")
            
            filters["limit"] = request.args.get("limit", "100")
            filters["offset"] = request.args.get("offset", "0")
            
            response, status_code = self.service.list_payments("student", **filters)
            return jsonify(response), status_code
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception as e:
            return jsonify({"error": "Erro interno do servidor"}), 500
