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


if __name__ == "__main__":
    unittest.main()
