import unittest
from unittest.mock import Mock, patch

from errors import ValidationError
from repositories.asaas_repository import AsaasRepository
from repositories.supabase_repository import SupabaseRepository
from services.payment_service import PaymentService


class PaymentCardAddressTests(unittest.TestCase):
    def setUp(self):
        self.lesson = {
            "id": 12,
            "student_id": 21,
            "instructor_id": 32,
            "payment_status": "Pending",
            "total_price": 100,
        }
        self.student = {"id": 21, "bepayhub_customer_id": "customer-test", "phone": "(11) 98888-7777"}
        self.instructor = {"asaas_wallet_id": "wallet-test"}
        self.card_data = {
            "payment_method": "credit_card",
            "credit_card": {"number": "4111111111111111"},
            "credit_card_holder_info": {
                "name": "Teste",
                "email": "student@example.test",
                "cpfCnpj": "12345678901",
                "phone": "5511999999999",
                "mobilePhone": "5511999999999",
                "postalCode": "99999999",
                "addressNumber": "999",
            },
        }

    def _run_payment(self, addresses):
        service = PaymentService()
        service._apply_payment_status = Mock()
        with (
            patch.object(
                SupabaseRepository,
                "fetch_one",
                side_effect=[self.lesson, self.student, self.instructor],
            ),
            patch.object(SupabaseRepository, "fetch_all", return_value=addresses) as fetch_all,
            patch.object(SupabaseRepository, "insert", return_value={"id": 55}),
            patch.object(
                AsaasRepository,
                "create_payment",
                return_value={"id": "payment-test", "status": "PENDING"},
            ) as create_payment,
        ):
            result = service.pay_lesson(self.lesson["id"], self.card_data)
        return result, fetch_all, create_payment

    def test_uses_student_address_but_keeps_cardholder_cpf(self):
        result, fetch_all, create_payment = self._run_payment([
            {"zip_code": "11111-111", "number": "10", "updated_at": "2025-01-01T00:00:00Z"},
            {"zip_code": "01234-567", "number": "42B", "updated_at": "2025-02-01T00:00:00Z"},
        ])

        self.assertTrue(result["success"])
        fetch_all.assert_called_once_with(
            "address",
            {"owner_id": 21, "owner_type": "Student"},
        )
        holder = create_payment.call_args.args[0]["creditCardHolderInfo"]
        self.assertEqual(holder["postalCode"], "01234567")
        self.assertEqual(holder["addressNumber"], "42B")
        self.assertEqual(holder["cpfCnpj"], "12345678901")
        self.assertEqual(holder["phone"], "11988887777")
        self.assertNotIn("mobilePhone", holder)
        self.assertEqual(self.card_data["credit_card_holder_info"]["postalCode"], "99999999")
        self.assertEqual(self.card_data["credit_card_holder_info"]["phone"], "5511999999999")

    def test_rejects_card_payment_without_valid_saved_address(self):
        service = PaymentService()
        with (
            patch.object(
                SupabaseRepository,
                "fetch_one",
                side_effect=[self.lesson, self.student, self.instructor],
            ),
            patch.object(SupabaseRepository, "fetch_all", return_value=[{"zip_code": "123", "number": ""}]),
            patch.object(AsaasRepository, "create_payment") as create_payment,
        ):
            with self.assertRaises(ValidationError):
                service.pay_lesson(self.lesson["id"], self.card_data)

        create_payment.assert_not_called()

    def test_rejects_card_payment_without_valid_saved_phone(self):
        self.student["phone"] = None
        service = PaymentService()
        with (
            patch.object(
                SupabaseRepository,
                "fetch_one",
                side_effect=[self.lesson, self.student, self.instructor],
            ),
            patch.object(SupabaseRepository, "fetch_all", return_value=[{"zip_code": "01234-567", "number": "42"}]),
            patch.object(AsaasRepository, "create_payment") as create_payment,
        ):
            with self.assertRaisesRegex(ValidationError, "telefone"):
                service.pay_lesson(self.lesson["id"], self.card_data)

        create_payment.assert_not_called()


if __name__ == "__main__":
    unittest.main()