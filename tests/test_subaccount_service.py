import unittest
from unittest.mock import patch

from errors import IntegrationError
from repositories.asaas_repository import AsaasRepository
from repositories.supabase_repository import SupabaseRepository
from services.subaccount_service import SubaccountService


class SubaccountServiceTests(unittest.TestCase):
    def setUp(self):
        self.instructor = {
            "id": 17,
            "name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.test",
            "cnpj": "12345678901234",
            "phone": "5511999999999",
            "birth_date": "1988-12-10",
            "incomeValue": 4000,
            "asaas_wallet_id": None,
        }
        self.address = {
            "street": "Rua Um",
            "number": "42",
            "complement": "Sala 5",
            "province": "Centro",
            "zip_code": "01001-000",
            "city": "Sao Paulo",
            "state": "SP",
        }

    def _fetch_one(self, table, query):
        if table == "instructor":
            return self.instructor
        if table == "address":
            return self.address
        self.fail(f"Consulta inesperada: {table}")

    def test_persists_wallet_id_and_preserves_original_payload_data(self):
        asaas_response = {
            "id": "subaccount-id-123",
            "walletId": "wallet-id-456",
            "accessToken": {"apiKey": "test-api-key"},
        }
        expected_payload = {
            "name": "Ada Lovelace",
            "email": "ada@example.test",
            "cpfCnpj": "12345678901234",
            "phone": "5511999999999",
            "mobilePhone": "5511999999999",
            "companyType": "MEI",
            "birthDate": "1988-12-10",
            "incomeValue": 4000,
            "address": "Rua Um",
            "addressNumber": "42",
            "complement": "Sala 5",
            "province": "Centro",
            "postalCode": "01001-000",
            "city": "Sao Paulo",
            "state": "SP",
        }

        with (
            patch.object(SupabaseRepository, "fetch_one", side_effect=self._fetch_one),
            patch.object(AsaasRepository, "create_subaccount", return_value=asaas_response) as create,
            patch.object(SupabaseRepository, "update", return_value={"id": 17}) as update,
        ):
            result = SubaccountService().create_subaccount(17)

        self.assertEqual(create.call_args.args[0], expected_payload)
        update.assert_called_once_with(
            "instructor",
            {"id": 17},
            {"asaas_wallet_id": "wallet-id-456", "asaas_api_key": "test-api-key"},
        )
        self.assertEqual(result, {"wallet_id": "wallet-id-456", "api_key": "test-api-key"})

    def test_accepts_legacy_top_level_api_key(self):
        with (
            patch.object(SupabaseRepository, "fetch_one", side_effect=self._fetch_one),
            patch.object(
                AsaasRepository,
                "create_subaccount",
                return_value={"id": "subaccount-id-123", "walletId": "wallet-id-456", "apiKey": "legacy-key"},
            ),
            patch.object(SupabaseRepository, "update", return_value={"id": 17}) as update,
        ):
            result = SubaccountService().create_subaccount(17)

        self.assertEqual(result["wallet_id"], "wallet-id-456")
        update.assert_called_once_with(
            "instructor",
            {"id": 17},
            {"asaas_wallet_id": "wallet-id-456", "asaas_api_key": "legacy-key"},
        )

    def test_does_not_persist_account_id_when_wallet_id_is_missing(self):
        with (
            patch.object(SupabaseRepository, "fetch_one", side_effect=self._fetch_one),
            patch.object(
                AsaasRepository,
                "create_subaccount",
                return_value={"id": "subaccount-id-123", "apiKey": "test-api-key"},
            ),
            patch.object(SupabaseRepository, "update") as update,
        ):
            with self.assertRaises(IntegrationError):
                SubaccountService().create_subaccount(17)

        update.assert_not_called()

    def test_does_not_persist_when_api_key_is_missing(self):
        with (
            patch.object(SupabaseRepository, "fetch_one", side_effect=self._fetch_one),
            patch.object(
                AsaasRepository,
                "create_subaccount",
                return_value={"id": "subaccount-id-123", "walletId": "wallet-id-456"},
            ),
            patch.object(SupabaseRepository, "update") as update,
        ):
            with self.assertRaises(IntegrationError):
                SubaccountService().create_subaccount(17)

        update.assert_not_called()


if __name__ == "__main__":
    unittest.main()