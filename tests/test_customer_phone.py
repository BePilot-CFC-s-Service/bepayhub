import unittest
from unittest.mock import patch

from errors import ValidationError
from repositories.asaas_repository import AsaasRepository
from repositories.supabase_repository import SupabaseRepository
from services.customer_service import CustomerService


class CustomerPhoneTests(unittest.TestCase):
    def setUp(self):
        self.student = {
            "id": 21,
            "name": "Ana",
            "last_name": "Teste",
            "cpf": "12345678901",
            "email": "ana@example.test",
            "phone": "(21) 98400-0000",
        }

    def test_creates_customer_with_normalized_mobile_number(self):
        with (
            patch.object(SupabaseRepository, "fetch_one", side_effect=[self.student, None]),
            patch.object(AsaasRepository, "create_customer", return_value={"id": "customer-test"}) as create,
            patch.object(SupabaseRepository, "update") as update,
        ):
            result = CustomerService().create_customer({"user_type": "student", "user_id": 21})

        self.assertEqual(result, "customer-test")
        payload = create.call_args.args[0]
        self.assertEqual(payload["mobilePhone"], "21984000000")
        self.assertIsInstance(payload["mobilePhone"], str)
        self.assertNotIn("phone", payload)
        update.assert_called_once_with("student", {"id": 21}, {"bepayhub_customer_id": "customer-test"})
        self.assertEqual(self.student["phone"], "(21) 98400-0000")

    def test_rejects_invalid_phone_before_creating_customer(self):
        self.student["phone"] = "123"
        with (
            patch.object(SupabaseRepository, "fetch_one", return_value=self.student),
            patch.object(AsaasRepository, "create_customer") as create,
            patch.object(SupabaseRepository, "update") as update,
        ):
            with self.assertRaises(ValidationError):
                CustomerService().create_customer({"user_type": "student", "user_id": 21})

        create.assert_not_called()
        update.assert_not_called()

    def test_creates_customer_with_normalized_landline(self):
        self.student["phone"] = "(21) 3344-5566"
        with (
            patch.object(SupabaseRepository, "fetch_one", side_effect=[self.student, None]),
            patch.object(AsaasRepository, "create_customer", return_value={"id": "customer-test"}) as create,
            patch.object(SupabaseRepository, "update"),
        ):
            CustomerService().create_customer({"user_type": "student", "user_id": 21})

        self.assertEqual(create.call_args.args[0]["phone"], "2133445566")
        self.assertNotIn("mobilePhone", create.call_args.args[0])

    def test_preserves_unformatted_mobile_number_as_string(self):
        self.student["phone"] = "21984000000"
        with (
            patch.object(SupabaseRepository, "fetch_one", side_effect=[self.student, None]),
            patch.object(AsaasRepository, "create_customer", return_value={"id": "customer-test"}) as create,
            patch.object(SupabaseRepository, "update"),
        ):
            CustomerService().create_customer({"user_type": "student", "user_id": 21})

        self.assertEqual(create.call_args.args[0]["mobilePhone"], "21984000000")


if __name__ == "__main__":
    unittest.main()