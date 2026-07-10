# TRD: Technical Requirements Document for Python FastAPI Media Service

## 1. Technical Objective

Build a Python FastAPI backend that acts as a media-control service for camera live streaming, recording, and playback.

The service must:

- Accept frontend requests directly from React
- Validate bearer token through Java API server
- Get camera device/RTSP info from Java API server
- Use MediaMTX for live streaming
- Use FFmpeg for recording
- Store recordings as segmented `.mp4` files
- Use YAML configuration
- Avoid DB dependency in the current version
- Be designed for approximately 300 cameras

---

## 2. Architecture

```txt
React Frontend
   |
   | Authorization: Bearer <token>
   v
Python FastAPI Media Service
   |
   | Validate token/session
   v
Java API Server
   |
   | Valid/Invalid response
   v
Python FastAPI Media Service
   |
   | Get camera RTSP/device info
   v
Java API Server
   |
   | Camera data response
   v
Python FastAPI Media Service
   |
   | Live: MediaMTX
   | Recording: FFmpeg background workers
   v
MediaMTX / FFmpeg / Video Storage
```

---

## 3. Required Technologies

## 3.1 Backend Framework

```txt
Python >=3.11,<3.14
FastAPI
Uvicorn
Pydantic
PyYAML
HTTPX
```

Recommended packages:

```txt
fastapi
uvicorn[standard]
pydantic
pydantic-settings
PyYAML
httpx
python-multipart
aiofiles
psutil
```

Windows local setup must use Python 3.11, 3.12, or 3.13 for the current pinned dependency set. Python 3.14 can force native dependency builds, especially `pydantic-core`, and fail without Visual Studio C++ Build Tools. The repository includes `scripts/setup.ps1`, `scripts/check_python_version.py`, and `pyproject.toml` with `requires-python = ">=3.11,<3.14"` to make this constraint explicit before dependency installation.

Optional future packages:

```txt
SQLAlchemy
Alembic
Redis
Celery or RQ
APScheduler
```

---

## 3.2 Live Streaming

Use:

```txt
MediaMTX
```

Purpose:

- RTSP ingest
- HLS/WebRTC output
- Stream path management
- Live stream fanout

Camera input:

```txt
RTSP
```

Recommended frontend playback:

```txt
HLS using hls.js or video.js
```

Low-latency future option:

```txt
WebRTC through MediaMTX
```

---

## 3.3 Recording

Use:

```txt
FFmpeg
```

Purpose:

- Read RTSP camera stream
- Write segmented `.mp4` recordings
- Run as background worker process
- Support runtime on/off control through `recording.enabled` or `MEDIA_SERVICE__RECORDING__ENABLED`

Default recording mode:

```txt
-c:v copy
```

This avoids CPU-heavy re-encoding.

Recording disable behavior:

```txt
MEDIA_SERVICE__RECORDING__ENABLED=false
```

When disabled, `POST /api/v1/recorders/{camera_id}/start` must return `503` with error code `RECORDING_DISABLED`. Status, list, and stop endpoints remain available.

---

## 3.4 Storage

Current storage:

```txt
Local disk / mounted disk / NAS mount
```

Recording file format:

```txt
.mp4
```

Recommended folder structure:

```txt
/data/recordings/{camera_id}/{yyyy-mm-dd}/{hour}/{camera_id}_{yyyymmdd}_{hhmmss}.mp4
```

Example:

```txt
/data/recordings/CAM-101/2026-07-09/10/CAM-101_20260709_100000.mp4
```

---

## 3.5 Database

Current version:

```txt
No database dependency in Python service.
```

Future support should be kept in config:

```txt
database.enabled = false
```

Future database can store:

- Recording metadata
- Camera health logs
- Recording jobs
- Stream sessions
- FFmpeg process logs
- Storage usage logs

---

## 4. API Communication Requirements

## 4.1 Frontend to Python

Frontend will call Python directly for:

```txt
Live stream
Recording
Playback
Health/status
```

Frontend must send:

```txt
Authorization: Bearer <token>
```

---

## 4.2 Python to Java

Python will call Java for:

```txt
Token/session validation
Stream device information
```

Python will not directly manage users or camera master data.

---

## 5. Required Java APIs

## 5.1 Token Validation API

Endpoint:

```txt
GET /api/auth/session/validate
```

Headers:

```txt
Authorization: Bearer <token>
```

Expected valid response:

```json
{
  "valid": true,
  "userId": "USER-101",
  "username": "harsh",
  "roles": ["ADMIN"],
  "permissions": ["CAMERA_LIVE_VIEW", "CAMERA_PLAYBACK", "CAMERA_RECORDING"]
}
```

Expected invalid response:

```json
{
  "valid": false,
  "message": "Invalid or expired token"
}
```

---

## 5.2 Stream Devices API

Endpoint:

```txt
GET /api/devices/stream/all
```

Headers:

```txt
Authorization: Bearer <token>
```

Expected response:

```json
[
  {
    "deviceId": 2,
    "customDeviceId": "CAM-02\n",
    "ipAddress": "192.168.38\n",
    "username": "User1",
    "password": "PassWd",
    "portNumber": 765,
    "rtspUrl": "rtsp://192.168.2"
  }
]
```

Python selects the requested camera by trimmed `customDeviceId` or numeric `deviceId`. Java string values may include newline characters, so Python normalizes them before using camera ID, IP address, and RTSP URL values.

---

## 6. Python API Requirements

## 6.1 Health APIs

```txt
GET /health
GET /api/v1/health
```

Response example:

```json
{
  "status": true,
  "service": "python-media-service",
  "activeStreams": 10,
  "activeRecorders": 5,
  "storageFreePercent": 72
}
```

---

## 6.2 Stream APIs

```txt
POST /api/v1/streams/{camera_id}/start
POST /api/v1/streams/{camera_id}/stop
GET  /api/v1/streams/{camera_id}/status
GET  /api/v1/streams
```

Start stream response:

```json
{
  "status": true,
  "cameraId": "CAM-101",
  "streamStatus": "started",
  "streamType": "hls",
  "streamUrl": "http://localhost:8888/cam-CAM-101/index.m3u8"
}
```

---

## 6.3 Recorder APIs

```txt
POST /api/v1/recorders/{camera_id}/start
POST /api/v1/recorders/{camera_id}/stop
GET  /api/v1/recorders/{camera_id}/status
GET  /api/v1/recorders
```

Start recording response:

```json
{
  "status": true,
  "cameraId": "CAM-101",
  "recordingStatus": "started",
  "segmentDurationSeconds": 900,
  "storagePath": "/data/recordings/CAM-101/2026-07-09"
}
```

---

## 6.4 Playback APIs

```txt
GET /api/v1/playback/search?cameraId=CAM-101&from=2026-07-09T10:00:00&to=2026-07-09T11:00:00
GET /api/v1/playback/{camera_id}/files?date=2026-07-09
GET /api/v1/playback/{camera_id}/file?path=<encoded-path>
```

Search response:

```json
{
  "status": true,
  "cameraId": "CAM-101",
  "files": [
    {
      "fileName": "CAM-101_20260709_100000.mp4",
      "startTime": "2026-07-09T10:00:00",
      "endTime": "2026-07-09T10:15:00",
      "playbackUrl": "http://localhost:8000/api/v1/playback/CAM-101/file?path=encoded"
    }
  ]
}
```

---

## 7. Middleware Requirements

## 7.1 Bearer Token Middleware

All protected APIs must use middleware.

Protected APIs:

```txt
/api/v1/streams/*
/api/v1/recorders/*
/api/v1/playback/*
```

Public APIs:

```txt
/health
/api/v1/health
/docs if enabled in non-production
```

Middleware behavior:

```txt
1. Check Authorization header.
2. Validate Bearer format.
3. Call Java validation API.
4. Continue request if valid.
5. Return 401 if invalid.
6. Return 503 if Java auth service is unavailable.
```

---

## 8. MediaMTX Technical Requirements

## 8.1 Path Name

```txt
cam-{camera_id}
```

Example:

```txt
cam-CAM-101
```

## 8.2 Public HLS URL

```txt
{public_hls_base_url}/cam-{camera_id}/index.m3u8
```

Example:

```txt
http://localhost:8888/cam-CAM-101/index.m3u8
```

## 8.3 MediaMTX Config

MediaMTX should be controlled through config/API where possible.

Required settings:

- HLS enabled
- WebRTC optional
- RTSP transport TCP preferred
- Dynamic path support if needed

---

## 9. FFmpeg Technical Requirements

## 9.1 Default Command Pattern

```bash
ffmpeg \
  -rtsp_transport tcp \
  -i "RTSP_URL" \
  -map 0:v:0 \
  -an \
  -c:v copy \
  -f segment \
  -segment_time 900 \
  -reset_timestamps 1 \
  -strftime 1 \
  "/data/recordings/CAM-101/%Y-%m-%d/%H/CAM-101_%Y%m%d_%H%M%S.mp4"
```

## 9.2 Requirements

- Must run as separate OS process.
- Must be managed by Python process manager.
- Must not block FastAPI request.
- Must support graceful stop.
- Must support forced kill after timeout.
- Must restart on failure based on config.

---

## 10. YAML Configuration Requirement

Create:

```txt
config/config.yaml
```

Required sample:

```yaml
app:
  name: "python-media-service"
  environment: "development"
  host: "0.0.0.0"
  port: 8000
  log_level: "INFO"

java_api:
  base_url: "http://java-api-server:8080"
  session_validate_endpoint: "/api/auth/session/validate"
  camera_stream_all_endpoint: "/api/devices/stream/all"
  timeout_seconds: 5
  retry_count: 2

security:
  enable_bearer_validation: true
  mask_rtsp_url_in_logs: true
  allow_docs_in_production: false

mediamtx:
  base_url: "http://localhost:9997"
  public_hls_base_url: "http://localhost:8888"
  public_webrtc_base_url: "http://localhost:8889"
  rtsp_transport: "tcp"
  path_prefix: "cam-"
  auto_create_paths: true
  start_on_demand: true

recording:
  enabled: true
  storage_root: "/data/recordings"
  segment_duration_seconds: 900
  file_extension: "mp4"
  ffmpeg_path: "/usr/bin/ffmpeg"
  rtsp_transport: "tcp"
  video_codec_mode: "copy"
  include_audio: false
  max_restart_attempts: 5
  restart_delay_seconds: 10
  stop_grace_seconds: 10

worker:
  max_recording_workers: 300
  max_live_streams: 300
  health_check_interval_seconds: 30
  inactive_stream_ttl_seconds: 300

storage:
  retention_days: 30
  min_free_disk_percent: 15
  cleanup_enabled: true

database:
  enabled: false
  type: "postgresql"
  host: ""
  port: 5432
  name: ""
  username: ""
  password: ""
```

---

## 11. Project Structure

```txt
python-media-service/
  app/
    main.py
    core/
      config.py
      logging.py
      security.py
      exceptions.py
    middleware/
      auth_middleware.py
    api/
      routes/
        streams.py
        recorders.py
        playback.py
        health.py
    services/
      java_client.py
      mediamtx_service.py
      recording_service.py
      playback_service.py
      camera_service.py
    workers/
      recorder_worker.py
      process_manager.py
    schemas/
      camera.py
      stream.py
      recorder.py
      playback.py
      common.py
    utils/
      rtsp.py
      file_utils.py
      time_utils.py
  config/
    config.yaml
  scripts/
    start.sh
    stop.sh
  storage/
  logs/
  tests/
  requirements.txt
  Dockerfile
  docker-compose.yml
  README.md
```

---

## 12. Error Response Standard

Use a common response format:

```json
{
  "status": false,
  "message": "Error message",
  "errorCode": "ERROR_CODE",
  "details": {}
}
```

Common error codes:

```txt
AUTH_TOKEN_MISSING
AUTH_TOKEN_INVALID
AUTH_SERVICE_UNAVAILABLE
CAMERA_NOT_FOUND
CAMERA_INACTIVE
JAVA_API_ERROR
MEDIAMTX_ERROR
RECORDING_ALREADY_RUNNING
RECORDING_NOT_RUNNING
FFMPEG_START_FAILED
STORAGE_NOT_AVAILABLE
PLAYBACK_FILE_NOT_FOUND
INVALID_FILE_PATH
```

---

## 13. Production Deployment Requirements

- Use Docker for Python service.
- Use Docker or binary for MediaMTX.
- Install FFmpeg inside Python service image or host machine.
- Mount recording storage volume.
- Mount YAML config as external file.
- Use Nginx reverse proxy in front of service.
- Set API timeouts.
- Configure CORS for frontend domain.
- Add service restart policy.
- Add log rotation.

---

## 14. 300 Camera Design Rules

- FastAPI should never transport raw video frames to frontend.
- MediaMTX must handle stream fanout.
- FFmpeg must run in background workers.
- Avoid transcoding unless absolutely required.
- Use `-c:v copy` by default.
- Use worker limits.
- Use disk free-space checks.
- Use retention cleanup.
- Use per-camera process state.
- Use clear logs and monitoring.
- Future scaling can split cameras across multiple media servers.

---

## 15. Future Improvements

- Redis for shared runtime state
- Database for recording metadata
- HLS playback generation
- WebRTC low-latency playback
- Multi-node media server assignment
- Camera health scheduler
- Admin UI for service status
- Prometheus/Grafana monitoring
- Object storage integration

---

## 16. Current Implementation Status

Updated on 2026-07-09.

Implemented foundation:

- `python-media-service/app/main.py` provides the FastAPI application.
- `python-media-service/app/core/config.py` loads and validates `config/config.yaml`.
- `python-media-service/app/core/logging.py` configures console/file logging and masks RTSP credentials.
- `python-media-service/app/api/routes/health.py` exposes `/health` and `/api/v1/health`.
- `python-media-service/app/services/java_client.py` validates bearer tokens and fetches stream-device camera info from Java.
- `python-media-service/app/middleware/auth_middleware.py` protects non-public APIs and maps auth errors.
- `python-media-service/app/services/camera_service.py` validates active camera status and keeps RTSP data internal.
- `python-media-service/app/services/mediamtx_service.py` generates MediaMTX paths and HLS URLs from YAML config.
- `python-media-service/app/services/stream_service.py` tracks active streams in memory.
- `python-media-service/app/api/routes/streams.py` exposes stream start, stop, status, and list APIs.
- `python-media-service/app/workers/recorder_worker.py` builds FFmpeg segmented MP4 commands and creates camera/date/hour output folders.
- `python-media-service/app/workers/process_manager.py` tracks FFmpeg processes, blocks duplicate starts, stops workers, monitors exits, and restarts failed workers when configured.
- `python-media-service/app/services/recording_service.py` starts/stops recording workers after camera validation.
- `python-media-service/app/api/routes/recorders.py` exposes recorder start, stop, status, and list APIs.
- `python-media-service/app/services/playback_service.py` searches local recordings and resolves encoded relative playback file tokens safely.
- `python-media-service/app/api/routes/playback.py` exposes playback search, file listing, and MP4 serving APIs.
- `python-media-service/app/services/storage_service.py` checks storage writability, free disk percentage, and retention cleanup.
- `python-media-service/Dockerfile` installs Python dependencies and FFmpeg.
- `python-media-service/docker-compose.yml` defines the Python service, mock Java API, and MediaMTX with mounted config, logs, and recording storage.
- `python-media-service/mediamtx.yml` enables RTSP, HLS, WebRTC, and the MediaMTX API.
- `python-media-service/app/mock_java.py` provides local Docker-only auth and camera-info endpoints for integration verification.
- `python-media-service/app/main.py` configures CORS, standardized error handlers, and lifespan shutdown cleanup.
- `python-media-service/README.md` documents Windows PowerShell setup and run commands.

Verification performed:

- Python compile check passed for `python-media-service/app`.
- Config loader successfully loaded the default YAML file.
- Uvicorn started locally on `127.0.0.1:8001`.
- `/health` and `/api/v1/health` returned successful JSON responses.
- `python -m unittest discover -s tests` passed 42 tests covering config/env overrides, CORS, RTSP masking, Java client responses, Java timeout handling, auth middleware responses, health dependency shape, camera service behavior, MediaMTX path/URL generation, stream route/service behavior, FFmpeg command building, process manager lifecycle/restart behavior, recorder route/service behavior, playback search/file serving, path traversal protection, and storage checks.
- Uvicorn smoke check confirmed `/api/v1/health` works and `/api/v1/streams/CAM-101/status` rejects missing bearer token with `AUTH_TOKEN_MISSING`.
- Uvicorn smoke check confirmed `/api/v1/recorders/CAM-101/status` rejects missing bearer token with `AUTH_TOKEN_MISSING`.
- Uvicorn smoke check confirmed `/api/v1/health` returns `storageFreePercent` and `/api/v1/playback/search` rejects missing bearer token with `AUTH_TOKEN_MISSING`.
- Uvicorn smoke check confirmed `/api/v1/health` returns MediaMTX and Java reachability fields.
- `docker compose config --quiet` passed.
- Docker Desktop was started successfully.
- `docker compose build` passed.
- `docker compose up -d` started `python-media-service`, `mock-java-api`, and `mediamtx`.
- Runtime `/api/v1/health` from Docker returned `mediamtx.reachable=true` and `javaApi.reachable=true` with mock Java.
- `docker compose exec -T python-media-service ffmpeg -version` confirmed FFmpeg 7.1.5 is available in the Python container.
- Mock Java validated `mock-valid-token` and returned `rtsp://mediamtx:8554/cam-CAM-101`.
- Synthetic FFmpeg publisher streamed test video to MediaMTX path `cam-CAM-101`.
- `POST /api/v1/streams/CAM-101/start` returned an HLS URL, and `curl -L http://127.0.0.1:8888/cam-CAM-101/index.m3u8` returned an HLS playlist.
- `POST /api/v1/recorders/CAM-101/start` recorded the synthetic stream and created `storage/recordings/CAM-101/2026-07-09/10/CAM-101_20260709_105707.mp4`.
- Playback search returned the recorded MP4, and playback file serving returned HTTP 200 with 215911 bytes.

Next technical slice:

1. Point `java_api.base_url` at the production Java API and verify real auth/camera-info integration.
2. Configure a real RTSP camera stream and verify HLS playback in React.
3. Start recording against the real RTSP source and verify MP4 segments plus playback.
