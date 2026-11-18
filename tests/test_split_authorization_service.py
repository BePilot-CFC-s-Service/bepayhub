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
                "payment": {"id": "pay-test"},
                "walletId": "wallet-test",
                "percentualValue": 85,
                "fixedValue": None,
                "totalValue": "86.17",
            },
        }
        self.service.supabase.fetch_all_service_role.return_value = [{"lesson_id": 93, "amount": "105.00"}]
        self.service.supabase.fetch_one_service_role.side_effect = [
            {"id": 93, "status": "Scheduled", "instructor_id": 17},
            {"asaas_wallet_id": "wallet-test"},
        ]
        self.service.asaas.get_payment.return_value = {
            "id": "pay-test",
            "externalReference": "lesson_93",
            "status": "RECEIVED",
            "value": "105.00",
            "netValue": "101.38",
            "split": [{"id": "split-test", "walletId": "wallet-test", "status": "AWAITING_CREDIT", "percentualValue": 85, "fixedValue": None}],
        }

    def test_approves_matching_payment_wallet_and_net_split(self):
        self.assertTrue(self.service.is_authorized(self.event))
        self.service.asaas.get_payment.assert_called_once_with("pay-test")

    def test_refuses_unrelated_operation_without_queries(self):
        self.event["type"] = "TRANSFER"
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


if __name__ == "__main__":
    unittest.main()