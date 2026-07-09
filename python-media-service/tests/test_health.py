import unittest

from fastapi.testclient import TestClient

from app.main import create_app


class HealthTests(unittest.TestCase):
    def test_detailed_health_includes_dependency_and_storage_status(self) -> None:
        response = TestClient(create_app()).get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("storageFreePercent", payload)
        self.assertIn("mediamtx", payload)
        self.assertIn("reachable", payload["mediamtx"])
        self.assertIn("javaApi", payload)
        self.assertIn("reachable", payload["javaApi"])


if __name__ == "__main__":
    unittest.main()
