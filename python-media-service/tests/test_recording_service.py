import asyncio
import unittest
from pathlib import Path

from app.core.config import load_settings
from app.schemas.recorder import RecordingState
from app.schemas.stream import InternalCamera
from app.services.recording_service import RecordingService


class StubCameraService:
    async def get_active_camera(self, camera_id: str, bearer_token: str) -> InternalCamera:
        return InternalCamera(
            camera_id=camera_id,
            camera_name="Gantry Camera",
            rtsp_url="rtsp://user:secret@192.168.1.10:554/stream1",
            ip_address="192.168.1.10",
            status="active",
        )


class StubProcessManager:
    def __init__(self) -> None:
        self.command: list[str] | None = None
        self.state: RecordingState | None = None

    def active_count(self) -> int:
        return 0

    async def start_process(self, state: RecordingState, command: list[str]) -> RecordingState:
        self.command = command
        self.state = state
        state.pid = 12345
        return state

    async def stop_process(self, camera_id: str) -> dict:
        return {"status": True, "cameraId": camera_id, "recordingStatus": "stopped", "pid": None}

    def get_state(self, camera_id: str) -> RecordingState | None:
        return self.state if self.state and self.state.camera_id == camera_id else None

    def list_states(self) -> list[RecordingState]:
        return [self.state] if self.state else []

    async def shutdown(self) -> None:
        return None


def settings_for_test():
    return load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")


class RecordingServiceTests(unittest.TestCase):
    def test_start_recording_returns_pid_and_storage_path(self) -> None:
        manager = StubProcessManager()
        service = RecordingService(settings_for_test(), camera_service=StubCameraService(), process_manager=manager)

        state = asyncio.run(service.start_recording("CAM-101", "token"))
        response = state.to_response()

        self.assertEqual(response["pid"], 12345)
        self.assertEqual(response["recordingStatus"], "recording")
        self.assertIn("CAM-101", response["storagePath"])
        self.assertIsNotNone(manager.command)

    def test_status_returns_not_running_when_missing(self) -> None:
        service = RecordingService(settings_for_test(), camera_service=StubCameraService(), process_manager=StubProcessManager())

        response = asyncio.run(service.get_status("CAM-404"))

        self.assertEqual(response["recordingStatus"], "not_running")


if __name__ == "__main__":
    unittest.main()
