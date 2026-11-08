import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from test_instructor_finance import create_app
from config import Settings


API_DIR = os.path.dirname(os.path.dirname(__file__))


def configured_origins(override=None):
    env = os.environ.copy()
    env.pop("CORS_ALLOWED_ORIGINS", None)
    if override is not None:
        env["CORS_ALLOWED_ORIGINS"] = override
    code = (
        "import sys, types, json; "
        "sys.modules['dotenv'] = types.SimpleNamespace(load_dotenv=lambda: None); "
        "from config import Settings; print(json.dumps(Settings.CORS_ALLOWED_ORIGINS))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=API_DIR, env=env,
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


class CorsTest(unittest.TestCase):
    def test_default_origins_and_browser_preflight(self):
        origins = configured_origins()
        self.assertEqual(origins, [
            "http://localhost:5173", "http://localhost:3000",
            "https://instructor.bepilot.com.br",
        ])
        with patch.object(Settings, "CORS_ALLOWED_ORIGINS", origins):
            client = create_app().test_client()
            for origin in origins:
                with self.subTest(origin=origin):
                    response = client.options(
                        "/api/v1/instructors/11111111-1111-4111-8111-111111111111/balance",
                        headers={
                            "Origin": origin,
                            "Access-Control-Request-Method": "GET",
                            "Access-Control-Request-Headers": "authorization",
                        },
                    )
                    self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin)
                    self.assertIn("authorization", response.headers.get("Access-Control-Allow-Headers", "").lower())
                    response = client.get(
                        "/api/v1/instructors/11111111-1111-4111-8111-111111111111/balance",
                        headers={"Origin": origin},
                    )
                    self.assertEqual(response.status_code, 401)
                    self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin)
            response = client.get("/api/v1/health", headers={"Origin": "https://untrusted.example"})
            self.assertNotIn("Access-Control-Allow-Origin", response.headers)

    def test_environment_override_replaces_default(self):
        self.assertEqual(
            configured_origins(" https://custom.example/,http://localhost:3000 "),
            ["https://custom.example", "http://localhost:3000"],
        )


if __name__ == "__main__":
    unittest.main()
