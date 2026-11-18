import unittest
from unittest.mock import patch

from flask import Flask

from config import Settings
from controllers.payment_controller import PaymentController


class RefundControllerTests(unittest.TestCase):
    def setUp(self):
        self.controller = PaymentController()
        app = Flask(__name__)
        app.register_blueprint(self.controller.blueprint, url_prefix="/api/v1")
        self.client = app.test_client()
        self.key = "test-refund-secret-not-for-production-123"

    def test_requires_configured_key(self):
        with patch.object(Settings, "REFUND_API_KEY", ""):
            response = self.client.post("/api/v1/lessons/12/refund")
        self.assertEqual(response.status_code, 503)

    def test_denies_missing_or_invalid_key_without_calling_service(self):
        with (
            patch.object(Settings, "REFUND_API_KEY", self.key),
            patch.object(self.controller.payment_service, "request_refund") as refund,
        ):
            for headers in ({}, {"Authorization": "Bearer wrong"}):
                response = self.client.post("/api/v1/lessons/12/refund", headers=headers)
                self.assertEqual(response.status_code, 401)
        refund.assert_not_called()

    def test_authorized_request_returns_accepted(self):
        with (
            patch.object(Settings, "REFUND_API_KEY", self.key),
            patch.object(self.controller.payment_service, "request_refund", return_value={"status": "pending"}) as refund,
        ):
            response = self.client.post(
                "/api/v1/lessons/12/refund", headers={"Authorization": f"Bearer {self.key}"}
            )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json(), {"status": "pending"})
        refund.assert_called_once_with(12)

    def test_authorized_status_query(self):
        with (
            patch.object(Settings, "REFUND_API_KEY", self.key),
            patch.object(self.controller.payment_service, "get_refund_status", return_value={"status": "refunded"}),
        ):
            response = self.client.get(
                "/api/v1/lessons/12/refund", headers={"Authorization": f"Bearer {self.key}"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "refunded"})

    def test_status_query_rejects_missing_key(self):
        with (
            patch.object(Settings, "REFUND_API_KEY", self.key),
            patch.object(self.controller.payment_service, "get_refund_status") as status,
        ):
            response = self.client.get("/api/v1/lessons/12/refund")
        self.assertEqual(response.status_code, 401)
        status.assert_not_called()


if __name__ == "__main__":
    unittest.main()