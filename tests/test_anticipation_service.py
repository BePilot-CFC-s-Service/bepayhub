import unittest
from unittest.mock import Mock

from errors import IntegrationError, ValidationError
from services.anticipation_service import AnticipationService


class AnticipationServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AnticipationService()
        self.service.supabase = Mock()
        self.service.asaas = Mock()
        self.service.supabase.fetch_one_service_role.return_value = {"id": 12, "status": "Scheduled"}
        self.service.supabase.fetch_all_service_role.return_value = [
            {"status": "Paid", "bepayhub_transaction_id": "pay-test"},
        ]
        self.service.asaas.get_payment.return_value = {
            "id": "pay-test", "externalReference": "lesson_12", "billingType": "CREDIT_CARD", "installment": None,
        }
        self.service.asaas.simulate_anticipation.return_value = {"isDocumentationRequired": False, "netValue": 90}

    def test_simulates_complete_installment_not_individual_payment(self):
        self.service.asaas.get_payment.return_value["installment"] = "installment-test"
        result = self.service.simulate_lesson(12)
        self.service.asaas.simulate_anticipation.assert_called_once_with({"installment": "installment-test"})
        self.assertEqual(result["scope"], "installment")

    def test_simulates_single_payment_when_not_installment(self):
        result = self.service.simulate_lesson(12)
        self.service.asaas.simulate_anticipation.assert_called_once_with({"payment": "pay-test"})
        self.assertEqual(result["scope"], "payment")

    def test_missing_subaccount_key_never_falls_back_to_parent(self):
        self.service.supabase.fetch_one_service_role.return_value = {"id": 32, "asaas_api_key": None}
        with self.assertRaises(ValidationError):
            self.service.get_configuration(32)
        self.service.asaas.get_anticipation_configuration.assert_not_called()

    def test_subaccount_configuration_uses_its_own_key(self):
        self.service.supabase.fetch_one_service_role.return_value = {"id": 32, "asaas_api_key": "subaccount-test-key"}
        self.service.asaas.get_anticipation_configuration.return_value = {"creditCardAutomaticEnabled": False}
        result = self.service.get_configuration(32)
        self.assertEqual(result, {"credit_card_automatic_enabled": False})
        self.service.asaas.get_anticipation_configuration.assert_called_once_with(api_key="subaccount-test-key")

    def test_malformed_configuration_is_not_treated_as_enabled(self):
        self.service.asaas.get_anticipation_configuration.return_value = {"creditCardAutomaticEnabled": "true"}
        with self.assertRaises(IntegrationError):
            self.service.get_configuration()

    def test_invalid_simulation_is_not_accepted(self):
        self.service.asaas.simulate_anticipation.return_value = {}
        with self.assertRaises(IntegrationError):
            self.service.simulate_lesson(12)

    def test_invalid_installment_does_not_fall_back_to_single_payment(self):
        self.service.asaas.get_payment.return_value["installment"] = " "
        with self.assertRaises(IntegrationError):
            self.service.simulate_lesson(12)
        self.service.asaas.simulate_anticipation.assert_not_called()

    def test_missing_installment_field_does_not_fall_back_to_single_payment(self):
        del self.service.asaas.get_payment.return_value["installment"]
        with self.assertRaises(IntegrationError):
            self.service.simulate_lesson(12)
        self.service.asaas.simulate_anticipation.assert_not_called()

    def test_sandbox_single_payment_with_null_installment_number_is_supported(self):
        payment = self.service.asaas.get_payment.return_value
        del payment["installment"]
        payment["installmentNumber"] = None
        result = self.service.simulate_lesson(12)
        self.assertEqual(result["scope"], "payment")
        self.service.asaas.simulate_anticipation.assert_called_once_with({"payment": "pay-test"})

    def test_installment_number_without_id_never_simulates_single_payment(self):
        payment = self.service.asaas.get_payment.return_value
        del payment["installment"]
        payment["installmentNumber"] = 2
        with self.assertRaises(IntegrationError):
            self.service.simulate_lesson(12)
        self.service.asaas.simulate_anticipation.assert_not_called()

    def test_simulation_omits_unexpected_provider_fields(self):
        self.service.asaas.simulate_anticipation.return_value["unexpected"] = "not exposed"
        result = self.service.simulate_lesson(12)
        self.assertNotIn("unexpected", result["simulation"])

    def test_cancelled_lesson_is_not_simulated(self):
        self.service.supabase.fetch_one_service_role.return_value = {"id": 12, "status": "Cancelled"}
        with self.assertRaises(ValidationError):
            self.service.simulate_lesson(12)
        self.service.asaas.simulate_anticipation.assert_not_called()


if __name__ == "__main__":
    unittest.main()