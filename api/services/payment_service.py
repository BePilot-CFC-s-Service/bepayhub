from datetime import datetime
from repositories.supabase_repository import SupabaseRepository
from repositories.asaas_repository import AsaasRepository
from errors import ValidationError, NotFoundError
from utils.validators import validate_required_fields
from utils.asaas_status import map_asaas_status_to_payment_status
from models.enums import PaymentStatus

class PaymentService:
    def __init__(self):
        self.supabase = SupabaseRepository
        self.asaas = AsaasRepository

    def _get_due_date(self, lesson: dict) -> str:
        """Retorna a data de vencimento no formato YYYY-MM-DD."""
        payment_deadline = lesson.get("payment_deadline")
        if payment_deadline:
            if isinstance(payment_deadline, str):
                due_date = payment_deadline.split("T")[0].split(" ")[0]
                if due_date:
                    return due_date
            else:
                return payment_deadline.strftime("%Y-%m-%d")
        return datetime.now().strftime("%Y-%m-%d")

    def pay_lesson(self, lesson_id: int, data: dict) -> dict:
        """Processa pagamento de uma aula com split e retorna dados do PIX se aplicável."""
        validate_required_fields(data, ["payment_method"])
        payment_method = data["payment_method"].lower()

        # Busca aula
        lesson = self.supabase.fetch_one("lesson", {"id": lesson_id})
        if not lesson:
            raise NotFoundError("Aula não encontrada", 404)

        if lesson["payment_status"] == PaymentStatus.PAID.value:
            return {"success": False, "error": "Aula já paga"}

        # Busca student para obter customer_id
        student = self.supabase.fetch_one("student", {"id": lesson["student_id"]})
        if not student or not student.get("bepayhub_customer_id"):
            raise ValidationError("Student não possui customer cadastrado", 400)

        # Busca instrutor para obter asaas_wallet_id (subconta)
        instructor = self.supabase.fetch_one("instructor", {"id": lesson["instructor_id"]})
        if not instructor:
            raise ValidationError("Instrutor não encontrado", 404)

        wallet_id = instructor.get("asaas_wallet_id")
        if not wallet_id:
            raise ValidationError(
                "Instrutor não possui asaas_wallet_id cadastrado. Crie a subconta primeiro.",
                400
            )

        # Monta payload de pagamento
        payment_payload = {
            "customer": student["bepayhub_customer_id"],
            "billingType": self._map_billing_type(payment_method),
            "value": lesson["total_price"],
            "dueDate": self._get_due_date(lesson),
            "description": f"Aula {lesson_id}",
            "externalReference": f"lesson_{lesson_id}",
        }

        payment_payload["split"] = [
            {
                "walletId": wallet_id,
                "percentualValue": 90
            }
        ]

        if payment_payload["billingType"] == "CREDIT_CARD":
            validate_required_fields(data, ["credit_card", "credit_card_holder_info"])
            payment_payload["creditCard"] = data["credit_card"]
            payment_payload["creditCardHolderInfo"] = data["credit_card_holder_info"]
            payment_payload["remoteIp"] = data.get("remote_ip")

        asaas_response = self.asaas.create_payment(payment_payload)

        mapped_status = map_asaas_status_to_payment_status(asaas_response.get("status", "PENDING"))

        payment_record = {
            "lesson_id": lesson_id,
            "bepayhub_transaction_id": asaas_response["id"],
            "amount": lesson["total_price"],
            "status": mapped_status,
            "method": payment_method,
            "pix_qr_code": asaas_response.get("pixQrCodeUrl"),
            "pix_copy_paste": asaas_response.get("pixCopiaECola"),
            "invoice_url": asaas_response.get("invoiceUrl"),
            "paid_at": asaas_response.get("paidDate"),
        }
        self.supabase.insert("payment", payment_record)

        self.supabase.update("lesson", {"id": lesson_id}, {"payment_status": mapped_status})

        result = {
            "success": True,
            "payment_id": asaas_response["id"],
        }

        if payment_payload["billingType"] == "PIX":
            pix_data = self.asaas.get_pix_qr_code(asaas_response["id"])
            result["pix_qr_code"] = pix_data.get("encodedImage")
            result["pix_copy_paste"] = pix_data.get("payload")

        return result

    def get_payment_status(self, lesson_id: int) -> str:
        """Retorna status de pagamento de uma aula."""
        lesson = self.supabase.fetch_one("lesson", {"id": lesson_id})
        if not lesson:
            raise NotFoundError("Aula não encontrada", 404)

        return lesson["payment_status"].lower()

    def _map_billing_type(self, method: str) -> str:
        mapping = {
            "pix": "PIX",
            "credit_card": "CREDIT_CARD",
            "debit_card": "DEBIT_CARD",
        }
        if method not in mapping:
            raise ValidationError("Método de pagamento inválido", 400)
        return mapping[method]