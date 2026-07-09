from pathlib import Path
import os
import unittest

from app.core.config import get_settings, load_settings


class ConfigTests(unittest.TestCase):
    def test_config_loads_required_sections(self) -> None:
        config_path = Path(__file__).resolve().parents[1] / "config" / "config.yaml"
        settings = load_settings(config_path)

        self.assertEqual(settings.app.name, "python-media-service")
        self.assertFalse(settings.database.enabled)
        self.assertEqual(settings.worker.max_recording_workers, 300)

    def test_env_override_parses_lists_and_booleans(self) -> None:
        os.environ["MEDIA_SERVICE__SECURITY__CORS_ALLOWED_ORIGINS"] = '["http://localhost:3000"]'
        os.environ["MEDIA_SERVICE__SECURITY__CORS_ALLOW_CREDENTIALS"] = "false"
        get_settings.cache_clear()
        try:
            config_path = Path(__file__).resolve().parents[1] / "config" / "config.yaml"
            settings = load_settings(config_path)

            self.assertEqual(settings.security.cors_allowed_origins, ["http://localhost:3000"])
            self.assertFalse(settings.security.cors_allow_credentials)
        finally:
            os.environ.pop("MEDIA_SERVICE__SECURITY__CORS_ALLOWED_ORIGINS", None)
            os.environ.pop("MEDIA_SERVICE__SECURITY__CORS_ALLOW_CREDENTIALS", None)
            get_settings.cache_clear()


if __name__ == "__main__":
    unittest.main()
