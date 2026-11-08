import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests

# Do not load a local .env when running these isolated tests.
original_dotenv = sys.modules.get("dotenv")
sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda: None)
try:
    from app import create_app
    from config import Settings
    from repositories.supabase_repository import SupabaseRepository
    from services.instructor_service import InstructorService
finally:
    if original_dotenv is None:
        del sys.modules["dotenv"]
    else:
        sys.modules["dotenv"] = original_dotenv


OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
BASE = f"/api/v1/instructors/{OWNER}"
ROUTES = [
    ("get", "/balance"),
    ("get", "/lessons/paid"),
    ("get", "/lessons/unpaid"),
    ("post", "/payout"),
    ("get", "/transactions"),
    ("get", "/payouts"),
]


def auth_response(status=200, user_id=OWNER):
    response = Mock(status_code=status)
    response.json.return_value = {"id": user_id}
    return response


class InstructorFinanceTest(unittest.TestCase):
    def setUp(self):
        self.settings = patch.multiple(
            Settings, SUPABASE_URL="https://supabase.example",
            SUPABASE_KEY="test-anon-key", SUPABASE_SERVICE_ROLE_KEY="test-service-key",
        )
        self.settings.start()
        self.addCleanup(self.settings.stop)
        app = create_app()
        app.testing = True
        self.client = app.test_client()

    def test_missing_and_malformed_authorization_on_all_routes(self):
        with patch("utils.instructor_auth.requests.get") as auth, \
             patch.object(InstructorService, "get_balance") as balance:
            for method, route in ROUTES:
                for headers in ({}, {"Authorization": "Basic not-a-token"}):
                    with self.subTest(method=method, route=route, headers=headers):
                        response = getattr(self.client, method)(BASE + route, headers=headers)
                        self.assertEqual(response.status_code, 401)
            auth.assert_not_called()
            balance.assert_not_called()

    def test_invalid_and_other_owner_on_all_routes(self):
        with patch("utils.instructor_auth.requests.get") as auth, \
             patch.object(SupabaseRepository, "fetch_all") as query, \
             patch.object(SupabaseRepository, "fetch_one") as lookup:
            for method, route in ROUTES:
                for auth_result, status in ((auth_response(401), 401), (auth_response(200, OTHER), 403)):
                    with self.subTest(method=method, route=route, status=status):
                        auth.return_value = auth_result
                        response = getattr(self.client, method)(
                            BASE + route, headers={"Authorization": "Bearer test-token"},
                            json={"amount": 1} if method == "post" else None,
                        )
                        self.assertEqual(response.status_code, status)
            query.assert_not_called()
            lookup.assert_not_called()
            auth.assert_called_with(
                "https://supabase.example/auth/v1/user",
                headers={"apikey": "test-anon-key", "Authorization": "Bearer test-token"},
                timeout=10,
            )

    def test_auth_failure_is_not_mistaken_for_invalid_token(self):
        with patch("utils.instructor_auth.requests.get") as auth:
            auth.side_effect = requests.Timeout()
            response = self.client.get(BASE + "/balance", headers={"Authorization": "Bearer test-token"})
            self.assertEqual(response.status_code, 504)
            auth.side_effect = None
            auth.return_value = auth_response(503)
            response = self.client.get(BASE + "/balance", headers={"Authorization": "Bearer test-token"})
            self.assertEqual(response.status_code, 502)
            auth.return_value = auth_response(200, "not-a-uuid")
            response = self.client.get(BASE + "/balance", headers={"Authorization": "Bearer test-token"})
            self.assertEqual(response.status_code, 502)

    def test_authorized_routes_and_existing_balance_shape(self):
        balance = {
            "instructor_id": OWNER, "wallet_id": "wallet",
            "balances": {"available": 3, "to_receive": 2, "estimated": 1},
            "metrics": {"total_earned_history": 4},
        }
        with patch("utils.instructor_auth.requests.get", return_value=auth_response()), \
             patch.object(InstructorService, "get_balance", return_value=balance) as get_balance, \
             patch.object(InstructorService, "get_lessons_by_payment_status", return_value=[]) as lessons, \
             patch.object(InstructorService, "create_payout", return_value={"success": True}) as payout:
            headers = {"Authorization": "Bearer test-token"}
            self.assertEqual(self.client.get(BASE + "/balance", headers=headers).get_json(), balance)
            get_balance.assert_called_once_with(OWNER)
            for route in ("/lessons/paid", "/lessons/unpaid"):
                self.assertEqual(self.client.get(BASE + route, headers=headers).get_json(), [])
            self.assertEqual(lessons.call_count, 2)
            response = self.client.post(BASE + "/payout", headers=headers, json={"amount": 1})
            self.assertEqual(response.status_code, 200)
            payout.assert_called_once_with(OWNER, {"amount": 1})

    def test_histories_select_filter_order_limit_and_return_arrays(self):
        cases = [
            ("/transactions", "instructor_balance_transaction", "id,type,description,amount,created_at",
             [{"id": 2, "type": "LessonEarned", "description": "a", "amount": 10, "created_at": "2026-02-01"},
              {"id": 1, "type": "LessonEarned", "description": "b", "amount": 5, "created_at": "2026-01-01"}]),
            ("/payouts", "instructor_payout", "id,amount,status,created_at",
             [{"id": 3, "amount": 3, "status": "pending", "created_at": "2026-02-01"}]),
        ]
        with patch("utils.instructor_auth.requests.get", return_value=auth_response()), \
             patch.object(SupabaseRepository, "_request") as query:
            for route, table, columns, rows in cases:
                with self.subTest(route=route):
                    query.return_value = rows
                    response = self.client.get(BASE + route, headers={"Authorization": "Bearer test-token"})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.get_json(), rows)
                    query.assert_called_with(
                        "GET", table, query={"instructor_id": OWNER}, use_service_role=True,
                        params={"select": columns, "order": "created_at.desc,id.desc", "limit": 100},
                    )
            query.return_value = []
            self.assertEqual(
                self.client.get(BASE + "/transactions", headers={"Authorization": "Bearer test-token"}).get_json(),
                [],
            )

    def test_authorized_balance_uses_uuid_for_all_queries(self):
        instructor = {"asaas_wallet_id": "wallet", "asaas_api_key": "test-key"}
        with patch("utils.instructor_auth.requests.get", return_value=auth_response()), \
             patch.object(SupabaseRepository, "fetch_one", return_value=instructor) as lookup, \
             patch.object(SupabaseRepository, "fetch_all", side_effect=[
                 [{"total_price": 100}], [{"total_price": 50}], [{"amount": 90}],
             ]) as query, \
             patch("repositories.asaas_repository.AsaasRepository.get_finance_balance",
                   return_value={"balance": 12}):
            response = self.client.get(BASE + "/balance", headers={"Authorization": "Bearer test-token"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), {
                "instructor_id": OWNER, "wallet_id": "wallet",
                "balances": {"available": 12, "to_receive": 90, "estimated": 45},
                "metrics": {"total_earned_history": 90},
            })
            lookup.assert_called_once_with("instructor", {"id": OWNER})
            self.assertEqual(query.call_count, 3)
            for call in query.call_args_list:
                self.assertEqual(call.args[1]["instructor_id"], OWNER)

    def test_repository_forwards_postgrest_query_parameters(self):
        response = Mock(status_code=200, content=b"[]")
        response.json.return_value = []
        with patch("repositories.supabase_repository.requests.request", return_value=response) as http:
            SupabaseRepository.fetch_all(
                "instructor_payout", {"instructor_id": OWNER}, select="id,amount,status,created_at",
                order="created_at.desc,id.desc", limit=100, use_service_role=True,
            )
            call = http.call_args.kwargs
            self.assertEqual(call["url"], f"https://supabase.example/rest/v1/instructor_payout?instructor_id=eq.{OWNER}")
            self.assertEqual(call["params"], {
                "select": "id,amount,status,created_at", "order": "created_at.desc,id.desc", "limit": 100,
            })
            self.assertEqual(call["headers"]["apikey"], "test-service-key")

    def test_invalid_payouts_are_rejected_before_provider_or_lookup(self):
        with patch("utils.instructor_auth.requests.get", return_value=auth_response()), \
             patch.object(SupabaseRepository, "fetch_one") as lookup, \
             patch("repositories.asaas_repository.AsaasRepository.create_transfer") as transfer:
            for amount in (0, -1, True, "1", [], {}, float("inf"), float("nan"), 10 ** 400):
                with self.subTest(amount=str(amount)):
                    response = self.client.post(
                        BASE + "/payout", headers={"Authorization": "Bearer test-token"},
                        json={"amount": amount},
                    )
                    self.assertEqual(response.status_code, 400)
            lookup.assert_not_called()
            transfer.assert_not_called()

    def test_positive_payout_reaches_provider(self):
        instructor = {
            "asaas_wallet_id": "wallet", "asaas_api_key": "test-key", "bank_code": "1",
            "agency_number": "2", "account_number": "3", "name": "Name",
        }
        with patch.object(SupabaseRepository, "fetch_one", return_value=instructor), \
             patch("repositories.asaas_repository.AsaasRepository.create_transfer", return_value={"id": "transfer"}) as transfer:
            result = InstructorService().create_payout(OWNER, {"amount": 0.01})
            self.assertEqual(result["amount"], 0.01)
            self.assertEqual(transfer.call_args.args[0]["value"], 0.01)


if __name__ == "__main__":
    unittest.main()
