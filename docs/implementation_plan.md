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

### Tasks

- [x] Create `app/services/java_client.py`.
- [x] Implement token validation API call.
- [x] Implement camera device info API call.
- [x] Add timeout handling.
- [x] Add retry handling.
- [x] Add clear error mapping.

### Required Java APIs

```txt
GET /api/auth/session/validate
GET /api/cameras/{camera_id}/device-info
```

### Acceptance Check

- [x] Valid token response is parsed.
- [x] Invalid token response is handled.
- [x] Java API timeout returns service unavailable error.
- [x] Camera info response is parsed.

---

## Phase 5: Bearer Token Middleware

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/middleware/auth_middleware.py`.
- [x] Read `Authorization` header.
- [x] Validate `Bearer <token>` format.
- [x] Call Java API validation endpoint.
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
- [x] Protected APIs reject invalid token.
- [x] Protected APIs continue when Java validates token.

---

## Phase 6: Camera Service

Status: Completed on 2026-07-09.

### Tasks

- [x] Create `app/services/camera_service.py`.
- [x] Get camera device info from Java API.
- [x] Validate camera status is active.
- [x] Mask RTSP URL in logs.
- [x] Return clean internal camera object.

### Acceptance Check

- [x] Camera info is fetched by camera ID.
- [x] Inactive camera returns proper error.
- [x] RTSP URL is only used internally.

---

## Phase 7: MediaMTX Integration

Status: Partially completed on 2026-07-09. Path generation, HLS URL generation, and local status shape exist. Actual MediaMTX installation/runtime verification is pending Docker/deployment work.

### Tasks

- [ ] Install and run MediaMTX.
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

Status: Partially completed on 2026-07-09. Command building, folder creation, process monitoring, and restart behavior are implemented. Live MP4 segment creation requires FFmpeg plus a reachable RTSP source.

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
- [ ] MP4 segments are created.
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
- [x] Stop recording terminates worker.
- [x] Status returns PID and recording state.

---

## Phase 12: Playback Service

### Tasks

- [ ] Create `app/services/playback_service.py`.
- [ ] Search files by camera ID.
- [ ] Filter files by date/time range.
- [ ] Generate safe playback URLs.
- [ ] Prevent path traversal.
- [ ] Serve `.mp4` files safely.

### Acceptance Check

- [ ] Playback search returns only matching files.
- [ ] Playback URL does not expose unsafe file path.
- [ ] File serving works in browser.

---

## Phase 13: Playback APIs

### Tasks

- [ ] Create `app/api/routes/playback.py`.
- [ ] Implement search API.
- [ ] Implement date-wise files API.
- [ ] Implement file playback API.

### APIs

```txt
GET /api/v1/playback/search
GET /api/v1/playback/{camera_id}/files
GET /api/v1/playback/{camera_id}/file
```

### Acceptance Check

- [ ] Search validates token.
- [ ] Search returns playback files.
- [ ] React can play returned playback URL.

---

## Phase 14: Storage Management

### Tasks

- [ ] Create storage root if missing.
- [ ] Check free disk percentage.
- [ ] Add retention cleanup job.
- [ ] Add cleanup config in YAML.
- [ ] Add error if storage is not writable.

### Acceptance Check

- [ ] Service detects low disk.
- [ ] Recording is blocked or warned if disk is unsafe.
- [ ] Old files can be cleaned based on retention days.

---

## Phase 15: Health and Monitoring APIs

Status: Partially completed on 2026-07-09. Basic detailed health shape exists; MediaMTX reachability, Java reachability, active worker counts, and storage free-space checks will be completed after service integrations exist.

### Tasks

- [x] Add detailed health API.
- [x] Return active stream count.
- [x] Return active recording worker count.
- [ ] Return MediaMTX reachability.
- [ ] Return Java API reachability if needed.
- [ ] Return storage free space.

### API

```txt
GET /api/v1/health
```

### Acceptance Check

- [ ] Health API returns useful operational status.
- [ ] Health API helps debug production issues.

---

## Phase 16: Docker and Deployment

### Tasks

- [ ] Create Dockerfile.
- [ ] Add FFmpeg installation in image.
- [ ] Add docker-compose for Python service and MediaMTX.
- [ ] Mount recording storage volume.
- [ ] Mount config YAML.
- [ ] Add restart policy.

### Acceptance Check

- [ ] Service runs in Docker.
- [ ] MediaMTX runs in Docker.
- [ ] Recording files persist on mounted storage.

---

## Phase 17: Production Hardening

### Tasks

- [ ] Add request timeout to Java calls.
- [ ] Add retry policy.
- [ ] Add max worker limit.
- [ ] Add graceful shutdown to stop workers.
- [ ] Add signal handling.
- [ ] Add CORS rules.
- [ ] Add API docs.
- [ ] Add error response standardization.

### Acceptance Check

- [ ] Service does not crash on Java timeout.
- [ ] Service does not start more than max worker limit.
- [ ] Service stops safely.

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
- [ ] Integration test playback search.

### Acceptance Check

- [x] Core services have tests.
- [ ] Basic integration flow works.

---

## 3. Final Implementation Checklist

- [x] FastAPI project created.
- [x] YAML config working.
- [x] Auth middleware working.
- [x] Java token validation integrated.
- [x] Java camera info API integrated.
- [ ] MediaMTX stream setup working.
- [x] Stream APIs working.
- [x] FFmpeg recording worker working.
- [x] Recorder APIs working.
- [ ] Playback APIs working.
- [x] Storage structure working.
- [x] Logs implemented.
- [x] RTSP masking implemented.
- [ ] Docker setup ready.
- [ ] README complete.
- [ ] Audit checklist passed.
