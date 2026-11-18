from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from repositories.supabase_repository import SupabaseRepository
from repositories.asaas_repository import AsaasRepository
from errors import ValidationError, NotFoundError, IntegrationError
from utils.validators import validate_required_fields
from utils.asaas_status import map_asaas_status_to_payment_status
from models.enums import PaymentStatus, LessonStatus
from services.payment_split import build_asaas_split

FINAL_LESSON_STATUSES = {
    LessonStatus.CANCELLED.value,
    LessonStatus.COMPLETED.value,
    LessonStatus.NO_SHOW.value,
    LessonStatus.IN_PROGRESS.value,
}

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

    def _get_current_iso(self) -> str:
        """Retorna timestamp atual em ISO 8601."""
        return datetime.now(timezone.utc).isoformat()

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

        if payment_method == "pix":
            pending_pix = self.supabase.fetch_all_service_role("payment", {
                "lesson_id": lesson_id,
                "status": PaymentStatus.PENDING.value,
                "method": "pix",
            })
            if len(pending_pix) > 1:
                raise ValidationError("Mais de uma cobrança PIX pendente; requer conciliação", 409)
            if pending_pix:
                return self._reuse_pending_pix(lesson_id, pending_pix[0])

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

        payment_payload["split"] = build_asaas_split(wallet_id)

        if payment_payload["billingType"] == "CREDIT_CARD":
            validate_required_fields(data, ["credit_card", "credit_card_holder_info"])
            payment_payload["creditCard"] = data["credit_card"]
            student_addresses = self.supabase.fetch_all("address", {
                "owner_id": lesson["student_id"],
                "owner_type": "Student",
            })
            student_address = max(
                student_addresses,
                key=lambda address: address.get("updated_at") or "",
                default=None,
            )
            postal_code = "".join(filter(str.isdigit, str((student_address or {}).get("zip_code") or "")))
            address_number = str((student_address or {}).get("number") or "").strip()
            if len(postal_code) != 8 or not address_number:
                raise ValidationError(
                    "Aluno não possui CEP e número de endereço válidos cadastrados para pagamento com cartão",
                    400,
                )

            phone = "".join(filter(str.isdigit, str(student.get("phone") or "")))
            if len(phone) < 10:
                raise ValidationError(
                    "Aluno não possui telefone com DDD válido cadastrado para pagamento com cartão",
                    400,
                )

            holder_info = dict(data["credit_card_holder_info"])
            holder_info["postalCode"] = postal_code
            holder_info["addressNumber"] = address_number
            holder_info["phone"] = phone
            holder_info.pop("mobilePhone", None)
            payment_payload["creditCardHolderInfo"] = holder_info
            payment_payload["remoteIp"] = data.get("remote_ip")

        # Cria a cobrança no Asaas
        try:
            asaas_response = self.asaas.create_payment(payment_payload)
        except IntegrationError as error:
            if payment_payload["billingType"] == "PIX" and error.status_code == 504:
                raise IntegrationError(
                    "Criação do PIX não confirmada; consulte a cobrança no Asaas antes de tentar novamente",
                    504,
                ) from error
            raise
        mapped_status = map_asaas_status_to_payment_status(asaas_response.get("status", "PENDING"))

        # Prepara dados iniciais do registro (sem QR code ainda)
        payment_record = {
            "lesson_id": lesson_id,
            "bepayhub_transaction_id": asaas_response["id"],
            "amount": lesson["total_price"],
            "status": mapped_status,
            "method": payment_method,
            "pix_qr_code": None,
            "pix_copy_paste": None,
            "invoice_url": asaas_response.get("invoiceUrl"),
            "paid_at": asaas_response.get("paidDate"),
            "created_at": self._get_current_iso(),
            "updated_at": self._get_current_iso(),
        }
        inserted = self.supabase.insert("payment", payment_record)

        # Atualiza status de pagamento (e da aula, se confirmado)
        self._apply_payment_status(lesson, mapped_status)

        # Prepara resposta base
        result = {
            "success": True,
            "payment_id": asaas_response["id"],
        }

        # Se for PIX, busca o QR Code e o Copia e Cola
        if payment_payload["billingType"] == "PIX":
            pix_data = self.asaas.get_pix_qr_code(asaas_response["id"])
            if not isinstance(pix_data, dict) or not pix_data.get("encodedImage") or not pix_data.get("payload"):
                raise IntegrationError("QR Code PIX indisponível para a cobrança existente", 502)
            encoded_image = pix_data.get("encodedImage")
            payload_text = pix_data.get("payload")

            # Determina o ID do registro inserido para atualização
            payment_db_id = None
            if inserted and "id" in inserted:
                payment_db_id = inserted["id"]
            else:
                # Se não retornou, busca pelo transaction_id
                existing = self.supabase.fetch_one(
                    "payment",
                    {"bepayhub_transaction_id": asaas_response["id"]}
                )
                if existing:
                    payment_db_id = existing["id"]

            if payment_db_id is not None:
                self.supabase.update(
                    "payment",
                    {"id": payment_db_id},
                    {
                        "pix_qr_code": encoded_image,
                        "pix_copy_paste": payload_text,
                        "updated_at": self._get_current_iso(),
                    }
                )

            result["pix_qr_code"] = encoded_image
            result["pix_copy_paste"] = payload_text

        return result

    def _reuse_pending_pix(self, lesson_id: int, payment: dict) -> dict:
        payment_id = payment.get("bepayhub_transaction_id")
        if not payment_id or not payment.get("id"):
            raise IntegrationError("Cobrança PIX pendente incompleta; requer conciliação", 409)

        provider_payment = self.asaas.get_payment(payment_id)
        if (
            not isinstance(provider_payment, dict)
            or provider_payment.get("id") != payment_id
            or provider_payment.get("externalReference") != f"lesson_{lesson_id}"
            or provider_payment.get("billingType") != "PIX"
            or provider_payment.get("status") != "PENDING"
        ):
            raise ValidationError("Cobrança PIX pendente divergente; requer conciliação", 409)

        pix_data = self.asaas.get_pix_qr_code(payment_id)
        if not isinstance(pix_data, dict) or not pix_data.get("encodedImage") or not pix_data.get("payload"):
            raise IntegrationError("QR Code PIX indisponível para a cobrança existente", 502)
        self.supabase.update("payment", {"id": payment["id"]}, {
            "pix_qr_code": pix_data["encodedImage"],
            "pix_copy_paste": pix_data["payload"],
            "updated_at": self._get_current_iso(),
        })
        return {
            "success": True,
            "payment_id": payment_id,
            "pix_qr_code": pix_data["encodedImage"],
            "pix_copy_paste": pix_data["payload"],
        }

    def _apply_payment_status(self, lesson: dict, payment_status: str) -> None:
        """Grava o payment_status da aula; pagamento confirmado agenda a aula automaticamente."""
        changes = {"payment_status": payment_status}
        if (
            payment_status == PaymentStatus.PAID.value
            and lesson.get("status") not in FINAL_LESSON_STATUSES
        ):
            changes["status"] = LessonStatus.SCHEDULED.value
        self.supabase.update("lesson", {"id": lesson["id"]}, changes)

    def request_refund(self, lesson_id: int) -> dict:
        lesson = self.supabase.fetch_one_service_role("lesson", {"id": lesson_id})
        if not lesson:
            raise NotFoundError("Aula não encontrada", 404)
        if lesson.get("status") != LessonStatus.CANCELLED.value:
            raise ValidationError("Somente aulas canceladas podem ser estornadas", 400)

        payments = self.supabase.fetch_all_service_role("payment", {"lesson_id": lesson_id})
        paid = [payment for payment in payments if payment.get("status") == PaymentStatus.PAID.value]
        if len(paid) != 1 or not paid[0].get("bepayhub_transaction_id"):
            raise ValidationError("A aula deve possuir exatamente um pagamento confirmado", 409)
        payment = paid[0]
        payment_id = payment["bepayhub_transaction_id"]
        provider_payment = self.asaas.get_payment(payment_id)
        eligible_statuses = {"PIX": ("RECEIVED",), "CREDIT_CARD": ("CONFIRMED", "RECEIVED")}
        if (
            not isinstance(provider_payment, dict)
            or provider_payment.get("id") != payment_id
            or provider_payment.get("externalReference") != f"lesson_{lesson_id}"
            or provider_payment.get("status") not in eligible_statuses.get(provider_payment.get("billingType"), ())
        ):
            raise ValidationError("Cobrança no Asaas não corresponde à aula paga; requer conciliação", 409)
        try:
            local_amount = Decimal(str(payment["amount"]))
            provider_amount = Decimal(str(provider_payment["value"]))
            if not local_amount.is_finite() or not provider_amount.is_finite() or local_amount <= 0 or local_amount != provider_amount:
                raise ValueError("Valores divergentes")
        except (KeyError, InvalidOperation, ValueError):
            raise ValidationError("Valor da cobrança diverge do pagamento; requer conciliação", 409)
        refunds = self.asaas.get_payment_refunds(payment_id)
        if not isinstance(refunds, dict) or not isinstance(refunds.get("data"), list):
            raise IntegrationError("Resposta inválida do Asaas ao consultar estornos", 502)
        if refunds["data"] or refunds.get("hasMore"):
            raise ValidationError("A cobrança já possui histórico de estorno; requer conciliação", 409)

        try:
            lock = self.supabase.insert("lesson_refund_requests", {
                "lesson_id": lesson_id,
                "payment_id": payment["id"],
            })
        except IntegrationError as error:
            if error.status_code == 409:
                raise ValidationError("Estorno já solicitado; consulte sua situação", 409) from error
            raise
        if not lock:
            raise IntegrationError("Não foi possível registrar a tentativa de estorno", 500)

        self.asaas.refund_payment(payment_id)
        return {"status": "pending"}

    def get_refund_status(self, lesson_id: int) -> dict:
        attempt = self.supabase.fetch_one_service_role("lesson_refund_requests", {"lesson_id": lesson_id})
        if not attempt:
            raise NotFoundError("Solicitação de estorno não encontrada", 404)
        payment = self.supabase.fetch_one_service_role("payment", {"id": attempt["payment_id"], "lesson_id": lesson_id})
        if not payment or not payment.get("bepayhub_transaction_id"):
            raise IntegrationError("Pagamento associado ao estorno não encontrado", 500)

        refunds = self.asaas.get_payment_refunds(payment["bepayhub_transaction_id"])
        if not isinstance(refunds, dict) or not isinstance(refunds.get("data"), list):
            raise IntegrationError("Resposta inválida do Asaas ao consultar estornos", 502)
        if refunds.get("hasMore"):
            return {"status": "manual_review"}
        entries = refunds["data"]
        if not entries:
            return {"status": "unknown"}
        if any(not isinstance(entry, dict) for entry in entries):
            raise IntegrationError("Resposta inválida do Asaas ao consultar estornos", 502)
        if any(entry.get("status") == "PENDING" for entry in entries):
            return {"status": "pending"}
        if any(entry.get("status") not in ("DONE", "CANCELLED") for entry in entries):
            return {"status": "manual_review"}

        try:
            amount = Decimal(str(payment["amount"]))
            values = [Decimal(str(entry["value"])) for entry in entries if entry.get("status") == "DONE"]
            if not amount.is_finite() or any(not value.is_finite() or value < 0 for value in values):
                raise ValueError("Valores não finitos ou negativos")
            refunded = sum(values, Decimal("0"))
        except (KeyError, InvalidOperation, ValueError):
            raise IntegrationError("Valores de estorno inválidos", 502)
        if amount > 0 and refunded == amount:
            if not self.supabase.update("payment", {"id": payment["id"]}, {"status": PaymentStatus.REFUNDED.value}):
                raise IntegrationError("Não foi possível atualizar o pagamento estornado", 500)
            if not self.supabase.update("lesson", {"id": lesson_id}, {"payment_status": PaymentStatus.REFUNDED.value}):
                raise IntegrationError("Não foi possível atualizar a aula estornada", 500)
            return {"status": "refunded"}
        return {"status": "manual_review"}

    def get_payment_status(self, lesson_id: int) -> str:
        """Retorna status de pagamento de uma aula, sincronizando com o Asaas enquanto pendente."""
        lesson = self.supabase.fetch_one("lesson", {"id": lesson_id})
        if not lesson:
            raise NotFoundError("Aula não encontrada", 404)

        if lesson["payment_status"] == PaymentStatus.PENDING.value:
            self._sync_with_asaas(lesson)
            lesson = self.supabase.fetch_one("lesson", {"id": lesson_id}) or lesson

        return lesson["payment_status"].lower()

    def _sync_with_asaas(self, lesson: dict) -> None:
        """Confirma no Asaas pagamentos PIX/cartão que ainda constam como pendentes (sem webhook)."""
        payment = self.supabase.fetch_one("payment", {"lesson_id": lesson["id"]})
        if not payment or not payment.get("bepayhub_transaction_id"):
            return
        try:
            asaas_payment = self.asaas.get_payment(payment["bepayhub_transaction_id"])
        except Exception:
            return  # mantém o status atual; nova tentativa no próximo polling

        mapped = map_asaas_status_to_payment_status(asaas_payment.get("status", "PENDING"))
        if mapped == PaymentStatus.PENDING.value:
            return
        self.supabase.update(
            "payment",
            {"id": payment["id"]},
            {
                "status": mapped,
                "paid_at": asaas_payment.get("paidDate") or asaas_payment.get("confirmedDate"),
                "updated_at": self._get_current_iso(),
            },
        )
        self._apply_payment_status(lesson, mapped)

    def _map_billing_type(self, method: str) -> str:
        mapping = {
            "pix": "PIX",
            "credit_card": "CREDIT_CARD",
            "debit_card": "DEBIT_CARD",
        }
        if method not in mapping:
            raise ValidationError("Método de pagamento inválido", 400)
        return mapping[method]