import unittest
from unittest.mock import Mock

from errors import IntegrationError
from services.split_authorization_service import SplitAuthorizationService


class SplitAuthorizationServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = SplitAuthorizationService()
        self.service.supabase = Mock()
        self.service.asaas = Mock()
        self.event = {
            "type": "PAYMENT_SPLIT",
            "paymentSplit": {
                "id": "split-test",
                "status": "AWAITING_CREDIT",
                "payment": {"id": "pay-test", "externalReference": "lesson_93"},
                "walletId": "wallet-test",
                "percentualValue": 85,
                "fixedValue": None,
                "totalValue": "87.55",
            },
        }
        self.service.supabase.fetch_all_service_role.return_value = [{
            "lesson_id": 93,
            "bepayhub_transaction_id": "pay-test",
            "amount": "105.00",
        }]
        self.service.supabase.fetch_one_service_role.side_effect = [
            {"id": 93, "status": "Scheduled", "instructor_id": 17},
            {"asaas_wallet_id": "wallet-test"},
        ]
        self.service.asaas.get_payment.return_value = {
            "id": "pay-test",
            "externalReference": "lesson_93",
            "status": "RECEIVED",
            "value": "105.00",
            "netValue": "103.01",
            "split": [{
                "id": "split-test",
                "walletId": "wallet-test",
                "status": "AWAITING_CREDIT",
                "percentualValue": 85,
                "fixedValue": None,
                "totalValue": "87.55",
            }],
        }

    def test_approves_matching_payment_wallet_and_net_split(self):
        self.assertTrue(self.service.is_authorized(self.event))
        self.service.asaas.get_payment.assert_called_once_with("pay-test")

    def test_approves_when_truncation_and_rounding_produce_same_cents(self):
        provider_payment = self.service.asaas.get_payment.return_value
        provider_payment["netValue"] = "101.38"
        provider_payment["split"][0]["totalValue"] = "86.17"
        self.event["paymentSplit"]["totalValue"] = "86.17"
        self.assertTrue(self.service.is_authorized(self.event))

    def test_refuses_split_rounded_up_even_when_provider_and_event_match(self):
        self.event["paymentSplit"]["totalValue"] = "87.56"
        self.service.asaas.get_payment.return_value["split"][0]["totalValue"] = "87.56"
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_split_one_cent_below_truncated_value(self):
        self.event["paymentSplit"]["totalValue"] = "87.54"
        self.service.asaas.get_payment.return_value["split"][0]["totalValue"] = "87.54"
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_split_with_fractional_cents(self):
        self.event["paymentSplit"]["totalValue"] = "87.5585"
        self.service.asaas.get_payment.return_value["split"][0]["totalValue"] = "87.5585"
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_notification_webhook_without_queries(self):
        self.assertFalse(self.service.is_authorized({
            "event": "PAYMENT_RECEIVED",
            "payment": self.service.asaas.get_payment.return_value,
        }))
        self.service.supabase.fetch_all_service_role.assert_not_called()
        self.service.asaas.get_payment.assert_not_called()

    def test_refuses_unrelated_operation_without_queries(self):
        self.event["type"] = "TRANSFER"
        self.assertFalse(self.service.is_authorized(self.event))
        self.service.supabase.fetch_all_service_role.assert_not_called()

    def test_refuses_non_awaiting_credit_status(self):
        self.event["paymentSplit"]["status"] = "CREDITED"
        self.assertFalse(self.service.is_authorized(self.event))
        self.service.supabase.fetch_all_service_role.assert_not_called()

    def test_missing_payment_is_retried_without_approval(self):
        self.service.supabase.fetch_all_service_role.return_value = []
        with self.assertRaises(IntegrationError):
            self.service.is_authorized(self.event)
        self.service.asaas.get_payment.assert_not_called()

    def test_refuses_different_instructor_wallet(self):
        self.service.supabase.fetch_one_service_role.side_effect = [
            {"id": 93, "status": "Scheduled", "instructor_id": 17},
            {"asaas_wallet_id": "different-wallet"},
        ]
        with self.assertLogs("services.split_authorization_service", level="WARNING") as captured:
            self.assertFalse(self.service.is_authorized(self.event))
        self.assertIn("carteira_divergente", captured.output[0])
        self.assertNotIn("wallet-test", captured.output[0])
        self.assertNotIn("pay-test", captured.output[0])

    def test_refuses_wrong_split_amount(self):
        self.event["paymentSplit"]["totalValue"] = "90.00"
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_provider_split_amount_different_from_event(self):
        self.service.asaas.get_payment.return_value["split"][0]["totalValue"] = "80.00"
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_changed_event_reference(self):
        self.event["paymentSplit"]["payment"]["externalReference"] = "lesson_99"
        self.assertFalse(self.service.is_authorized(self.event))
        self.service.asaas.get_payment.assert_not_called()

    def test_refuses_changed_local_payment_id(self):
        self.service.supabase.fetch_all_service_role.return_value[0]["bepayhub_transaction_id"] = "pay-other"
        self.assertFalse(self.service.is_authorized(self.event))
        self.service.asaas.get_payment.assert_not_called()

    def test_refuses_wrong_percentage(self):
        self.event["paymentSplit"]["percentualValue"] = 100
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_fixed_value(self):
        self.event["paymentSplit"]["fixedValue"] = 10
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_unknown_provider_split(self):
        self.service.asaas.get_payment.return_value["split"][0]["id"] = "other-split"
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_unconfirmed_provider_payment(self):
        self.service.asaas.get_payment.return_value["status"] = "PENDING"
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_split_cancelled_at_provider(self):
        self.service.asaas.get_payment.return_value["split"][0]["status"] = "CANCELLED"
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_changed_provider_reference(self):
        self.service.asaas.get_payment.return_value["externalReference"] = "lesson_99"
        self.assertFalse(self.service.is_authorized(self.event))

    def test_refuses_cancelled_lesson(self):
        self.service.supabase.fetch_one_service_role.side_effect = [
            {"id": 93, "status": "Cancelled", "instructor_id": 17},
        ]
        self.assertFalse(self.service.is_authorized(self.event))
        self.service.asaas.get_payment.assert_not_called()

    def test_refuses_no_show_lesson(self):
        self.service.supabase.fetch_one_service_role.side_effect = [
            {"id": 93, "status": "NoShow", "instructor_id": 17},
        ]
        self.assertFalse(self.service.is_authorized(self.event))
        self.service.asaas.get_payment.assert_not_called()

    def test_refuses_ambiguous_local_payments(self):
        self.service.supabase.fetch_all_service_role.return_value *= 2
        self.assertFalse(self.service.is_authorized(self.event))
        self.service.asaas.get_payment.assert_not_called()

    def test_supabase_failure_is_propagated_for_retry(self):
        self.service.supabase.fetch_all_service_role.side_effect = IntegrationError("indisponível", 503)
        with self.assertRaises(IntegrationError):
            self.service.is_authorized(self.event)

    def test_asaas_failure_is_propagated_for_retry(self):
        self.service.asaas.get_payment.side_effect = IntegrationError("indisponível", 502)
        with self.assertRaises(IntegrationError):
            self.service.is_authorized(self.event)

    def test_repeated_identical_event_has_consistent_decision(self):
        self.assertTrue(self.service.is_authorized(self.event))
        self.service.supabase.fetch_all_service_role.return_value = [{
            "lesson_id": 93,
            "bepayhub_transaction_id": "pay-test",
            "amount": "105.00",
        }]
        self.service.supabase.fetch_one_service_role.side_effect = [
            {"id": 93, "status": "Scheduled", "instructor_id": 17},
            {"asaas_wallet_id": "wallet-test"},
        ]
        self.assertTrue(self.service.is_authorized(self.event))


if __name__ == "__main__":
    unittest.main()