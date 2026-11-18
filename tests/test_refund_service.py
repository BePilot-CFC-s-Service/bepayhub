import unittest
from unittest.mock import Mock

from errors import IntegrationError, ValidationError
from services.payment_service import PaymentService


class RefundServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = PaymentService()
        self.service.supabase = Mock()
        self.service.asaas = Mock()
        self.lesson = {"id": 12, "status": "Cancelled", "payment_status": "Paid"}
        self.payment = {"id": 44, "lesson_id": 12, "status": "Paid", "amount": "100.00", "bepayhub_transaction_id": "pay-test"}
        self.service.supabase.fetch_one_service_role.return_value = self.lesson
        self.service.supabase.fetch_all_service_role.return_value = [self.payment]
        self.service.supabase.insert.return_value = {"lesson_id": 12, "payment_id": 44}
        self.service.asaas.get_payment.return_value = {
            "id": "pay-test", "externalReference": "lesson_12", "billingType": "PIX", "status": "RECEIVED", "value": 100,
        }
        self.service.asaas.get_payment_refunds.return_value = {"data": []}

    def test_requests_full_refund_only_after_unique_attempt_is_saved(self):
        result = self.service.request_refund(12)
        self.assertEqual(result, {"status": "pending"})
        self.service.supabase.insert.assert_called_once_with("lesson_refund_requests", {"lesson_id": 12, "payment_id": 44})
        self.service.asaas.refund_payment.assert_called_once_with("pay-test")
        self.service.supabase.update.assert_not_called()

    def test_duplicate_attempt_never_calls_refund(self):
        self.service.supabase.insert.side_effect = IntegrationError("duplicate", 409)
        with self.assertRaises(ValidationError):
            self.service.request_refund(12)
        self.service.asaas.refund_payment.assert_not_called()

    def test_existing_provider_refund_never_calls_refund(self):
        self.service.asaas.get_payment_refunds.return_value = {"data": [{"status": "PENDING"}]}
        with self.assertRaises(ValidationError):
            self.service.request_refund(12)
        self.service.supabase.insert.assert_not_called()
        self.service.asaas.refund_payment.assert_not_called()

    def test_uncancelled_lesson_never_calls_refund(self):
        self.lesson["status"] = "Scheduled"
        with self.assertRaises(ValidationError):
            self.service.request_refund(12)
        self.service.asaas.refund_payment.assert_not_called()

    def test_provider_payment_must_match_lesson_and_amount(self):
        for field, value in (("externalReference", "lesson_99"), ("status", "PENDING"), ("value", 99)):
            with self.subTest(field=field):
                provider_payment = dict(self.service.asaas.get_payment.return_value, **{field: value})
                self.service.asaas.get_payment.return_value = provider_payment
                with self.assertRaises(ValidationError):
                    self.service.request_refund(12)
                self.service.supabase.insert.assert_not_called()
                self.service.asaas.refund_payment.assert_not_called()
                self.service.asaas.get_payment.return_value = {
                    "id": "pay-test", "externalReference": "lesson_12", "billingType": "PIX", "status": "RECEIVED", "value": 100,
                }

    def test_confirmed_pix_and_other_payment_methods_are_rejected(self):
        for billing_type, status in (("PIX", "CONFIRMED"), ("BOLETO", "RECEIVED")):
            with self.subTest(billing_type=billing_type):
                self.service.asaas.get_payment.return_value.update({"billingType": billing_type, "status": status})
                with self.assertRaises(ValidationError):
                    self.service.request_refund(12)
                self.service.supabase.insert.assert_not_called()
                self.service.asaas.refund_payment.assert_not_called()

    def test_confirmed_card_can_be_refunded(self):
        self.service.asaas.get_payment.return_value.update({"billingType": "CREDIT_CARD", "status": "CONFIRMED"})
        self.assertEqual(self.service.request_refund(12), {"status": "pending"})
        self.service.asaas.refund_payment.assert_called_once_with("pay-test")

    def test_pending_refund_is_not_marked_refunded(self):
        self.service.supabase.fetch_one_service_role.side_effect = [{"payment_id": 44}, self.payment]
        self.service.asaas.get_payment_refunds.return_value = {"data": [{"status": "PENDING", "value": 100}]}
        self.assertEqual(self.service.get_refund_status(12), {"status": "pending"})
        self.service.supabase.update.assert_not_called()

    def test_full_done_refund_updates_payment_and_lesson(self):
        self.service.supabase.fetch_one_service_role.side_effect = [{"payment_id": 44}, self.payment]
        self.service.supabase.update.return_value = {"id": 1}
        self.service.asaas.get_payment_refunds.return_value = {"data": [{"status": "DONE", "value": 100}]}
        self.assertEqual(self.service.get_refund_status(12), {"status": "refunded"})
        self.assertEqual(self.service.supabase.update.call_count, 2)

    def test_partial_refund_requires_manual_review(self):
        self.service.supabase.fetch_one_service_role.side_effect = [{"payment_id": 44}, self.payment]
        self.service.asaas.get_payment_refunds.return_value = {"data": [{"status": "DONE", "value": 50}]}
        self.assertEqual(self.service.get_refund_status(12), {"status": "manual_review"})
        self.service.supabase.update.assert_not_called()

    def test_paginated_history_does_not_confirm_refund(self):
        self.service.supabase.fetch_one_service_role.side_effect = [{"payment_id": 44}, self.payment]
        self.service.asaas.get_payment_refunds.return_value = {"data": [{"status": "DONE", "value": 100}], "hasMore": True}
        self.assertEqual(self.service.get_refund_status(12), {"status": "manual_review"})
        self.service.supabase.update.assert_not_called()

    def test_provider_timeout_leaves_attempt_locked(self):
        self.service.asaas.refund_payment.side_effect = IntegrationError("timeout", 504)
        with self.assertRaises(IntegrationError):
            self.service.request_refund(12)
        self.service.supabase.insert.assert_called_once()
        self.service.asaas.refund_payment.assert_called_once_with("pay-test")
        self.service.supabase.delete.assert_not_called()

    def test_retry_after_timeout_does_not_send_another_refund(self):
        self.service.supabase.insert.side_effect = [
            {"lesson_id": 12, "payment_id": 44},
            IntegrationError("duplicate", 409),
        ]
        self.service.asaas.refund_payment.side_effect = IntegrationError("timeout", 504)

        with self.assertRaises(IntegrationError):
            self.service.request_refund(12)
        with self.assertRaises(ValidationError):
            self.service.request_refund(12)

        self.service.asaas.refund_payment.assert_called_once_with("pay-test")

    def test_ambiguous_multiple_paid_payments_are_rejected(self):
        self.service.supabase.fetch_all_service_role.return_value = [self.payment, dict(self.payment, id=45)]
        with self.assertRaises(ValidationError):
            self.service.request_refund(12)
        self.service.asaas.refund_payment.assert_not_called()


if __name__ == "__main__":
    unittest.main()