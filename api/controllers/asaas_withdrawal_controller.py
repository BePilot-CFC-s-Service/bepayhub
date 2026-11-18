import logging
from hmac import compare_digest

from flask import jsonify, request

from config import Settings
from controllers.base_controller import BaseController
from services.split_authorization_service import SplitAuthorizationService

logger = logging.getLogger(__name__)


class AsaasWithdrawalController(BaseController):
    def __init__(self):
        super().__init__("asaas_withdrawal", url_prefix="")
        self.service = SplitAuthorizationService()
        self.register_route("/asaas/withdrawal-validation", ["POST"], self.validate_withdrawal)

    def validate_withdrawal(self):
        token = Settings.ASAAS_WITHDRAWAL_WEBHOOK_TOKEN
        if len(token) < 32:
            return jsonify({"error": "Webhook de validação não configurado"}), 503
        supplied = request.headers.get("asaas-access-token", "")
        if not compare_digest(supplied.encode("utf-8"), token.encode("utf-8")):
            return jsonify({"error": "Acesso não autorizado"}), 401
        try:
            authorized = self.service.is_authorized(request.get_json(silent=True))
        except Exception:
            logger.warning("Validação de split temporariamente indisponível")
            return jsonify({"error": "Validação temporariamente indisponível"}), 503
        return jsonify({"status": "APPROVED" if authorized else "REFUSED"}), 200