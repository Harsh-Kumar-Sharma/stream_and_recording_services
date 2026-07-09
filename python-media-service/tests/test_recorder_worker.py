import unittest
from datetime import datetime
from pathlib import Path

from app.core.config import load_settings
from app.schemas.stream import InternalCamera
from app.workers.recorder_worker import build_ffmpeg_command, recording_output_dir


def settings_for_test():
    return load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")


class RecorderWorkerTests(unittest.TestCase):
    def test_build_ffmpeg_command_uses_configured_pattern(self) -> None:
        settings = settings_for_test()
        camera = InternalCamera(
            camera_id="CAM-101",
            camera_name="Gantry Camera",
            rtsp_url="rtsp://user:secret@192.168.1.10:554/stream1",
            ip_address="192.168.1.10",
            status="active",
        )

        command = build_ffmpeg_command(settings, camera, datetime(2026, 7, 9, 10, 0, 0))

        self.assertEqual(command[0], settings.recording.ffmpeg_path)
        self.assertIn("-rtsp_transport", command)
        self.assertIn("tcp", command)
        self.assertIn("-c:v", command)
        self.assertIn("copy", command)
        self.assertIn("-f", command)
        self.assertIn("segment", command)
        self.assertIn("-segment_time", command)
        self.assertIn("900", command)
        self.assertIn("-strftime", command)
        self.assertTrue(command[-1].endswith("CAM-101_%Y%m%d_%H%M%S.mp4"))
        self.assertIn("rtsp://user:secret@192.168.1.10:554/stream1", command)
        self.assertNotIn("secret", command[-1])

    def test_recording_output_dir_is_camera_date_hour_based(self) -> None:
        output_dir = recording_output_dir(settings_for_test(), "CAM-101", datetime(2026, 7, 9, 10, 0, 0))

        self.assertTrue(str(output_dir).endswith("storage\\recordings\\CAM-101\\2026-07-09\\10") or str(output_dir).endswith("storage/recordings/CAM-101/2026-07-09/10"))


if __name__ == "__main__":
    unittest.main()
