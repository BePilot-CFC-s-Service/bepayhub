from errors import IntegrationError, NotFoundError, ValidationError
from models.enums import LessonStatus, PaymentStatus
from repositories.asaas_repository import AsaasRepository
from repositories.supabase_repository import SupabaseRepository


class AnticipationService:
    def __init__(self):
        self.supabase = SupabaseRepository
        self.asaas = AsaasRepository

    def get_configuration(self, instructor_id=None):
        api_key = None
        if instructor_id is not None:
            instructor = self.supabase.fetch_one_service_role("instructor", {"id": instructor_id})
            if not instructor:
                raise NotFoundError("Instrutor não encontrado", 404)
            api_key = instructor.get("asaas_api_key")
            if not isinstance(api_key, str) or not api_key.strip():
                raise ValidationError("Instrutor não possui credencial Asaas cadastrada", 400)

        configuration = self.asaas.get_anticipation_configuration(api_key=api_key)
        if not isinstance(configuration, dict) or type(configuration.get("creditCardAutomaticEnabled")) is not bool:
            raise IntegrationError("Resposta inválida do Asaas para antecipação automática", 502)
        return {"credit_card_automatic_enabled": configuration["creditCardAutomaticEnabled"]}

    def simulate_lesson(self, lesson_id):
        lesson = self.supabase.fetch_one_service_role("lesson", {"id": lesson_id})
        if not lesson:
            raise NotFoundError("Aula não encontrada", 404)
        if lesson.get("status") in (LessonStatus.CANCELLED.value, LessonStatus.NO_SHOW.value):
            raise ValidationError("Aulas canceladas não podem ser antecipadas", 400)

        payments = self.supabase.fetch_all_service_role("payment", {"lesson_id": lesson_id})
        paid = [payment for payment in payments if payment.get("status") == PaymentStatus.PAID.value]
        if len(paid) != 1 or not paid[0].get("bepayhub_transaction_id"):
            raise ValidationError("A aula deve possuir exatamente um pagamento confirmado", 409)
        payment_id = paid[0]["bepayhub_transaction_id"]
        payment = self.asaas.get_payment(payment_id)
        if (
            not isinstance(payment, dict)
            or payment.get("id") != payment_id
            or payment.get("externalReference") != f"lesson_{lesson_id}"
            or payment.get("billingType") != "CREDIT_CARD"
        ):
            raise ValidationError("Cobrança no Asaas não corresponde à aula de cartão", 409)

        if "installment" not in payment and "installmentNumber" not in payment:
            raise IntegrationError("Informação de parcelamento ausente no Asaas", 502)
        installment = payment.get("installment")
        if installment is None and payment.get("installmentNumber") is not None:
            raise IntegrationError("Identificador de parcelamento ausente no Asaas", 502)
        if installment is not None and (not isinstance(installment, str) or not installment.strip()):
            raise IntegrationError("Identificador de parcelamento inválido no Asaas", 502)
        target = {"installment": installment} if installment else {"payment": payment_id}
        simulation = self.asaas.simulate_anticipation(target)
        if not isinstance(simulation, dict) or type(simulation.get("isDocumentationRequired")) is not bool:
            raise IntegrationError("Resposta inválida do Asaas para simulação", 502)
        allowed = (
            "installment", "payment", "anticipationDate", "dueDate", "fee",
            "anticipationDays", "netValue", "totalValue", "value", "isDocumentationRequired",
        )
        return {
            "scope": "installment" if installment else "payment",
            "simulation": {field: simulation[field] for field in allowed if field in simulation},
        }