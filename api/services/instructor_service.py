from repositories.supabase_repository import SupabaseRepository
from repositories.asaas_repository import AsaasRepository
from errors import ValidationError, NotFoundError, IntegrationError
from utils.validators import validate_required_fields
from models.enums import PaymentStatus, PayoutStatus

class InstructorService:
    def __init__(self):
        self.supabase = SupabaseRepository
        self.asaas = AsaasRepository

    def get_lessons_by_payment_status(self, instructor_id: int, paid: bool) -> list:
        """Retorna lista de aulas pagas ou não pagas para um instrutor."""
        status_filter = PaymentStatus.PAID.value if paid else {"neq": PaymentStatus.PAID.value}
        lessons = self.supabase.fetch_all(
            "lesson",
            {"instructor_id": instructor_id, "payment_status": status_filter}
        )
        if not lessons:
            return []

        result = []
        for lesson in lessons:
            result.append({
                "instructor_id": instructor_id,
                "lesson_id": lesson["id"],
                "payment_status": lesson["payment_status"].lower(),
            })
        return result

    def create_payout(self, instructor_id: int, data: dict) -> dict:
        """Inicia uma transferência para o instrutor."""
        validate_required_fields(data, ["amount"])
        amount = data["amount"]

        # Busca saldo do instrutor
        balance = self.supabase.fetch_one("instructor_balance", {"instructor_id": instructor_id})
        if not balance:
            raise NotFoundError("Instrutor não possui saldo registrado", 404)

        if float(balance["available_amount"]) < float(amount):
            raise ValidationError("Saldo disponível insuficiente", 400)

        # Busca dados do instrutor para obter customer_id e dados bancários
        instructor = self.supabase.fetch_one("instructor", {"id": instructor_id})
        if not instructor or not instructor.get("bepayhub_customer_id"):
            raise ValidationError("Instrutor não possui customer cadastrado", 400)

        # Monta payload de transferência (PIX)
        transfer_payload = {
            "value": amount,
            "pixAddressKey": instructor.get("pix_key"),  # Assumimos que existe campo pix_key no cadastro
            "pixAddressKeyType": "CPF",  # ou outro tipo
            "description": f"Repasse aula instrutor {instructor_id}",
        }

        # Cria transferência no Asaas
        asaas_response = self.asaas.create_transfer(transfer_payload)

        # Atualiza saldo
        new_available = float(balance["available_amount"]) - float(amount)
        new_pending = float(balance.get("pending_amount", 0)) + float(amount)
        self.supabase.update(
            "instructor_balance",
            {"instructor_id": instructor_id},
            {"available_amount": new_available, "pending_amount": new_pending}
        )

        # Cria registro de payout
        payout_record = {
            "instructor_id": instructor_id,
            "amount": amount,
            "status": PayoutStatus.PENDING.value,
            "bepayhub_transfer_id": asaas_response["id"],
            "expected_deposit_date": asaas_response.get("estimatedDepositDate"),
        }
        self.supabase.insert("instructor_payout", payout_record)

        # Cria transação de saldo
        self.supabase.insert("instructor_balance_transaction", {
            "instructor_id": instructor_id,
            "type": "PayoutTransferred",
            "amount": -float(amount),
            "description": f"Transferência payout {asaas_response['id']}",
        })

        return {
            "success": True,
            "transfer_id": asaas_response["id"],
            "amount": amount,
            "status": "pending",
        }

    def get_balance(self, instructor_id: int) -> dict:
        """Retorna saldo total e disponível do instrutor."""
        balance = self.supabase.fetch_one("instructor_balance", {"instructor_id": instructor_id})
        if not balance:
            raise NotFoundError("Instrutor não possui saldo registrado", 404)

        return {
            "total_earned": balance.get("total_earned", 0),
            "available_amount": balance.get("available_amount", 0),
            "pending_amount": balance.get("pending_amount", 0),
        }