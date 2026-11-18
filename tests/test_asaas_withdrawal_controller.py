import unittest
from unittest.mock import patch

from flask import Flask

from config import Settings
from controllers.asaas_withdrawal_controller import AsaasWithdrawalController


class AsaasWithdrawalControllerTests(unittest.TestCase):
    def setUp(self):
        self.controller = AsaasWithdrawalController()
        app = Flask(__name__)
        app.register_blueprint(self.controller.blueprint, url_prefix="/api/v1")
        self.client = app.test_client()
        self.token = "test-webhook-secret-not-for-production-123"

    def test_denies_requests_when_not_configured(self):
        with patch.object(Settings, "ASAAS_WITHDRAWAL_WEBHOOK_TOKEN", ""):
            response = self.client.post("/api/v1/asaas/withdrawal-validation", json={})
        self.assertEqual(response.status_code, 503)

    def test_denies_invalid_token_without_calling_service(self):
        with (
            patch.object(Settings, "ASAAS_WITHDRAWAL_WEBHOOK_TOKEN", self.token),
            patch.object(self.controller.service, "is_authorized") as authorize,
        ):
            response = self.client.post(
                "/api/v1/asaas/withdrawal-validation", json={}, headers={"asaas-access-token": "wrong"}
            )
        self.assertEqual(response.status_code, 401)
        authorize.assert_not_called()

    def test_approves_only_validated_event(self):
        event = {"type": "PAYMENT_SPLIT"}
        with (
            patch.object(Settings, "ASAAS_WITHDRAWAL_WEBHOOK_TOKEN", self.token),
            patch.object(self.controller.service, "is_authorized", return_value=True) as authorize,
        ):
            response = self.client.post(
                "/api/v1/asaas/withdrawal-validation", json=event, headers={"asaas-access-token": self.token}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "APPROVED"})
        authorize.assert_called_once_with(event)

    def test_refuses_unrecognized_event(self):
        with (
            patch.object(Settings, "ASAAS_WITHDRAWAL_WEBHOOK_TOKEN", self.token),
            patch.object(self.controller.service, "is_authorized", return_value=False),
        ):
            response = self.client.post(
                "/api/v1/asaas/withdrawal-validation", json={}, headers={"asaas-access-token": self.token}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "REFUSED"})

    def test_dependency_failure_does_not_approve(self):
        with (
            patch.object(Settings, "ASAAS_WITHDRAWAL_WEBHOOK_TOKEN", self.token),
            patch.object(self.controller.service, "is_authorized", side_effect=RuntimeError("failure")),
        ):
            response = self.client.post(
                "/api/v1/asaas/withdrawal-validation", json={}, headers={"asaas-access-token": self.token}
            )
        self.assertEqual(response.status_code, 503)

    def test_full_split_validation_with_provider_and_database_mocks(self):
        event = {
            "type": "PAYMENT_SPLIT",
            "paymentSplit": {
                "id": "split-test", "status": "AWAITING_CREDIT", "payment": {"id": "pay-test"},
                "walletId": "wallet-test", "percentualValue": 85, "fixedValue": None, "totalValue": "86.17",
            },
        }
        provider_payment = {
            "id": "pay-test", "externalReference": "lesson_93", "status": "RECEIVED",
            "value": "105.00", "netValue": "101.38",
            "split": [{"id": "split-test", "walletId": "wallet-test", "status": "AWAITING_CREDIT", "percentualValue": 85, "fixedValue": None}],
        }
        with (
            patch.object(Settings, "ASAAS_WITHDRAWAL_WEBHOOK_TOKEN", self.token),
            patch.object(self.controller.service, "supabase") as supabase,
            patch.object(self.controller.service, "asaas") as asaas,
        ):
            supabase.fetch_all_service_role.return_value = [{"lesson_id": 93, "amount": "105.00"}]
            supabase.fetch_one_service_role.side_effect = [
                {"id": 93, "status": "Scheduled", "instructor_id": 17},
                {"asaas_wallet_id": "wallet-test"},
            ]
            asaas.get_payment.return_value = provider_payment
            response = self.client.post(
                "/api/v1/asaas/withdrawal-validation", json=event, headers={"asaas-access-token": self.token}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "APPROVED"})
        asaas.get_payment.assert_called_once_with("pay-test")

    def test_real_service_refuses_other_operations(self):
        with (
            patch.object(Settings, "ASAAS_WITHDRAWAL_WEBHOOK_TOKEN", self.token),
            patch.object(self.controller.service, "supabase") as supabase,
        ):
            response = self.client.post(
                "/api/v1/asaas/withdrawal-validation", json={"type": "TRANSFER"},
                headers={"asaas-access-token": self.token},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "REFUSED"})
        supabase.fetch_all_service_role.assert_not_called()


if __name__ == "__main__":
    unittest.main()