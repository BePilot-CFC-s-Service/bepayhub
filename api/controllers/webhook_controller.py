from flask import request, jsonify
from .base_controller import BaseController
from services.webhook_service import WebhookService
from errors import ApiError

class WebhookController(BaseController):
    def __init__(self):
        super().__init__("webhooks", url_prefix="")
        self.service = WebhookService()
        self._register_routes()

    def _register_routes(self):
        self.register_route(
            "/webhooks/asaas",
            ["POST"],
            self.handle_asaas_webhook,
            "asaas_webhook"
        )

    def handle_asaas_webhook(self):
        try:
            data = request.get_json(silent=True)
            if not data:
                raise ApiError("Payload JSON inválido", 400)

            result = self.service.handle_asaas_webhook(data)
            return jsonify(result), 200
        except ApiError as e:
            return jsonify({"error": e.message, "details": e.details}), e.status_code
        except Exception:
            # Não retorna 500 para não causar retries indevidos
            return jsonify({"success": False, "error": "Erro interno"}), 200