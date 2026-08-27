from repositories.supabase_repository import SupabaseRepository
from utils.asaas_status import map_asaas_status_to_payment_status

class WebhookService:
    def __init__(self):
        self.supabase = SupabaseRepository

    def handle_asaas_webhook(self, payload: dict) -> dict:
        """
        Processa webhook do Asaas (eventos de confirmação de pagamento PIX).
        Retorna {'success': True} mesmo que não encontre o pagamento,
        para evitar que o Asaas fique reenviando.
        """
        event = payload.get("event")
        payment = payload.get("payment", {})

        # Eventos que indicam pagamento efetivado
        if event not in ("PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"):
            return {"success": True, "ignored": True}

        transaction_id = payment.get("id")
        if not transaction_id:
            return {"success": True, "ignored": True}

        # Busca registro no Supabase pelo bepayhub_transaction_id
        payment_record = self.supabase.fetch_one(
            "payment",
            {"bepayhub_transaction_id": transaction_id}
        )
        if not payment_record:
            return {"success": True, "ignored": True}

        mapped_status = map_asaas_status_to_payment_status(payment.get("status", "RECEIVED"))

        # Atualiza status na tabela payment
        self.supabase.update(
            "payment",
            {"id": payment_record["id"]},
            {"status": mapped_status, "paid_at": payment.get("paidDate")}
        )

        # Atualiza status na tabela lesson
        lesson_id = payment_record.get("lesson_id")
        if lesson_id:
            self.supabase.update(
                "lesson",
                {"id": lesson_id},
                {"payment_status": mapped_status}
            )

        return {"success": True}