
from flask import request, jsonify
from .base_controller import BaseController
from services.payment_service import PaymentService
from services.instructor_service import InstructorService
from errors import ApiError
from utils.instructor_auth import require_instructor_owner

class PaymentController(BaseController):
    def __init__(self):
        super().__init__("payments", url_prefix="")
        self.payment_service = PaymentService()
        self.instructor_service = InstructorService()
        self._register_routes()

    def _register_routes(self):
        # Payment endpoints
        self.register_route(
            "/lessons/<int:lesson_id>/pay", ["POST"], self.pay_lesson
        )
        self.register_route(
            "/lessons/<int:lesson_id>/payment-status", ["GET"], self.get_payment_status
        )

        # Instructor endpoints
        self.register_route(
            "/instructors/<uuid:instructor_id>/lessons/paid", ["GET"], require_instructor_owner(self.get_paid_lessons)
        )
        self.register_route(
            "/instructors/<uuid:instructor_id>/lessons/unpaid", ["GET"], require_instructor_owner(self.get_unpaid_lessons)
        )
        self.register_route(
            "/instructors/<uuid:instructor_id>/payout", ["POST"], require_instructor_owner(self.create_payout)
        )
        self.register_route(
            "/instructors/<uuid:instructor_id>/balance", ["GET"], require_instructor_owner(self.get_balance)
        )
        self.register_route(
            "/instructors/<uuid:instructor_id>/transactions", ["GET"], require_instructor_owner(self.get_transactions)
        )
        self.register_route(
            "/instructors/<uuid:instructor_id>/payouts", ["GET"], require_instructor_owner(self.get_payouts)
        )

    def pay_lesson(self, lesson_id):
        try:
            data = request.get_json(silent=True)
            if not data:
                raise ApiError("Payload JSON inválido", 400)

            result = self.payment_service.pay_lesson(lesson_id, data)
            return jsonify(result), 200
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception:
            return jsonify({"error": "Erro interno do servidor"}), 500

    def get_payment_status(self, lesson_id):
        try:
            status = self.payment_service.get_payment_status(lesson_id)
            return jsonify({"status": status}), 200
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception:
            return jsonify({"error": "Erro interno do servidor"}), 500

    def get_paid_lessons(self, instructor_id):
        try:
            lessons = self.instructor_service.get_lessons_by_payment_status(instructor_id, paid=True)
            return jsonify(lessons), 200
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception:
            return jsonify({"error": "Erro interno do servidor"}), 500

    def get_unpaid_lessons(self, instructor_id):
        try:
            lessons = self.instructor_service.get_lessons_by_payment_status(instructor_id, paid=False)
            return jsonify(lessons), 200
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception:
            return jsonify({"error": "Erro interno do servidor"}), 500

    def create_payout(self, instructor_id):
        try:
            data = request.get_json(silent=True)
            if not isinstance(data, dict) or not data:
                raise ApiError("Payload JSON inválido", 400)

            result = self.instructor_service.create_payout(instructor_id, data)
            return jsonify(result), 200
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception:
            return jsonify({"error": "Erro interno do servidor"}), 500

    def get_balance(self, instructor_id):
        try:
            balance = self.instructor_service.get_balance(instructor_id)
            return jsonify(balance), 200
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception:
            return jsonify({"error": "Erro interno do servidor"}), 500

    def get_transactions(self, instructor_id):
        return jsonify(self.instructor_service.get_transactions(instructor_id)), 200

    def get_payouts(self, instructor_id):
        return jsonify(self.instructor_service.get_payouts(instructor_id)), 200
