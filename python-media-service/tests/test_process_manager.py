import asyncio
import unittest
from pathlib import Path

from app.core.config import load_settings
from app.core.exceptions import RecordingAlreadyRunningError
from app.schemas.recorder import RecordingState
from app.workers.process_manager import ProcessManager


class FakeProcess:
    def __init__(self, pid: int = 12345) -> None:
        self.pid = pid
        self.terminated = False
        self.killed = False
        self._done = asyncio.Event()

    def terminate(self) -> None:
        self.terminated = True
        self._done.set()

    def kill(self) -> None:
        self.killed = True
        self._done.set()

    async def wait(self) -> int:
        await self._done.wait()
        return 0


class FakeExitProcess:
    def __init__(self, return_code: int, pid: int = 12345) -> None:
        self.pid = pid
        self.return_code = return_code

    def terminate(self) -> None:
        return None

    def kill(self) -> None:
        return None

    async def wait(self) -> int:
        return self.return_code


def settings_for_test():
    settings = load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")
    settings.recording.stop_grace_seconds = 1
    settings.recording.restart_delay_seconds = 0
    return settings


def state_for_test() -> RecordingState:
    return RecordingState(
        camera_id="CAM-101",
        camera_name="Gantry Camera",
        pid=None,
        recording_status="recording",
        storage_path="storage/recordings/CAM-101/2026-07-09/10",
    )


class ProcessManagerTests(unittest.TestCase):
    def test_start_process_tracks_state(self) -> None:
        async def run() -> None:
            async def factory(*command: str) -> FakeProcess:
                return FakeProcess()

            manager = ProcessManager(settings_for_test(), process_factory=factory)
            state = await manager.start_process(state_for_test(), ["ffmpeg"])

            self.assertEqual(state.pid, 12345)
            self.assertEqual(manager.active_count(), 1)
            self.assertEqual(len(manager.list_states()), 1)
            await manager.shutdown()

        asyncio.run(run())

    def test_duplicate_start_is_blocked(self) -> None:
        async def run() -> None:
            async def factory(*command: str) -> FakeProcess:
                return FakeProcess()

            manager = ProcessManager(settings_for_test(), process_factory=factory)
            await manager.start_process(state_for_test(), ["ffmpeg"])

            with self.assertRaises(RecordingAlreadyRunningError):
                await manager.start_process(state_for_test(), ["ffmpeg"])
            await manager.shutdown()

        asyncio.run(run())

    def test_stop_process_marks_state_stopped(self) -> None:
        async def run() -> None:
            async def factory(*command: str) -> FakeProcess:
                return FakeProcess()

            manager = ProcessManager(settings_for_test(), process_factory=factory)
            await manager.start_process(state_for_test(), ["ffmpeg"])
            response = await manager.stop_process("CAM-101")

            self.assertEqual(response["recordingStatus"], "stopped")
            self.assertEqual(manager.active_count(), 0)

        asyncio.run(run())

    def test_failed_process_restarts_when_enabled(self) -> None:
        async def run() -> None:
            settings = settings_for_test()
            settings.recording.max_restart_attempts = 1
            processes = [FakeExitProcess(1, 111), FakeProcess(222)]

            async def factory(*command: str):
                return processes.pop(0)

            manager = ProcessManager(settings, process_factory=factory)
            await manager.start_process(state_for_test(), ["ffmpeg"])
            await asyncio.sleep(0.01)
            state = manager.get_state("CAM-101")

            self.assertIsNotNone(state)
            self.assertEqual(state.restart_count, 1)
            self.assertEqual(state.pid, 222)
            await manager.shutdown()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
