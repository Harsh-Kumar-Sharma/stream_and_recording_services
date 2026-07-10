class MediaServiceError(Exception):
    def __init__(self, message: str, error_code: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


class AuthTokenInvalidError(MediaServiceError):
    def __init__(self, message: str = "Invalid or expired session") -> None:
        super().__init__(message, "AUTH_TOKEN_INVALID", 401)


class AuthServiceUnavailableError(MediaServiceError):
    def __init__(self, message: str = "Authentication service unavailable") -> None:
        super().__init__(message, "AUTH_SERVICE_UNAVAILABLE", 503)


class JavaApiError(MediaServiceError):
    def __init__(self, message: str = "Java API request failed", status_code: int = 502) -> None:
        super().__init__(message, "JAVA_API_ERROR", status_code)


class CameraNotFoundError(MediaServiceError):
    def __init__(self, message: str = "Camera not found") -> None:
        super().__init__(message, "CAMERA_NOT_FOUND", 404)


class CameraInactiveError(MediaServiceError):
    def __init__(self, message: str = "Camera is inactive") -> None:
        super().__init__(message, "CAMERA_INACTIVE", 409)


class MediaMtxError(MediaServiceError):
    def __init__(self, message: str = "MediaMTX operation failed") -> None:
        super().__init__(message, "MEDIAMTX_ERROR", 502)


class RecordingAlreadyRunningError(MediaServiceError):
    def __init__(self, message: str = "Recording is already running") -> None:
        super().__init__(message, "RECORDING_ALREADY_RUNNING", 409)


class RecordingDisabledError(MediaServiceError):
    def __init__(self, message: str = "Recording service is disabled") -> None:
        super().__init__(message, "RECORDING_DISABLED", 503)


class RecordingNotRunningError(MediaServiceError):
    def __init__(self, message: str = "Recording is not running") -> None:
        super().__init__(message, "RECORDING_NOT_RUNNING", 404)


class FfmpegStartError(MediaServiceError):
    def __init__(self, message: str = "FFmpeg process failed to start") -> None:
        super().__init__(message, "FFMPEG_START_FAILED", 500)


class PlaybackFileNotFoundError(MediaServiceError):
    def __init__(self, message: str = "Playback file not found") -> None:
        super().__init__(message, "PLAYBACK_FILE_NOT_FOUND", 404)


class InvalidFilePathError(MediaServiceError):
    def __init__(self, message: str = "Invalid file path") -> None:
        super().__init__(message, "INVALID_FILE_PATH", 400)


class StorageNotAvailableError(MediaServiceError):
    def __init__(self, message: str = "Storage is not available") -> None:
        super().__init__(message, "STORAGE_NOT_AVAILABLE", 507)
