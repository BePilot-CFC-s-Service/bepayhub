import asyncio
from concurrent.futures import ThreadPoolExecutor
from repositories.supabase_repository import SupabaseRepository
from repositories.asaas_repository import AsaasRepository
from errors import ValidationError, NotFoundError, IntegrationError
from utils.validators import validate_required_fields
from models.enums import PaymentStatus

class PaymentService:
    def __init__(self):
        self.supabase = SupabaseRepository
        self.asaas = AsaasRepository

    def pay_lesson(self, lesson_id: int, data: dict) -> dict:
        """Processa pagamento de uma aula."""
        validate_required_fields(data, ["payment_method"])
        payment_method = data["payment_method"].lower()

        # Busca aula
        lesson = self.supabase.fetch_one("lesson", {"id": lesson_id})
        if not lesson:
            raise NotFoundError("Aula não encontrada", 404)

        # Verifica se aula já está paga
        if lesson["payment_status"] == PaymentStatus.PAID.value:
            return {"success": False, "error": "Aula já paga"}

        # Busca student para obter customer_id
        student = self.supabase.fetch_one("student", {"id": lesson["student_id"]})
        if not student or not student.get("bepayhub_customer_id"):
            raise ValidationError("Student não possui customer cadastrado", 400)

        # Monta payload de pagamento
        payment_payload = {
            "customer": student["bepayhub_customer_id"],
            "billingType": self._map_billing_type(payment_method),
            "value": lesson["total_price"],
            "dueDate": lesson["payment_deadline"].split("T")[0] if lesson.get("payment_deadline") else None,
            "description": f"Aula {lesson_id}",
            "externalReference": f"lesson_{lesson_id}",
        }

        # Adiciona dados de cartão se necessário
        if payment_payload["billingType"] == "CREDIT_CARD":
            validate_required_fields(data, ["credit_card", "credit_card_holder_info"])
            payment_payload["creditCard"] = data["credit_card"]
            payment_payload["creditCardHolderInfo"] = data["credit_card_holder_info"]
            payment_payload["remoteIp"] = data.get("remote_ip")

        # Cria pagamento no Asaas
        asaas_response = self.asaas.create_payment(payment_payload)

        # Cria registro de pagamento no Supabase
        payment_record = {
            "lesson_id": lesson_id,
            "bepayhub_transaction_id": asaas_response["id"],
            "amount": lesson["total_price"],
            "status": asaas_response["status"],  # PENDING, etc.
            "method": payment_method,
            "pix_qr_code": asaas_response.get("pixQrCodeUrl"),
            "pix_copy_paste": asaas_response.get("pixCopiaECola"),
            "invoice_url": asaas_response.get("invoiceUrl"),
            "paid_at": asaas_response.get("paidDate"),
        }
        self.supabase.insert("payment", payment_record)

        # Atualiza status da aula se necessário
        if asaas_response["status"] == "CONFIRMED":
            self.supabase.update("lesson", {"id": lesson_id}, {"payment_status": PaymentStatus.PAID.value})
        else:
            self.supabase.update("lesson", {"id": lesson_id}, {"payment_status": PaymentStatus.PENDING.value})

        return {"success": True}

    def get_payment_status(self, lesson_id: int) -> str:
        """Retorna status de pagamento de uma aula."""
        lesson = self.supabase.fetch_one("lesson", {"id": lesson_id})
        if not lesson:
            raise NotFoundError("Aula não encontrada", 404)

        payment_status = lesson["payment_status"]
        # Mapeia para minúsculo
        return payment_status.lower()

    def _map_billing_type(self, method: str) -> str:
        mapping = {
            "pix": "PIX",
            "credit_card": "CREDIT_CARD",
            "debit_card": "DEBIT_CARD",
        }
        if method not in mapping:
            raise ValidationError("Método de pagamento inválido", 400)
        return mapping[method]