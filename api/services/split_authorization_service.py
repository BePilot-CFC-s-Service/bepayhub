import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from errors import IntegrationError
from models.enums import LessonStatus
from repositories.asaas_repository import AsaasRepository
from repositories.supabase_repository import SupabaseRepository
from services.payment_split import INSTRUCTOR_SPLIT_PERCENT

logger = logging.getLogger(__name__)


class SplitAuthorizationService:
    def __init__(self):
        self.supabase = SupabaseRepository
        self.asaas = AsaasRepository

    @staticmethod
    def _decimal(value):
        if value is None or isinstance(value, bool):
            return None
        try:
            number = Decimal(str(value))
            return number if number.is_finite() else None
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _refuse(reason):
        logger.warning("Validação de split recusada: %s", reason)
        return False

    def is_authorized(self, payload):
        if not isinstance(payload, dict) or payload.get("type") != "PAYMENT_SPLIT":
            return self._refuse("tipo_nao_suportado")
        split = payload.get("paymentSplit")
        if not isinstance(split, dict) or split.get("status") != "AWAITING_CREDIT":
            return self._refuse("evento_invalido")
        payment_reference = split.get("payment")
        if not isinstance(payment_reference, dict):
            return self._refuse("pagamento_ausente")
        payment_id = payment_reference.get("id")
        split_id = split.get("id")
        wallet_id = split.get("walletId")
        if not all(isinstance(value, str) and value.strip() for value in (payment_id, split_id, wallet_id)):
            return self._refuse("identificadores_invalidos")

        payments = self.supabase.fetch_all_service_role("payment", {"bepayhub_transaction_id": payment_id})
        if not payments:
            raise IntegrationError("Pagamento ainda não está disponível para validação", 503)
        if len(payments) != 1:
            return self._refuse("pagamentos_ambiguos")
        payment = payments[0]
        if payment.get("bepayhub_transaction_id") != payment_id or not payment.get("lesson_id"):
            return self._refuse("pagamento_divergente")
        lesson_id = payment["lesson_id"]
        expected_reference = f"lesson_{lesson_id}"
        if payment_reference.get("externalReference") != expected_reference:
            return self._refuse("referencia_evento_divergente")

        lesson = self.supabase.fetch_one_service_role("lesson", {"id": lesson_id})
        if not lesson or lesson.get("status") in (LessonStatus.CANCELLED.value, LessonStatus.NO_SHOW.value):
            return self._refuse("aula_invalida")
        instructor_id = lesson.get("instructor_id")
        if not instructor_id:
            return self._refuse("instrutor_ausente")
        instructor = self.supabase.fetch_one_service_role("instructor", {"id": instructor_id})
        if not instructor or instructor.get("asaas_wallet_id") != wallet_id:
            return self._refuse("carteira_divergente")

        provider_payment = self.asaas.get_payment(payment_id)
        if (
            not isinstance(provider_payment, dict)
            or provider_payment.get("id") != payment_id
            or provider_payment.get("externalReference") != expected_reference
            or provider_payment.get("status") not in ("CONFIRMED", "RECEIVED")
        ):
            return self._refuse("cobranca_divergente")

        provider_splits = provider_payment.get("split")
        if not isinstance(provider_splits, list):
            return self._refuse("splits_indisponiveis")
        matching = [item for item in provider_splits if isinstance(item, dict) and item.get("id") == split_id]
        if (
            len(matching) != 1
            or matching[0].get("walletId") != wallet_id
            or matching[0].get("status") != "AWAITING_CREDIT"
        ):
            return self._refuse("split_divergente")
        provider_split = matching[0]
        if any(
            self._decimal(item.get("percentualValue")) != Decimal(INSTRUCTOR_SPLIT_PERCENT)
            for item in (split, provider_split)
        ):
            return self._refuse("percentual_divergente")
        for item in (split, provider_split):
            fixed_value = item.get("fixedValue")
            if fixed_value is not None and self._decimal(fixed_value) != Decimal("0"):
                return self._refuse("valor_fixo_nao_permitido")

        total = self._decimal(payment.get("amount"))
        provider_total = self._decimal(provider_payment.get("value"))
        net_value = self._decimal(provider_payment.get("netValue"))
        split_value = self._decimal(split.get("totalValue"))
        provider_split_value = self._decimal(provider_split.get("totalValue"))
        if (
            total is None
            or total <= 0
            or provider_total != total
            or net_value is None
            or net_value <= 0
            or split_value is None
            or provider_split_value is None
        ):
            return self._refuse("valores_invalidos")
        expected = (net_value * Decimal(INSTRUCTOR_SPLIT_PERCENT) / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if split_value != expected or provider_split_value != expected:
            return self._refuse("valor_split_divergente")
        logger.info("Validação de split aprovada")
        return True
