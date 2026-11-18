
from hmac import compare_digest
from flask import request, jsonify
from .base_controller import BaseController
from config import Settings
from services.payment_service import PaymentService
from services.instructor_service import InstructorService
from services.anticipation_service import AnticipationService
from errors import ApiError

class PaymentController(BaseController):
    def __init__(self):
        super().__init__("payments", url_prefix="")
        self.payment_service = PaymentService()
        self.instructor_service = InstructorService()
        self.anticipation_service = AnticipationService()
        self._register_routes()

    def _register_routes(self):
        # Payment endpoints
        self.register_route(
            "/lessons/<int:lesson_id>/pay", ["POST"], self.pay_lesson
        )
        self.register_route(
            "/lessons/<int:lesson_id>/payment-status", ["GET"], self.get_payment_status
        )
        self.register_route(
            "/lessons/<int:lesson_id>/refund", ["POST"], self.request_refund
        )
        self.register_route(
            "/lessons/<int:lesson_id>/refund", ["GET"], self.get_refund_status
        )
        self.register_route(
            "/anticipations/configuration", ["GET"], self.get_anticipation_configuration
        )
        self.register_route(
            "/instructors/<int:instructor_id>/anticipations/configuration", ["GET"], self.get_instructor_anticipation_configuration
        )
        self.register_route(
            "/lessons/<int:lesson_id>/anticipations/simulate", ["POST"], self.simulate_anticipation
        )

        # Instructor endpoints
        self.register_route(
            "/instructors/<int:instructor_id>/lessons/paid", ["GET"], self.get_paid_lessons
        )
        self.register_route(
            "/instructors/<int:instructor_id>/lessons/unpaid", ["GET"], self.get_unpaid_lessons
        )
        self.register_route(
            "/instructors/<int:instructor_id>/payout", ["POST"], self.create_payout
        )
        self.register_route(
            "/instructors/<int:instructor_id>/balance", ["GET"], self.get_balance
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

    @staticmethod
    def _require_refund_authorization():
        key = Settings.REFUND_API_KEY
        if len(key) < 32:
            raise ApiError("Estornos não configurados", 503)
        supplied = request.headers.get("Authorization", "")
        if not compare_digest(supplied.encode("utf-8"), f"Bearer {key}".encode("utf-8")):
            raise ApiError("Acesso não autorizado", 401)

    def request_refund(self, lesson_id):
        try:
            self._require_refund_authorization()
            result = self.payment_service.request_refund(lesson_id)
            return jsonify(result), 202
        except ApiError as error:
            return jsonify({"error": error.message, "details": error.details}), error.status_code
        except Exception:
            return jsonify({"error": "Erro interno do servidor"}), 500

    def get_refund_status(self, lesson_id):
        try:
            self._require_refund_authorization()
            result = self.payment_service.get_refund_status(lesson_id)
            return jsonify(result), 200
        except ApiError as error:
            return jsonify({"error": error.message, "details": error.details}), error.status_code
        except Exception:
            return jsonify({"error": "Erro interno do servidor"}), 500

    @staticmethod
    def _require_anticipation_authorization():
        key = Settings.ANTICIPATION_API_KEY
        if len(key) < 32:
            raise ApiError("Consultas de antecipação não configuradas", 503)
        supplied = request.headers.get("Authorization", "")
        if not compare_digest(supplied.encode("utf-8"), f"Bearer {key}".encode("utf-8")):
            raise ApiError("Acesso não autorizado", 401)

    def get_anticipation_configuration(self):
        try:
            self._require_anticipation_authorization()
            return jsonify(self.anticipation_service.get_configuration()), 200
        except ApiError as error:
            return jsonify({"error": error.message, "details": error.details}), error.status_code
        except Exception:
            return jsonify({"error": "Erro interno do servidor"}), 500

    def get_instructor_anticipation_configuration(self, instructor_id):
        try:
            self._require_anticipation_authorization()
            return jsonify(self.anticipation_service.get_configuration(instructor_id)), 200
        except ApiError as error:
            return jsonify({"error": error.message, "details": error.details}), error.status_code
        except Exception:
            return jsonify({"error": "Erro interno do servidor"}), 500

    def simulate_anticipation(self, lesson_id):
        try:
            self._require_anticipation_authorization()
            return jsonify(self.anticipation_service.simulate_lesson(lesson_id)), 200
        except ApiError as error:
            return jsonify({"error": error.message, "details": error.details}), error.status_code
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
            if not data:
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
