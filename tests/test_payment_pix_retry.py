import unittest
from unittest.mock import Mock

from errors import IntegrationError, ValidationError
from services.payment_service import PaymentService


class PaymentPixRetryTests(unittest.TestCase):
    def setUp(self):
        self.service = PaymentService()
        self.service.supabase = Mock()
        self.service.asaas = Mock()
        self.service.supabase.fetch_one.return_value = {"id": 95, "payment_status": "Pending"}
        self.service.supabase.fetch_all_service_role.return_value = [
            {"id": 10, "bepayhub_transaction_id": "pay-test", "status": "Pending", "method": "pix"}
        ]
        self.service.asaas.get_payment.return_value = {
            "id": "pay-test", "externalReference": "lesson_95", "billingType": "PIX", "status": "PENDING",
        }
        self.service.asaas.get_pix_qr_code.return_value = {"encodedImage": "qr-test", "payload": "payload-test"}

    def test_reuses_pending_charge_without_creating_another(self):
        result = self.service.pay_lesson(95, {"payment_method": "pix"})
        self.assertEqual(result["payment_id"], "pay-test")
        self.assertEqual(result["pix_qr_code"], "qr-test")
        self.assertEqual(result["pix_copy_paste"], "payload-test")
        self.service.asaas.create_payment.assert_not_called()
        self.service.asaas.get_pix_qr_code.assert_called_once_with("pay-test")
        self.service.supabase.update.assert_called_once()

    def test_timeout_does_not_create_another_charge(self):
        self.service.asaas.get_pix_qr_code.side_effect = IntegrationError("timeout", 504)
        with self.assertRaises(IntegrationError):
            self.service.pay_lesson(95, {"payment_method": "pix"})
        self.service.asaas.create_payment.assert_not_called()

    def test_retry_after_qr_timeout_reuses_first_charge(self):
        lesson = {"id": 95, "student_id": 21, "instructor_id": 32, "payment_status": "Pending", "total_price": 105}
        records = {
            "lesson": lesson,
            "student": {"bepayhub_customer_id": "customer-test"},
            "instructor": {"asaas_wallet_id": "wallet-test"},
        }
        self.service.supabase.fetch_one.side_effect = lambda table, query: records.get(table)
        self.service.supabase.fetch_all_service_role.side_effect = [
            [],
            [{"id": 10, "bepayhub_transaction_id": "pay-test", "status": "Pending", "method": "pix"}],
        ]
        self.service.supabase.insert.return_value = {"id": 10}
        self.service.asaas.create_payment.return_value = {"id": "pay-test", "status": "PENDING"}
        self.service.asaas.get_pix_qr_code.side_effect = [
            IntegrationError("timeout", 504),
            {"encodedImage": "qr-test", "payload": "payload-test"},
        ]

        with self.assertRaises(IntegrationError):
            self.service.pay_lesson(95, {"payment_method": "pix"})
        result = self.service.pay_lesson(95, {"payment_method": "pix"})

        self.assertEqual(result["pix_copy_paste"], "payload-test")
        self.service.asaas.create_payment.assert_called_once()
        self.assertEqual(self.service.asaas.get_pix_qr_code.call_count, 2)

    def test_creation_timeout_warns_against_blind_retry(self):
        lesson = {"id": 95, "student_id": 21, "instructor_id": 32, "payment_status": "Pending", "total_price": 105}
        records = {
            "lesson": lesson,
            "student": {"bepayhub_customer_id": "customer-test"},
            "instructor": {"asaas_wallet_id": "wallet-test"},
        }
        self.service.supabase.fetch_one.side_effect = lambda table, query: records.get(table)
        self.service.supabase.fetch_all_service_role.return_value = []
        self.service.asaas.create_payment.side_effect = IntegrationError("timeout", 504)

        with self.assertRaisesRegex(IntegrationError, "consulte a cobrança no Asaas"):
            self.service.pay_lesson(95, {"payment_method": "pix"})

        self.service.asaas.create_payment.assert_called_once()
        self.service.asaas.get_pix_qr_code.assert_not_called()

    def test_multiple_pending_charges_require_reconciliation(self):
        self.service.supabase.fetch_all_service_role.return_value *= 2
        with self.assertRaises(ValidationError):
            self.service.pay_lesson(95, {"payment_method": "pix"})
        self.service.asaas.create_payment.assert_not_called()
        self.service.asaas.get_pix_qr_code.assert_not_called()

    def test_different_provider_reference_is_rejected(self):
        self.service.asaas.get_payment.return_value["externalReference"] = "lesson_96"
        with self.assertRaises(ValidationError):
            self.service.pay_lesson(95, {"payment_method": "pix"})
        self.service.asaas.create_payment.assert_not_called()

    def test_paid_provider_charge_is_not_recreated(self):
        self.service.asaas.get_payment.return_value["status"] = "RECEIVED"
        with self.assertRaises(ValidationError):
            self.service.pay_lesson(95, {"payment_method": "pix"})
        self.service.asaas.create_payment.assert_not_called()
        self.service.asaas.get_pix_qr_code.assert_not_called()

    def test_incomplete_qr_is_not_returned_as_success(self):
        self.service.asaas.get_pix_qr_code.return_value = {"encodedImage": "qr-test"}
        with self.assertRaises(IntegrationError):
            self.service.pay_lesson(95, {"payment_method": "pix"})
        self.service.asaas.create_payment.assert_not_called()
        self.service.supabase.update.assert_not_called()

    def test_missing_provider_id_does_not_create_new_charge(self):
        self.service.supabase.fetch_all_service_role.return_value[0]["bepayhub_transaction_id"] = None
        with self.assertRaises(IntegrationError):
            self.service.pay_lesson(95, {"payment_method": "pix"})
        self.service.asaas.create_payment.assert_not_called()


if __name__ == "__main__":
    unittest.main()