import unittest
from unittest.mock import Mock, patch

from errors import IntegrationError
from repositories.asaas_repository import AsaasRepository


class AsaasRepositoryTests(unittest.TestCase):
    def test_anticipation_configuration_uses_requested_account(self):
        with patch.object(AsaasRepository, "_request", return_value={"creditCardAutomaticEnabled": True}) as request:
            result = AsaasRepository.get_anticipation_configuration(api_key="subaccount-test-key")

        request.assert_called_once_with("GET", "/anticipations/configurations", api_key="subaccount-test-key")
        self.assertTrue(result["creditCardAutomaticEnabled"])

    def test_anticipation_simulation_uses_parent_account(self):
        with patch.object(AsaasRepository, "_request", return_value={"isDocumentationRequired": False}) as request:
            AsaasRepository.simulate_anticipation({"installment": "installment-test"})

        request.assert_called_once_with(
            "POST", "/anticipations/simulate", data={"installment": "installment-test"}
        )

    def test_refund_uses_provider_payment_id_and_empty_body(self):
        with patch.object(AsaasRepository, "_request", return_value={"status": "REFUND_REQUESTED"}) as request:
            result = AsaasRepository.refund_payment("pay-test")

        request.assert_called_once_with("POST", "/payments/pay-test/refund", data={})
        self.assertEqual(result["status"], "REFUND_REQUESTED")

    def test_refund_history_uses_provider_payment_id(self):
        with patch.object(AsaasRepository, "_request", return_value={"data": []}) as request:
            AsaasRepository.get_payment_refunds("pay-test")

        request.assert_called_once_with("GET", "/payments/pay-test/refunds")

    def test_non_json_error_does_not_log_response_body(self):
        response = Mock(status_code=502, text="sensitive-response-marker")
        response.json.side_effect = ValueError("not json")

        with (
            patch("repositories.asaas_repository.requests.request", return_value=response),
            self.assertLogs("repositories.asaas_repository", level="ERROR") as captured,
        ):
            with self.assertRaises(IntegrationError):
                AsaasRepository.create_subaccount({})

        self.assertIn("status 502", captured.output[0])
        self.assertNotIn("sensitive-response-marker", captured.output[0])


if __name__ == "__main__":
    unittest.main()