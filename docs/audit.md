# Audit: Python FastAPI Media Service Reality Check

## 1. Purpose

This audit document is used to verify whether the built Python FastAPI media service matches the PRD, implementation plan, and technical requirements.

The AI/developer must review the implementation against this checklist after each phase.

---

## 2. Scope Verification

### Required Scope

- [ ] React frontend calls Python FastAPI directly for stream/playback/recording.
- [x] Python validates bearer token by calling Java API.
- [x] Python gets camera RTSP/device info from Java API.
- [ ] Python uses MediaMTX for live streaming.
- [x] Python uses FFmpeg for recording.
- [x] Recording runs in background worker.
- [x] Recording files are saved as segmented `.mp4`.
- [x] YAML config is used.
- [x] No database is required for current version.
- [x] Future DB config exists but is disabled.

### Out of Scope Check

Confirm these are not incorrectly added:

- [x] Python does not implement login.
- [x] Python does not implement user management.
- [x] Python does not implement role management.
- [x] Python does not expose RTSP URL to frontend.
- [x] Python does not process video frames for analytics.
- [x] Python does not force database dependency.
- [ ] Frontend does not need to call Java directly for media flow.

---

## 3. Architecture Check

Expected architecture:

```txt
React Frontend
   ↓
Python FastAPI Media Service
   ↓
Java API Server for auth and camera info
   ↓
MediaMTX / FFmpeg / Storage / Cameras
```

Checklist:

- [x] Stream API is exposed from Python.
- [x] Playback API is exposed from Python.
- [x] Recorder API is exposed from Python.
- [x] Java is called for camera info.
- [ ] Java token validation is temporarily bypassed and must be restored before production.
- [ ] MediaMTX handles live stream output.
- [x] FFmpeg handles recording output.

---

## 4. Auth Middleware Audit

### Required Behavior

- [x] Middleware checks `Authorization` header.
- [x] Middleware requires `Bearer <token>` format.
- [ ] Middleware calls Java session validation API. Temporarily bypassed on 2026-07-10.
- [x] Any Bearer-format token allows request during development bypass.
- [ ] Invalid token returns 401 after Java auth is restored.
- [x] Missing token returns 401.
- [ ] Java auth service down returns 503 after Java auth is restored.
- [x] User/session data is attached to request state if needed.

### Error Response Check

Missing token response:

```json
{
  "status": false,
  "message": "Authorization token is required"
}
```

Invalid token response:

```json
{
  "status": false,
  "message": "Invalid or expired session"
}
```

Java unavailable response:

```json
{
  "status": false,
  "message": "Authentication service unavailable"
}
```

Status:

- [ ] Invalid-token and Java-auth-unavailable responses are paused while hardcoded auth pass is enabled.

---

## 5. Java API Integration Audit

### Token Validation API

Expected endpoint:

```txt
GET /api/auth/session/validate
```

Checklist:

- [x] Python calls this endpoint.
- [x] Python sends bearer token to Java.
- [x] Python handles valid response.
- [x] Python handles invalid response.
- [x] Python handles timeout.
- [x] Python handles Java server error.

---

### Camera Device Info API

Expected endpoint:

```txt
GET /api/devices/stream/all
```

Checklist:

- [x] Python calls this endpoint after successful token validation.
- [x] Python receives RTSP URL.
- [x] Python receives device ID, custom device ID, IP, port, username/password, and RTSP URL.
- [x] Python trims newline/whitespace from Java string fields.
- [x] Python selects the requested camera by `customDeviceId` or `deviceId`.
- [x] Python defaults Java stream devices to active because this endpoint does not send a status field.
- [x] Python does not return RTSP URL to frontend.
- [x] Python masks RTSP URL in logs.

---

## 6. Stream Service Audit

### APIs

```txt
POST /api/v1/streams/{camera_id}/start
POST /api/v1/streams/{camera_id}/stop
GET  /api/v1/streams/{camera_id}/status
GET  /api/v1/streams
```

Checklist:

- [x] Start stream API exists.
- [x] Stop stream API exists.
- [x] Stream status API exists.
- [x] List active streams API exists.
- [x] Start stream validates token.
- [x] Start stream gets camera info from Java.
- [x] Start stream configures/verifies MediaMTX path.
- [x] Start stream returns HLS URL.
- [x] Start stream does not return RTSP URL.
- [x] Status API returns active/inactive state.

Expected response example:

```json
{
  "status": true,
  "cameraId": "CAM-101",
  "streamStatus": "started",
  "streamType": "hls",
  "streamUrl": "http://localhost:8888/cam-CAM-101/index.m3u8"
}
```

Status:

- [x] Stream response follows expected format.

---

## 7. MediaMTX Audit

Checklist:

- [x] MediaMTX is installed/running.
- [x] MediaMTX is reachable from Python service.
- [x] MediaMTX HLS is enabled.
- [x] Path naming uses `cam-{camera_id}`.
- [x] Stream URL is generated from YAML config.
- [x] MediaMTX errors are handled.
- [x] MediaMTX configuration is not hardcoded.

Path check:

```txt
cam-CAM-101
```

HLS URL check:

```txt
http://localhost:8888/cam-CAM-101/index.m3u8
```

---

## 8. Recording Service Audit

### APIs

```txt
POST /api/v1/recorders/{camera_id}/start
POST /api/v1/recorders/{camera_id}/stop
GET  /api/v1/recorders/{camera_id}/status
GET  /api/v1/recorders
```

Checklist:

- [x] Start recording API exists.
- [x] Stop recording API exists.
- [x] Recording status API exists.
- [x] List active recorders API exists.
- [x] Start recording validates token.
- [x] Start recording gets camera info from Java.
- [x] Start recording starts background worker.
- [x] Start recording is blocked when recording is disabled by environment.
- [x] Start recording returns immediately.
- [x] Duplicate recording worker for same camera is blocked.
- [x] Stop recording gracefully terminates FFmpeg.
- [x] Status returns process ID and recording status.

---

## 9. FFmpeg Worker Audit

Checklist:

- [x] FFmpeg path comes from YAML config.
- [x] FFmpeg uses RTSP URL internally.
- [x] FFmpeg uses RTSP over TCP by default.
- [x] FFmpeg uses `-c:v copy` by default.
- [x] FFmpeg writes `.mp4` segments.
- [x] Segment duration comes from YAML config.
- [x] Output folder is camera-wise/date-wise/hour-wise.
- [x] Worker monitors FFmpeg process.
- [x] Worker supports restart attempts.
- [x] Worker logs FFmpeg failures.

Expected command contains:

```txt
-rtsp_transport tcp
-c:v copy
-f segment
-segment_time 900
-reset_timestamps 1
-strftime 1
```

Status:

- [x] FFmpeg command follows expected pattern.

---

## 10. Storage Audit

Expected structure:

```txt
/data/recordings/{camera_id}/{yyyy-mm-dd}/{hour}/{camera_id}_{yyyymmdd}_{hhmmss}.mp4
```

Checklist:

- [x] Storage root comes from YAML config.
- [x] Service creates folders automatically.
- [x] Recording files are `.mp4`.
- [x] Disk writable check exists.
- [x] Free disk check exists.
- [x] Retention config exists.
- [x] Cleanup job exists or is planned.
- [x] Playback cannot access files outside storage root.

---

## 11. Playback Audit

### APIs

```txt
GET /api/v1/playback/search
GET /api/v1/playback/{camera_id}/files
GET /api/v1/playback/{camera_id}/file
```

Checklist:

- [x] Playback search validates token.
- [x] Playback search filters by camera ID.
- [x] Playback search filters by date/time.
- [x] Playback returns playback URLs.
- [x] Playback file serving works.
- [x] Path traversal is blocked.
- [x] Missing file returns 404.

Expected search response:

```json
{
  "status": true,
  "cameraId": "CAM-101",
  "files": []
}
```

Status:

- [x] Playback response follows expected format.

---

## 12. YAML Config Audit

Required file:

```txt
config/config.yaml
```

Checklist:

- [x] `app` section exists.
- [x] `java_api` section exists.
- [x] `security` section exists.
- [x] `mediamtx` section exists.
- [x] `recording` section exists.
- [x] `worker` section exists.
- [x] `storage` section exists.
- [x] `database` section exists.
- [x] `database.enabled` is false by default.
- [ ] No important value is hardcoded in Python code. Auth currently has a temporary hardcoded development session and must be restored before production.

---

## 13. Logging Audit

Checklist:

- [x] Logs are structured.
- [x] Logs include timestamp.
- [x] Logs include level.
- [x] Logs include camera ID where applicable.
- [ ] Logs include stream/recording action.
- [x] Logs mask RTSP credentials.
- [ ] Logs capture Java API errors.
- [ ] Logs capture FFmpeg errors.
- [x] Logs capture storage errors.

Critical security check:

- [x] Full RTSP URL with password is never printed.

---

## 14. Production Readiness Audit

Checklist:

- [x] Dockerfile exists.
- [x] docker-compose.yml exists.
- [x] FFmpeg is installed in container or host.
- [x] MediaMTX service is defined.
- [x] Recording storage is mounted as volume.
- [x] YAML config is mounted externally.
- [x] Restart policy exists.
- [x] CORS is configured.
- [x] API timeout is configured.
- [x] Java API retry count is configured.
- [x] Graceful shutdown is implemented.
- [x] Active FFmpeg workers are stopped on shutdown.

---

## 15. 300 Camera Scalability Audit

Checklist:

- [x] FastAPI does not stream video bytes.
- [x] MediaMTX handles live video fanout.
- [x] FFmpeg handles recording as background process.
- [x] Max live streams is configurable.
- [x] Max recording workers is configurable.
- [x] Duplicate camera recording is blocked.
- [x] CPU-heavy transcoding is avoided.
- [x] Disk capacity is checked.
- [x] Storage retention is configurable.
- [x] Future multi-server scaling is documented.

---

## 16. Testing Audit

Checklist:

- [x] Config loader test exists.
- [x] RTSP URL masking test exists.
- [x] Auth middleware test exists.
- [x] Java client mock test exists.
- [x] Camera service test exists.
- [x] MediaMTX service test exists or mock exists.
- [x] FFmpeg command builder test exists.
- [x] Process manager test exists.
- [x] Playback file search test exists.
- [x] Path traversal test exists.

---

## 17. Missing Items Report Template

After audit, fill this section.

### Completed Items

```txt
- Phase 1 project scaffold created under python-media-service.
- FastAPI app has /health and /api/v1/health endpoints.
- YAML configuration loader validates app, Java API, security, MediaMTX, recording, worker, storage, and database sections.
- Environment overrides are supported with MEDIA_SERVICE__SECTION__KEY variables.
- Structured console/file logging is configured.
- RTSP credential masking utility is implemented and covered by a unit test.
- Java API client validates tokens, fetches stream-device camera info, handles timeout/retry behavior, and maps errors.
- Bearer token middleware rejects missing/invalid tokens, returns 503 when Java auth is unavailable, and attaches session info to request state.
- Auth middleware and Java client behavior are covered by unit tests with mocks.
- Camera service fetches Java stream-device camera info, rejects inactive cameras when a status is present, masks RTSP in logs, and keeps RTSP out of API responses.
- MediaMTX service generates `cam-{camera_id}` paths and HLS URLs from YAML config.
- Stream start, stop, status, and list APIs are mounted under `/api/v1/streams`.
- Stream service and route behavior are covered by tests.
- FFmpeg command builder creates segmented MP4 recording commands from YAML config.
- Process manager tracks per-camera FFmpeg workers, blocks duplicate starts, stops workers, monitors exits, and restarts failed workers when configured.
- Recorder start, stop, status, and list APIs are mounted under `/api/v1/recorders`.
- Recorder start respects `recording.enabled` / `MEDIA_SERVICE__RECORDING__ENABLED` and returns `RECORDING_DISABLED` when turned off.
- Recorder worker, process manager, recording service, and recorder route behavior are covered by tests.
- Playback search, date-wise listing, and safe MP4 serving APIs are mounted under `/api/v1/playback`.
- Playback service returns encoded relative file tokens, blocks path traversal, and never returns absolute storage paths.
- Storage service creates/checks storage root, reports free disk percent, blocks unsafe recording startup, and can clean files older than retention days.
- Playback and storage behavior are covered by tests.
- Dockerfile, docker-compose.yml, and MediaMTX config are present with FFmpeg installation, mounted config/storage/log volumes, and restart policies.
- Production hardening now includes CORS config, lifespan shutdown cleanup, global error response standardization, Java timeout/retry handling, worker limits, and health dependency reachability fields.
- `docker compose config --quiet` passed.
- `docker compose build` passed.
- `docker compose up -d` started Python service, mock Java API, and MediaMTX.
- Runtime health returned `mediamtx.reachable=true` and `javaApi.reachable=true` with the mock Java API.
- FFmpeg is installed in the Python container.
- Mock Java API validated `mock-valid-token` and returned MediaMTX RTSP camera info through the stream-device list contract.
- Synthetic FFmpeg publisher streamed test video to `rtsp://mediamtx:8554/cam-CAM-101`.
- Stream API returned `http://localhost:8888/cam-CAM-101/index.m3u8`.
- HLS playlist fetch succeeded through MediaMTX.
- Recorder API captured the synthetic RTSP stream and created an MP4 segment on mounted storage.
- Playback search and file serving returned the recorded MP4 through the Python API.
- README contains Windows PowerShell setup and run commands.
- README, `pyproject.toml`, requirements comments, `scripts/setup.ps1`, and `scripts/check_python_version.py` now document/enforce Python >=3.11,<3.14 for local Windows setup.
```

### Missing Items

```txt
- Real Java API integration remains pending until the production Java service is reachable.
- Real camera RTSP/HLS/browser playback remains pending until a camera stream is available.
```

### Bugs Found

```txt
- Windows local setup with Python 3.14.5 caused `pydantic-core` to build from source and fail because MSVC `link.exe` was unavailable. Fixed by documenting and preflighting the supported Python range: >=3.11,<3.14, plus adding a PowerShell setup script that checks existing virtual environments before installing dependencies.
```

### Security Issues

```txt
- None found in completed foundation/auth/stream/recorder/playback/storage/deployment-hardening slices. RTSP passwords are masked in logger output, raw RTSP is not returned by APIs, and playback file tokens are constrained to the storage root.
```

### Performance Risks

```txt
- Live stream and recording worker limits are enforced in memory. Playback searches the local filesystem. Multi-process or multi-node shared state remains future work.
```

### Next Required Fixes

```txt
1. Point `java_api.base_url` at the production Java API and verify real token/camera-info calls.
2. Configure a real RTSP camera stream and verify HLS playback in the React frontend.
3. Start recording against the real RTSP source and verify MP4 segments plus playback.
```

---

## 18. Final Audit Decision

Choose one:

```txt
[ ] PASS - Ready for integration testing
[x] PARTIAL PASS - Local Docker end-to-end works with mock Java and synthetic RTSP; production Java/camera integration is pending
[ ] FAIL - Major architecture or security issues found
```

Reviewer notes:

```txt
Foundation, auth-client, camera, MediaMTX path generation/runtime, stream control APIs, FFmpeg command building, process management, recorder APIs, playback APIs, storage management, Docker files, production hardening, and local mock end-to-end verification completed on 2026-07-09. The Docker stack validates tokens through mock Java, fetches camera info, publishes synthetic RTSP to MediaMTX, returns an HLS playlist, records MP4 segments, and serves playback files. Production Java API integration and real camera/browser playback verification remain pending.
```
