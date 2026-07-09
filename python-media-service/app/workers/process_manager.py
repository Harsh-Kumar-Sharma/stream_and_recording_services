import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

from app.core.config import Settings
from app.core.exceptions import FfmpegStartError, RecordingAlreadyRunningError
from app.schemas.recorder import RecordingState

logger = logging.getLogger(__name__)


ProcessFactory = Callable[..., Awaitable]


async def default_process_factory(*command: str):
    return await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )


class ProcessManager:
    def __init__(self, settings: Settings, process_factory: ProcessFactory = default_process_factory) -> None:
        self.settings = settings
        self.process_factory = process_factory
        self._processes: dict[str, object] = {}
        self._states: dict[str, RecordingState] = {}
        self._commands: dict[str, list[str]] = {}
        self._lock = asyncio.Lock()

    async def start_process(self, state: RecordingState, command: list[str]) -> RecordingState:
        async with self._lock:
            existing = self._states.get(state.camera_id)
            if existing and existing.recording_status == "recording":
                raise RecordingAlreadyRunningError(f"Recording is already running for {state.camera_id}")

            try:
                process = await self.process_factory(*command)
            except OSError as exc:
                raise FfmpegStartError(str(exc)) from exc

            state.pid = getattr(process, "pid", None)
            self._processes[state.camera_id] = process
            self._states[state.camera_id] = state
            self._commands[state.camera_id] = command
            asyncio.create_task(self._monitor_process(state.camera_id))
            return state

    async def stop_process(self, camera_id: str) -> dict:
        async with self._lock:
            process = self._processes.pop(camera_id, None)
            state = self._states.get(camera_id)

        if process is not None:
            terminate = getattr(process, "terminate", None)
            if terminate:
                terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=self.settings.recording.stop_grace_seconds)
            except asyncio.TimeoutError:
                kill = getattr(process, "kill", None)
                if kill:
                    kill()
                await process.wait()

        if state:
            state.recording_status = "stopped"
            state.stopped_at = datetime.now(timezone.utc)
            state.pid = None
            return state.to_response()

        return {
            "status": True,
            "cameraId": camera_id,
            "recordingStatus": "not_running",
            "pid": None,
        }

    def get_state(self, camera_id: str) -> RecordingState | None:
        return self._states.get(camera_id)

    def list_states(self) -> list[RecordingState]:
        return list(self._states.values())

    def active_count(self) -> int:
        return sum(1 for state in self._states.values() if state.recording_status == "recording")

    async def shutdown(self) -> None:
        for camera_id in list(self._processes.keys()):
            await self.stop_process(camera_id)

    async def _monitor_process(self, camera_id: str) -> None:
        while True:
            process = self._processes.get(camera_id)
            state = self._states.get(camera_id)
            command = self._commands.get(camera_id)
            if process is None or state is None or command is None:
                return

            return_code = await process.wait()
            if self._processes.get(camera_id) is not process:
                return

            if return_code == 0:
                self._processes.pop(camera_id, None)
                state.recording_status = "stopped"
                state.pid = None
                return

            state.last_error = f"FFmpeg exited with code {return_code}"
            logger.error("Recording worker failed camera_id=%s return_code=%s", camera_id, return_code)

            if state.restart_count >= self.settings.recording.max_restart_attempts:
                self._processes.pop(camera_id, None)
                state.recording_status = "failed"
                state.pid = None
                return

            await asyncio.sleep(self.settings.recording.restart_delay_seconds)
            try:
                restarted = await self.process_factory(*command)
            except OSError as exc:
                self._processes.pop(camera_id, None)
                state.recording_status = "failed"
                state.pid = None
                state.last_error = str(exc)
                return

            state.restart_count += 1
            state.pid = getattr(restarted, "pid", None)
            state.recording_status = "recording"
            self._processes[camera_id] = restarted
