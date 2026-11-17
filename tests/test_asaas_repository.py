import unittest
from unittest.mock import Mock, patch

from errors import IntegrationError
from repositories.asaas_repository import AsaasRepository


class AsaasRepositoryTests(unittest.TestCase):
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