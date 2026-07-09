import unittest

from app.core.logging import mask_rtsp_url


class LoggingTests(unittest.TestCase):
    def test_mask_rtsp_url_hides_password(self) -> None:
        masked = mask_rtsp_url("rtsp://user:secret@192.168.1.10:554/stream1")

        self.assertEqual(masked, "rtsp://user:****@192.168.1.10:554/stream1")
        self.assertNotIn("secret", masked)


if __name__ == "__main__":
    unittest.main()
