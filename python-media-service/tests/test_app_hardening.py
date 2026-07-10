import unittest

from fastapi.testclient import TestClient

from app.main import create_app


class AppHardeningTests(unittest.TestCase):
    def test_cors_preflight_is_handled(self) -> None:
        response = TestClient(create_app()).options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access-control-allow-origin", response.headers)

    def test_protected_cors_preflight_skips_auth(self) -> None:
        response = TestClient(create_app()).options(
            "/api/v1/streams/9/status",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access-control-allow-origin", response.headers)
        self.assertIn("authorization", response.headers["access-control-allow-headers"].lower())


if __name__ == "__main__":
    unittest.main()
