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

### Tasks

- [ ] Create project folder `python-media-service`.
- [ ] Create FastAPI app structure.
- [ ] Add virtual environment setup.
- [ ] Add `requirements.txt`.
- [ ] Add `.env.example` if needed.
- [ ] Add `config/config.yaml`.
- [ ] Add README with setup commands.
- [ ] Add basic `/health` API.

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

- [ ] App starts using Uvicorn.
- [ ] `/health` returns success.
- [ ] YAML config loads successfully.

---

## Phase 2: YAML Configuration Loader

### Tasks

- [ ] Create `app/core/config.py`.
- [ ] Load YAML config from `config/config.yaml`.
- [ ] Add validation for required config keys.
- [ ] Add environment override support if needed.
- [ ] Add config sections for app, Java API, security, MediaMTX, recording, worker, storage, and future database.

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

- [ ] App fails with clear error if config is missing.
- [ ] App logs active environment.
- [ ] Config can be imported in services.

---

## Phase 3: Logging Setup

### Tasks

- [ ] Create `app/core/logging.py`.
- [ ] Add structured logs.
- [ ] Add log file output.
- [ ] Add console log output.
- [ ] Add RTSP masking utility.
- [ ] Ensure no RTSP credentials are printed.

### Acceptance Check

- [ ] Logs include timestamp, level, module, camera ID where available.
- [ ] RTSP passwords are masked.

---

## Phase 4: Java API Client

### Tasks

- [ ] Create `app/services/java_client.py`.
- [ ] Implement token validation API call.
- [ ] Implement camera device info API call.
- [ ] Add timeout handling.
- [ ] Add retry handling.
- [ ] Add clear error mapping.

### Required Java APIs

```txt
GET /api/auth/session/validate
GET /api/cameras/{camera_id}/device-info
```

### Acceptance Check

- [ ] Valid token response is parsed.
- [ ] Invalid token response is handled.
- [ ] Java API timeout returns service unavailable error.
- [ ] Camera info response is parsed.

---

## Phase 5: Bearer Token Middleware

### Tasks

- [ ] Create `app/middleware/auth_middleware.py`.
- [ ] Read `Authorization` header.
- [ ] Validate `Bearer <token>` format.
- [ ] Call Java API validation endpoint.
- [ ] Attach user/session info to request state.
- [ ] Skip auth for `/health` and docs if configured.

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

- [ ] Protected APIs reject missing token.
- [ ] Protected APIs reject invalid token.
- [ ] Protected APIs continue when Java validates token.

---

## Phase 6: Camera Service

### Tasks

- [ ] Create `app/services/camera_service.py`.
- [ ] Get camera device info from Java API.
- [ ] Validate camera status is active.
- [ ] Mask RTSP URL in logs.
- [ ] Return clean internal camera object.

### Acceptance Check

- [ ] Camera info is fetched by camera ID.
- [ ] Inactive camera returns proper error.
- [ ] RTSP URL is only used internally.

---

## Phase 7: MediaMTX Integration

### Tasks

- [ ] Install and run MediaMTX.
- [ ] Create `app/services/mediamtx_service.py`.
- [ ] Generate path name using `cam-{camera_id}`.
- [ ] Configure or validate MediaMTX path.
- [ ] Generate public HLS URL.
- [ ] Add stream status check.

### MediaMTX Path Rule

```txt
cam-{camera_id}
```

Example:

```txt
cam-CAM-101
```

### Acceptance Check

- [ ] Python can create or confirm MediaMTX path.
- [ ] Python returns HLS URL.
- [ ] React can play returned stream URL.

---

## Phase 8: Stream APIs

### Tasks

- [ ] Create `app/api/routes/streams.py`.
- [ ] Implement start stream API.
- [ ] Implement stop stream API.
- [ ] Implement stream status API.
- [ ] Implement list active streams API.

### APIs

```txt
POST /api/v1/streams/{camera_id}/start
POST /api/v1/streams/{camera_id}/stop
GET  /api/v1/streams/{camera_id}/status
GET  /api/v1/streams
```

### Acceptance Check

- [ ] Start stream validates token.
- [ ] Start stream gets camera info from Java.
- [ ] Start stream returns MediaMTX URL.
- [ ] Stop stream returns success.
- [ ] Status API returns active/inactive state.

---

## Phase 9: FFmpeg Process Manager

### Tasks

- [ ] Create `app/workers/process_manager.py`.
- [ ] Track process by camera ID.
- [ ] Prevent duplicate FFmpeg workers for same camera.
- [ ] Stop FFmpeg gracefully.
- [ ] Kill FFmpeg if graceful stop fails.
- [ ] Store runtime state in memory.

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

- [ ] Process manager can start process.
- [ ] Process manager can stop process.
- [ ] Duplicate start is blocked.
- [ ] Process state can be listed.

---

## Phase 10: FFmpeg Recording Worker

### Tasks

- [ ] Create `app/workers/recorder_worker.py`.
- [ ] Build FFmpeg command safely.
- [ ] Use RTSP over TCP.
- [ ] Use `-c:v copy` by default.
- [ ] Save segmented `.mp4` files.
- [ ] Create camera/date/hour folders automatically.
- [ ] Monitor process exit.
- [ ] Restart on failure based on YAML config.

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

- [ ] Recording starts in background.
- [ ] API response is returned immediately.
- [ ] MP4 segments are created.
- [ ] Worker restarts on failure if enabled.

---

## Phase 11: Recorder APIs

### Tasks

- [ ] Create `app/api/routes/recorders.py`.
- [ ] Implement start recording API.
- [ ] Implement stop recording API.
- [ ] Implement recording status API.
- [ ] Implement list recording workers API.

### APIs

```txt
POST /api/v1/recorders/{camera_id}/start
POST /api/v1/recorders/{camera_id}/stop
GET  /api/v1/recorders/{camera_id}/status
GET  /api/v1/recorders
```

### Acceptance Check

- [ ] Start recording validates token.
- [ ] Start recording gets RTSP info from Java.
- [ ] Start recording creates background FFmpeg worker.
- [ ] Stop recording terminates worker.
- [ ] Status returns PID and recording state.

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

### Tasks

- [ ] Add detailed health API.
- [ ] Return active stream count.
- [ ] Return active recording worker count.
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

- [ ] Unit test config loading.
- [ ] Unit test RTSP URL masking.
- [ ] Unit test token middleware.
- [ ] Unit test Java client with mock responses.
- [ ] Unit test FFmpeg command builder.
- [ ] Integration test stream start.
- [ ] Integration test recording start/stop.
- [ ] Integration test playback search.

### Acceptance Check

- [ ] Core services have tests.
- [ ] Basic integration flow works.

---

## 3. Final Implementation Checklist

- [ ] FastAPI project created.
- [ ] YAML config working.
- [ ] Auth middleware working.
- [ ] Java token validation integrated.
- [ ] Java camera info API integrated.
- [ ] MediaMTX stream setup working.
- [ ] Stream APIs working.
- [ ] FFmpeg recording worker working.
- [ ] Recorder APIs working.
- [ ] Playback APIs working.
- [ ] Storage structure working.
- [ ] Logs implemented.
- [ ] RTSP masking implemented.
- [ ] Docker setup ready.
- [ ] README complete.
- [ ] Audit checklist passed.
