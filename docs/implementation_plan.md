# Blueprint: Python FastAPI Media Service Implementation Plan

## 1. Goal

Build a production-ready Python FastAPI media backend for live streaming, recording, and playback.

The service will:

- Receive direct requests from React frontend
- Validate bearer token through Java API server
- Get camera RTSP/device info from Java API server
- Use MediaMTX for live stream delivery
- Use FFmpeg background workers for recording
- Use YAML configuration
- Avoid database dependency for now
- Support future database integration

---

## 2. Development Phases

## Phase 1: Project Setup

Status: Completed on 2026-07-09.

Update on 2026-07-10: Java stream-device integration was aligned with the Java developer contract: `GET /api/devices/stream/all` returns all stream devices and Python selects the requested camera by trimmed `customDeviceId` or numeric `deviceId`.

### Tasks

- [x] Create project folder `python-media-service`.
- [x] Create FastAPI app structure.
- [x] Add virtual environment setup.
- [x] Add `requirements.txt`.
- [x] Add `.env.example` if needed.
- [x] Add `config/config.yaml`.
- [x] Add README with setup commands.
- [x] Add basic `/health` API.

### Expected Output

```txt
python-media-service/
  app/
  config/
  logs/
  storage/
  requirements.txt
  README.md
```

### Acceptance Check

- [x] App starts using Uvicorn.
- [x] `/health` returns success.
- [x] YAML config loads successfully.

---

## Phase 2: YAML Configuration Loader

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/core/config.py`.
- [x] Load YAML config from `config/config.yaml`.
- [x] Add validation for required config keys.
- [x] Add environment override support if needed.
- [x] Add config sections for app, Java API, security, MediaMTX, recording, worker, storage, and future database.

### Required Config Sections

```txt
app
java_api
security
mediamtx
recording
worker
storage
database
```

### Acceptance Check

- [x] App fails with clear error if config is missing.
- [x] App logs active environment.
- [x] Config can be imported in services.

---

## Phase 3: Logging Setup

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/core/logging.py`.
- [x] Add structured logs.
- [x] Add log file output.
- [x] Add console log output.
- [x] Add RTSP masking utility.
- [x] Ensure no RTSP credentials are printed.

### Acceptance Check

- [x] Logs include timestamp, level, module, camera ID where available.
- [x] RTSP passwords are masked.

---

## Phase 4: Java API Client

Status: Completed on 2026-07-09.

Update on 2026-07-10: Java session validation call is temporarily commented out for development. `validate_token` returns a hardcoded valid admin session. Stream-device camera lookup still calls Java.

### Tasks

- [x] Create `app/services/java_client.py`.
- [x] Temporarily bypass token validation API call with hardcoded valid session.
- [x] Implement stream-device list API call for camera RTSP/device lookup.
- [x] Add timeout handling.
- [x] Add retry handling.
- [x] Add clear error mapping.

### Required Java APIs

```txt
GET /api/auth/session/validate  # temporarily bypassed in Python
GET /api/devices/stream/all
```

### Acceptance Check

- [x] Any bearer token produces a hardcoded valid development session.
- [ ] Restore valid/invalid token response handling before production.
- [ ] Restore Java auth timeout handling before production.
- [x] Stream-device list response is parsed, trimmed, and matched to the requested camera.

---

## Phase 5: Bearer Token Middleware

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/middleware/auth_middleware.py`.
- [x] Read `Authorization` header.
- [x] Validate `Bearer <token>` format.
- [x] Use Java client validation hook; currently hardcoded pass for development.
- [x] Attach user/session info to request state.
- [x] Skip auth for `/health` and docs if configured.

### Error Rules

Missing token:

```json
{
  "status": false,
  "message": "Authorization token is required"
}
```

Invalid token:

```json
{
  "status": false,
  "message": "Invalid or expired session"
}
```

Java unavailable:

```json
{
  "status": false,
  "message": "Authentication service unavailable"
}
```

### Acceptance Check

- [x] Protected APIs reject missing token.
- [ ] Protected APIs reject invalid token after Java auth is restored.
- [x] Protected APIs continue when bearer format is valid during development bypass.

---

## Phase 6: Camera Service

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/services/camera_service.py`.
- [x] Get camera device info from Java API stream-device list.
- [x] Validate camera status is active.
- [x] Mask RTSP URL in logs.
- [x] Return clean internal camera object.

### Acceptance Check

- [x] Camera info is selected by `customDeviceId` or `deviceId`.
- [x] Inactive camera returns proper error.
- [x] RTSP URL is only used internally.

---

## Phase 7: MediaMTX Integration

Status: Partially completed on 2026-07-09. Path generation, HLS URL generation, local status shape, Docker runtime verification, synthetic RTSP publishing, and HLS playlist verification are complete. Browser playback in React with a real camera stream is still pending.

### Tasks

- [x] Install and run MediaMTX.
- [x] Create `app/services/mediamtx_service.py`.
- [x] Generate path name using `cam-{camera_id}`.
- [x] Configure or validate MediaMTX path.
- [x] Generate public HLS URL.
- [x] Add stream status check.

### MediaMTX Path Rule

```txt
cam-{camera_id}
```

Example:

```txt
cam-CAM-101
```

### Acceptance Check

- [x] Python can create or confirm MediaMTX path.
- [x] Python returns HLS URL.
- [ ] React can play returned stream URL.

---

## Phase 8: Stream APIs

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/api/routes/streams.py`.
- [x] Implement start stream API.
- [x] Implement stop stream API.
- [x] Implement stream status API.
- [x] Implement list active streams API.

### APIs

```txt
POST /api/v1/streams/{camera_id}/start
POST /api/v1/streams/{camera_id}/stop
GET  /api/v1/streams/{camera_id}/status
GET  /api/v1/streams
```

### Acceptance Check

- [x] Start stream validates token.
- [x] Start stream gets camera info from Java.
- [x] Start stream returns MediaMTX URL.
- [x] Stop stream returns success.
- [x] Status API returns active/inactive state.

---

## Phase 9: FFmpeg Process Manager

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/workers/process_manager.py`.
- [x] Track process by camera ID.
- [x] Prevent duplicate FFmpeg workers for same camera.
- [x] Stop FFmpeg gracefully.
- [x] Kill FFmpeg if graceful stop fails.
- [x] Store runtime state in memory.

### Runtime State Example

```json
{
  "cameraId": "CAM-101",
  "pid": 12345,
  "status": "recording",
  "startedAt": "2026-07-09T10:00:00",
  "restartCount": 0
}
```

### Acceptance Check

- [x] Process manager can start process.
- [x] Process manager can stop process.
- [x] Duplicate start is blocked.
- [x] Process state can be listed.

---

## Phase 10: FFmpeg Recording Worker

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/workers/recorder_worker.py`.
- [x] Build FFmpeg command safely.
- [x] Use RTSP over TCP.
- [x] Use `-c:v copy` by default.
- [x] Save segmented `.mp4` files.
- [x] Create camera/date/hour folders automatically.
- [x] Monitor process exit.
- [x] Restart on failure based on YAML config.

### FFmpeg Command Pattern

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

### Acceptance Check

- [x] Recording starts in background.
- [x] API response is returned immediately.
- [x] MP4 segments are created.
- [x] Worker restarts on failure if enabled.

---

## Phase 11: Recorder APIs

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/api/routes/recorders.py`.
- [x] Implement start recording API.
- [x] Implement stop recording API.
- [x] Implement recording status API.
- [x] Implement list recording workers API.

### APIs

```txt
POST /api/v1/recorders/{camera_id}/start
POST /api/v1/recorders/{camera_id}/stop
GET  /api/v1/recorders/{camera_id}/status
GET  /api/v1/recorders
```

### Acceptance Check

- [x] Start recording validates token.
- [x] Start recording gets RTSP info from Java.
- [x] Start recording creates background FFmpeg worker.
- [x] Start recording is blocked with `RECORDING_DISABLED` when `recording.enabled` is false.
- [x] Stop recording terminates worker.
- [x] Status returns PID and recording state.

---

## Phase 12: Playback Service

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/services/playback_service.py`.
- [x] Search files by camera ID.
- [x] Filter files by date/time range.
- [x] Generate safe playback URLs.
- [x] Prevent path traversal.
- [x] Serve `.mp4` files safely.

### Acceptance Check

- [x] Playback search returns only matching files.
- [x] Playback URL does not expose unsafe file path.
- [x] File serving works in browser.

---

## Phase 13: Playback APIs

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/api/routes/playback.py`.
- [x] Implement search API.
- [x] Implement date-wise files API.
- [x] Implement file playback API.

### APIs

```txt
GET /api/v1/playback/search
GET /api/v1/playback/{camera_id}/files
GET /api/v1/playback/{camera_id}/file
```

### Acceptance Check

- [x] Search validates token.
- [x] Search returns playback files.
- [x] React can play returned playback URL.

---

## Phase 14: Storage Management

Status: Completed on 2026-07-09.

### Tasks

- [x] Create storage root if missing.
- [x] Check free disk percentage.
- [x] Add retention cleanup job.
- [x] Add cleanup config in YAML.
- [x] Add error if storage is not writable.

### Acceptance Check

- [x] Service detects low disk.
- [x] Recording is blocked or warned if disk is unsafe.
- [x] Old files can be cleaned based on retention days.

---

## Phase 15: Health and Monitoring APIs

Status: Completed on 2026-07-09.

### Tasks

- [x] Add detailed health API.
- [x] Return active stream count.
- [x] Return active recording worker count.
- [x] Return MediaMTX reachability.
- [x] Return Java API reachability if needed.
- [x] Return storage free space.

### API

```txt
GET /api/v1/health
```

### Acceptance Check

- [x] Health API returns useful operational status.
- [x] Health API helps debug production issues.

---

## Phase 16: Docker and Deployment

Status: Completed on 2026-07-09.

### Tasks

- [x] Create Dockerfile.
- [x] Add FFmpeg installation in image.
- [x] Add docker-compose for Python service and MediaMTX.
- [x] Mount recording storage volume.
- [x] Mount config YAML.
- [x] Add restart policy.

### Acceptance Check

- [x] Service runs in Docker.
- [x] MediaMTX runs in Docker.
- [x] Recording files persist on mounted storage.

---

## Phase 17: Production Hardening

Status: Completed on 2026-07-09.

### Tasks

- [x] Add request timeout to Java calls.
- [x] Add retry policy.
- [x] Add max worker limit.
- [x] Add graceful shutdown to stop workers.
- [x] Add signal handling.
- [x] Add CORS rules.
- [x] Add API docs.
- [x] Add error response standardization.

### Acceptance Check

- [x] Service does not crash on Java timeout.
- [x] Service does not start more than max worker limit.
- [x] Service stops safely.

---

## Phase 18: Testing

### Tasks

- [x] Unit test config loading.
- [x] Unit test RTSP URL masking.
- [x] Unit test token middleware.
- [x] Unit test Java client with mock responses.
- [x] Unit test FFmpeg command builder.
- [x] Integration test stream start.
- [x] Integration test recording start/stop.
- [x] Integration test playback search.

### Acceptance Check

- [x] Core services have tests.
- [x] Basic integration flow works.

---

## Phase 19: Windows Local Setup Compatibility

Status: Completed on 2026-07-10.

### Trigger

Local dependency installation was attempted with Python 3.14.5:

```txt
pydantic-core build failed because MSVC link.exe was not found
```

The root cause is that the current pinned dependency set can fall back to a native build path on Python 3.14 for Windows.

### Tasks

- [x] Document supported local interpreter range as Python >=3.11,<3.14.
- [x] Update README setup commands to create the virtual environment with `py -3.12`.
- [x] Add `scripts/check_python_version.py` to fail fast before `pip install`.
- [x] Add `scripts/setup.ps1` so Windows setup checks the Python version before installing dependencies.
- [x] Add `pyproject.toml` with `requires-python = ">=3.11,<3.14"`.
- [x] Add requirements note so the dependency pin file carries the interpreter constraint.
- [x] Update PRD/TRD/audit docs with the local setup compatibility rule.

### Acceptance Check

- [x] Python 3.14 produces a clear unsupported-version message before dependency installation.
- [x] Existing Python 3.14 virtual environments are detected before `pip install -r requirements.txt`.
- [x] Docs tell developers to use Python 3.11, 3.12, or 3.13.

---

## Phase 20: Recording Service Environment Toggle

Status: Completed on 2026-07-10.

### Tasks

- [x] Use `recording.enabled` as the runtime recording service on/off switch.
- [x] Support environment override through `MEDIA_SERVICE__RECORDING__ENABLED=false`.
- [x] Block recording start with `503 RECORDING_DISABLED` when disabled.
- [x] Keep recorder status, list, and stop endpoints available for operator visibility.
- [x] Add tests for disabled recording start and list response state.
- [x] Update README, `.env.example`, PRD, TRD, implementation plan, and audit docs.

### Acceptance Check

- [x] Recording can be turned off using environment without code changes.
- [x] Disabled recording does not start FFmpeg workers.
- [x] Recording can be turned back on by setting `MEDIA_SERVICE__RECORDING__ENABLED=true`.

---

## Phase 21: React Integration Handoff

Status: Completed on 2026-07-10.

### Tasks

- [x] Add `docs/react_integration_guide.md` for React developer handoff.
- [x] Document Python API base URL, auth header, camera ID usage, stream APIs, recording APIs, playback APIs, and HLS playback.
- [x] Document temporary hardcoded auth bypass and production restore warning.
- [x] Document `RECORDING_DISABLED` handling for React controls.

### Acceptance Check

- [x] React developer can integrate live HLS playback using returned `streamUrl`.
- [x] React developer can start/stop recording and handle disabled recording mode.
- [x] React developer can search and play MP4 playback files using returned `playbackUrl`.

---

## Phase 22: Real RTSP MediaMTX Source Path Setup

Status: Completed on 2026-07-10.

### Trigger

Frontend received successful `POST /api/v1/streams/2/start` response, but live playback did not start. Python logs showed:

```txt
Fetched camera device info camera_id=CAM-02 rtsp=rtsp://admin:****@192.168.0.102:8080/h264.sdp
Confirmed MediaMTX path camera_id=CAM-02 path=cam-CAM-02
```

The service was only generating the HLS path and URL. It was not configuring MediaMTX to pull the camera RTSP URL as a source.

### Tasks

- [x] Update `MediaMtxService.ensure_stream_path` to configure MediaMTX path source using the camera RTSP URL.
- [x] Use MediaMTX API `PATCH /v3/config/paths/patch/{path}` for existing paths.
- [x] Use MediaMTX API `POST /v3/config/paths/add/{path}` when the path does not exist.
- [x] Keep RTSP credentials masked in logs.
- [x] Add tests for patch existing path and add missing path behavior.
- [x] Document LAN HLS base URL requirement for React clients on another machine.

### Acceptance Check

- [x] Start stream configures MediaMTX with the real RTSP source before returning HLS URL.
- [x] React must use returned `streamUrl`.
- [x] For LAN frontend, `MEDIA_SERVICE__MEDIAMTX__PUBLIC_HLS_BASE_URL` must point to reachable server IP such as `http://192.168.0.103:8888`.

---

## 3. Final Implementation Checklist

- [x] FastAPI project created.
- [x] YAML config working.
- [x] Auth middleware working.
- [x] Temporary hardcoded auth pass enabled for development.
- [ ] Java token validation restored after temporary hardcoded auth bypass.
- [x] Java stream-device camera info API integrated.
- [x] MediaMTX stream setup working.
- [x] Stream APIs working.
- [x] FFmpeg recording worker working.
- [x] Recorder APIs working.
- [x] Playback APIs working.
- [x] Storage structure working.
- [x] Logs implemented.
- [x] RTSP masking implemented.
- [x] Docker setup ready.
- [x] README complete.
- [x] Windows Python version preflight documented.
- [x] Recording service env on/off switch implemented.
- [x] React integration handoff documented.
- [x] MediaMTX real RTSP source path setup implemented.
- [ ] Audit checklist passed.
