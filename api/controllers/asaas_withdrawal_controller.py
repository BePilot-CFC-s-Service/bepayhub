import logging
from hmac import compare_digest

from flask import jsonify, request

from config import Settings
from controllers.base_controller import BaseController
from errors import IntegrationError
from services.split_authorization_service import SplitAuthorizationService

logger = logging.getLogger(__name__)


class AsaasWithdrawalController(BaseController):
    def __init__(self):
        super().__init__("asaas_withdrawal", url_prefix="")
        self.service = SplitAuthorizationService()
        self.register_route("/asaas/withdrawal-validation", ["POST"], self.validate_withdrawal)

    def validate_withdrawal(self):
        token = Settings.ASAAS_WITHDRAWAL_WEBHOOK_TOKEN
        if not token:
            return jsonify({"error": "Webhook de validação não configurado"}), 503
        supplied = request.headers.get("asaas-access-token", "")
        if not compare_digest(supplied.encode("utf-8"), token.encode("utf-8")):
            return jsonify({"error": "Acesso não autorizado"}), 401
        if not all((
            Settings.SUPABASE_URL,
            Settings.SUPABASE_SERVICE_ROLE_KEY,
            Settings.ASAAS_API_URL,
            Settings.ASAAS_API_KEY,
        )):
            logger.warning("Validação de split sem configuração de integração completa")
            return jsonify({"error": "Validação temporariamente indisponível"}), 503
        try:
            authorized = self.service.is_authorized(request.get_json(silent=True))
        except IntegrationError as error:
            logger.warning("Validação de split temporariamente indisponível")
            logger.debug("Falha de integração na validação de split (HTTP %s)", error.status_code)
            return jsonify({"error": "Validação temporariamente indisponível"}), 503
        if authorized:
            return jsonify({"status": "APPROVED"}), 200
        return jsonify({
            "status": "REFUSED",
            "refuseReason": "Operação não autorizada pelas regras de validação",
        }), 200
