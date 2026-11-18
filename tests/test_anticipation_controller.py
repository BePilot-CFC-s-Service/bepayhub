import unittest
from unittest.mock import patch

from flask import Flask

from config import Settings
from controllers.payment_controller import PaymentController


class AnticipationControllerTests(unittest.TestCase):
    def setUp(self):
        self.controller = PaymentController()
        app = Flask(__name__)
        app.register_blueprint(self.controller.blueprint, url_prefix="/api/v1")
        self.client = app.test_client()
        self.key = "test-anticipation-secret-not-for-production-123"

    def test_requires_configured_key(self):
        with patch.object(Settings, "ANTICIPATION_API_KEY", ""):
            response = self.client.get("/api/v1/anticipations/configuration")
        self.assertEqual(response.status_code, 503)

    def test_rejects_unauthorized_simulation_without_calling_service(self):
        with (
            patch.object(Settings, "ANTICIPATION_API_KEY", self.key),
            patch.object(self.controller.anticipation_service, "simulate_lesson") as simulate,
        ):
            response = self.client.post("/api/v1/lessons/12/anticipations/simulate")
        self.assertEqual(response.status_code, 401)
        simulate.assert_not_called()

    def test_refund_key_does_not_authorize_anticipation(self):
        refund_key = "test-refund-secret-not-for-production-123"
        with (
            patch.object(Settings, "ANTICIPATION_API_KEY", self.key),
            patch.object(Settings, "REFUND_API_KEY", refund_key),
            patch.object(self.controller.anticipation_service, "get_configuration") as get_configuration,
        ):
            response = self.client.get(
                "/api/v1/anticipations/configuration", headers={"Authorization": f"Bearer {refund_key}"}
            )
        self.assertEqual(response.status_code, 401)
        get_configuration.assert_not_called()

    def test_authorized_main_configuration(self):
        with (
            patch.object(Settings, "ANTICIPATION_API_KEY", self.key),
            patch.object(self.controller.anticipation_service, "get_configuration", return_value={"credit_card_automatic_enabled": True}) as get_configuration,
        ):
            response = self.client.get(
                "/api/v1/anticipations/configuration", headers={"Authorization": f"Bearer {self.key}"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"credit_card_automatic_enabled": True})
        get_configuration.assert_called_once_with()

    def test_authorized_subaccount_configuration(self):
        with (
            patch.object(Settings, "ANTICIPATION_API_KEY", self.key),
            patch.object(self.controller.anticipation_service, "get_configuration", return_value={"credit_card_automatic_enabled": False}) as get_configuration,
        ):
            response = self.client.get(
                "/api/v1/instructors/32/anticipations/configuration", headers={"Authorization": f"Bearer {self.key}"}
            )
        self.assertEqual(response.status_code, 200)
        get_configuration.assert_called_once_with(32)

    def test_authorized_simulation_returns_provider_result(self):
        with (
            patch.object(Settings, "ANTICIPATION_API_KEY", self.key),
            patch.object(self.controller.anticipation_service, "simulate_lesson", return_value={"scope": "installment", "simulation": {"netValue": 90}}) as simulate,
        ):
            response = self.client.post(
                "/api/v1/lessons/12/anticipations/simulate", headers={"Authorization": f"Bearer {self.key}"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["scope"], "installment")
        simulate.assert_called_once_with(12)


if __name__ == "__main__":
    unittest.main()