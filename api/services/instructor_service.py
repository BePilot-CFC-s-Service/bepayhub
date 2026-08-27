from repositories.supabase_repository import SupabaseRepository
from repositories.asaas_repository import AsaasRepository
from errors import ValidationError, NotFoundError
from utils.validators import validate_required_fields
from models.enums import PaymentStatus

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
                "total_price": lesson["total_price"]
            })
        return result

    def create_payout(self, instructor_id: int, data: dict) -> dict:
        """
        Realiza transferência da subconta do instrutor para uma conta bancária real.
        O instrutor deve possuir subconta (asaas_wallet_id e asaas_api_key)
        e dados bancários cadastrados.
        """
        validate_required_fields(data, ["amount"])
        amount = data["amount"]

        instructor = self.supabase.fetch_one("instructor", {"id": instructor_id})
        if not instructor:
            raise NotFoundError("Instrutor não encontrado", 404)

        wallet_id = instructor.get("asaas_wallet_id")
        api_key = instructor.get("asaas_api_key")
        if not wallet_id or not api_key:
            raise ValidationError("Instrutor não possui subconta (wallet) para realizar payout", 400)

        bank_code = instructor.get("bank_code")
        agency_number = instructor.get("agency_number")
        account_number = instructor.get("account_number")
        account_digit = instructor.get("account_digit", "")
        account_type = instructor.get("account_type", "CHECKING")
        holder_name = instructor.get("bank_account_holder_name") or f"{instructor['name']} {instructor.get('last_name', '')}".strip()
        holder_cpf_cnpj = instructor.get("bank_account_cpf_cnpj") or instructor.get("cpf")

        if not all([bank_code, agency_number, account_number]):
            raise ValidationError("Dados bancários do instrutor incompletos", 400)

        transfer_payload = {
            "value": float(amount),
            "bankAccount": {
                "bank": {"code": bank_code},
                "account": {
                    "accountNumber": account_number,
                    "accountDigit": account_digit,
                    "accountType": account_type
                },
                "agency": {"agencyNumber": agency_number},
                "holder": {
                    "name": holder_name,
                    "cpfCnpj": holder_cpf_cnpj
                }
            },
            "description": f"Repasse aula instrutor {instructor_id}",
        }

        asaas_response = self.asaas.create_transfer(transfer_payload, api_key=api_key)

        return {
            "success": True,
            "transfer_id": asaas_response.get("id"),
            "amount": float(amount),
            "status": "pending",
        }

    def get_balance(self, instructor_id: int) -> dict:
        """
        Consulta o saldo financeiro do instrutor combinando Asaas e Supabase.
        Retorna um payload rico para o dashboard do instrutor.
        """
        # 1. Busca instrutor
        instructor = self.supabase.fetch_one("instructor", {"id": instructor_id})
        if not instructor:
            raise NotFoundError("Instrutor não encontrado", 404)

        wallet_id = instructor.get("asaas_wallet_id")
        api_key = instructor.get("asaas_api_key")
        if not wallet_id or not api_key:
            raise ValidationError("Instrutor não possui subconta configurada", 400)

        # 2. Saldo disponível (fonte: Asaas)
        balance_data = self.asaas.get_finance_balance(api_key=api_key)
        available = float(balance_data.get("balance", 0.0))

        # 3. Valores a receber (aulas Paid aguardando liquidação)
        paid_lessons = self.supabase.fetch_all(
            "lesson",
            {"instructor_id": instructor_id, "payment_status": PaymentStatus.PAID.value}
        )
        to_receive = round(sum(float(lesson.get("total_price", 0.0)) * 0.9 for lesson in paid_lessons), 2)

        # 4. Estimativa (aulas Pending aguardando pagamento)
        pending_lessons = self.supabase.fetch_all(
            "lesson",
            {"instructor_id": instructor_id, "payment_status": PaymentStatus.PENDING.value}
        )
        estimated = round(sum(float(lesson.get("total_price", 0.0)) * 0.9 for lesson in pending_lessons), 2)

        # 5. Total histórico ganho (fonte: instructor_balance_transaction)
        transactions = self.supabase.fetch_all(
            "instructor_balance_transaction",
            {"instructor_id": instructor_id, "type": "LessonEarned"}
        )
        total_earned_history = round(sum(float(tx.get("amount", 0.0)) for tx in transactions), 2)

        return {
            "instructor_id": instructor_id,
            "wallet_id": wallet_id,
            "balances": {
                "available": available,
                "to_receive": to_receive,
                "estimated": estimated
            },
            "metrics": {
                "total_earned_history": total_earned_history
            }
        }