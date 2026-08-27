from flask import request, jsonify, current_app
from .base_controller import BaseController
from services.subaccount_service import SubaccountService
from errors import ApiError

class InstructorSubaccountController(BaseController):
    def __init__(self):
        super().__init__("instructor_subaccounts", url_prefix="")
        self.service = SubaccountService()
        self._register_routes()

    def _register_routes(self):
        self.register_route(
            "/instructors/<int:instructor_id>/subaccount",
            ["POST"],
            self.create_subaccount,
            "create_instructor_subaccount"
        )

    def create_subaccount(self, instructor_id):
        try:
            result = self.service.create_subaccount(instructor_id)
            return jsonify(result), 201
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception as e:
            current_app.logger.exception("Erro inesperado em create_subaccount")
            return jsonify({"error": "Erro interno do servidor"}), 500