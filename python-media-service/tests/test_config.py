from pathlib import Path
import unittest

from app.core.config import load_settings


class ConfigTests(unittest.TestCase):
    def test_config_loads_required_sections(self) -> None:
        config_path = Path(__file__).resolve().parents[1] / "config" / "config.yaml"
        settings = load_settings(config_path)

        self.assertEqual(settings.app.name, "python-media-service")
        self.assertFalse(settings.database.enabled)
        self.assertEqual(settings.worker.max_recording_workers, 300)


if __name__ == "__main__":
    unittest.main()
