from app.core.config import Settings
from app.core.exceptions import MediaServiceError
from app.schemas.recorder import RecordingState
from app.services.camera_service import CameraService
from app.workers.process_manager import ProcessManager
from app.workers.recorder_worker import build_ffmpeg_command, recording_output_dir


class RecordingService:
    def __init__(
        self,
        settings: Settings,
        camera_service: CameraService | None = None,
        process_manager: ProcessManager | None = None,
    ) -> None:
        self.settings = settings
        self.camera_service = camera_service or CameraService(settings)
        self.process_manager = process_manager or ProcessManager(settings)

    async def start_recording(self, camera_id: str, bearer_token: str) -> RecordingState:
        if self.process_manager.active_count() >= self.settings.worker.max_recording_workers:
            raise MediaServiceError("Maximum recording worker limit reached", "MAX_RECORDING_WORKERS_REACHED", 429)

        camera = await self.camera_service.get_active_camera(camera_id, bearer_token)
        command = build_ffmpeg_command(self.settings, camera)
        output_dir = recording_output_dir(self.settings, camera.camera_id)
        state = RecordingState(
            camera_id=camera.camera_id,
            camera_name=camera.camera_name,
            pid=None,
            recording_status="recording",
            storage_path=str(output_dir),
        )
        return await self.process_manager.start_process(state, command)

    async def stop_recording(self, camera_id: str) -> dict:
        return await self.process_manager.stop_process(camera_id)

    async def get_status(self, camera_id: str) -> dict:
        state = self.process_manager.get_state(camera_id)
        if not state:
            return {
                "status": True,
                "cameraId": camera_id,
                "pid": None,
                "recordingStatus": "not_running",
                "restartCount": 0,
                "latestOutputFile": None,
                "lastError": None,
            }
        return state.to_response()

    async def list_recordings(self) -> dict:
        states = [state.to_response() for state in self.process_manager.list_states()]
        return {
            "status": True,
            "recorders": states,
            "count": len(states),
        }

    def active_count(self) -> int:
        return self.process_manager.active_count()

    async def shutdown(self) -> None:
        await self.process_manager.shutdown()
