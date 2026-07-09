# Audit: Python FastAPI Media Service Reality Check

## 1. Purpose

This audit document is used to verify whether the built Python FastAPI media service matches the PRD, implementation plan, and technical requirements.

The AI/developer must review the implementation against this checklist after each phase.

---

## 2. Scope Verification

### Required Scope

- [ ] React frontend calls Python FastAPI directly for stream/playback/recording.
- [ ] Python validates bearer token by calling Java API.
- [ ] Python gets camera RTSP/device info from Java API.
- [ ] Python uses MediaMTX for live streaming.
- [ ] Python uses FFmpeg for recording.
- [ ] Recording runs in background worker.
- [ ] Recording files are saved as segmented `.mp4`.
- [ ] YAML config is used.
- [ ] No database is required for current version.
- [ ] Future DB config exists but is disabled.

### Out of Scope Check

Confirm these are not incorrectly added:

- [ ] Python does not implement login.
- [ ] Python does not implement user management.
- [ ] Python does not implement role management.
- [ ] Python does not expose RTSP URL to frontend.
- [ ] Python does not process video frames for analytics.
- [ ] Python does not force database dependency.
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

- [ ] Stream API is exposed from Python.
- [ ] Playback API is exposed from Python.
- [ ] Recorder API is exposed from Python.
- [ ] Java is called only for token validation and camera info.
- [ ] MediaMTX handles live stream output.
- [ ] FFmpeg handles recording output.

---

## 4. Auth Middleware Audit

### Required Behavior

- [ ] Middleware checks `Authorization` header.
- [ ] Middleware requires `Bearer <token>` format.
- [ ] Middleware calls Java session validation API.
- [ ] Valid token allows request.
- [ ] Invalid token returns 401.
- [ ] Missing token returns 401.
- [ ] Java auth service down returns 503.
- [ ] User/session data is attached to request state if needed.

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

- [ ] Error responses match expected format.

---

## 5. Java API Integration Audit

### Token Validation API

Expected endpoint:

```txt
GET /api/auth/session/validate
```

Checklist:

- [ ] Python calls this endpoint.
- [ ] Python sends bearer token to Java.
- [ ] Python handles valid response.
- [ ] Python handles invalid response.
- [ ] Python handles timeout.
- [ ] Python handles Java server error.

---

### Camera Device Info API

Expected endpoint:

```txt
GET /api/cameras/{camera_id}/device-info
```

Checklist:

- [ ] Python calls this endpoint after successful token validation.
- [ ] Python receives RTSP URL.
- [ ] Python receives camera ID/name/IP/status.
- [ ] Python checks camera is active.
- [ ] Python does not return RTSP URL to frontend.
- [ ] Python masks RTSP URL in logs.

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

- [ ] Start stream API exists.
- [ ] Stop stream API exists.
- [ ] Stream status API exists.
- [ ] List active streams API exists.
- [ ] Start stream validates token.
- [ ] Start stream gets camera info from Java.
- [ ] Start stream configures/verifies MediaMTX path.
- [ ] Start stream returns HLS URL.
- [ ] Start stream does not return RTSP URL.
- [ ] Status API returns active/inactive state.

Expected response example:

```json
{
  "status": true,
  "cameraId": "CAM-101",
  "streamStatus": "started",
  "streamType": "hls",
  "streamUrl": "https://media.example.com/cam-CAM-101/index.m3u8"
}
```

Status:

- [ ] Stream response follows expected format.

---

## 7. MediaMTX Audit

Checklist:

- [ ] MediaMTX is installed/running.
- [ ] MediaMTX is reachable from Python service.
- [ ] MediaMTX HLS is enabled.
- [ ] Path naming uses `cam-{camera_id}`.
- [ ] Stream URL is generated from YAML config.
- [ ] MediaMTX errors are handled.
- [ ] MediaMTX configuration is not hardcoded.

Path check:

```txt
cam-CAM-101
```

HLS URL check:

```txt
https://media.example.com/cam-CAM-101/index.m3u8
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

- [ ] Start recording API exists.
- [ ] Stop recording API exists.
- [ ] Recording status API exists.
- [ ] List active recorders API exists.
- [ ] Start recording validates token.
- [ ] Start recording gets camera info from Java.
- [ ] Start recording starts background worker.
- [ ] Start recording returns immediately.
- [ ] Duplicate recording worker for same camera is blocked.
- [ ] Stop recording gracefully terminates FFmpeg.
- [ ] Status returns process ID and recording status.

---

## 9. FFmpeg Worker Audit

Checklist:

- [ ] FFmpeg path comes from YAML config.
- [ ] FFmpeg uses RTSP URL internally.
- [ ] FFmpeg uses RTSP over TCP by default.
- [ ] FFmpeg uses `-c:v copy` by default.
- [ ] FFmpeg writes `.mp4` segments.
- [ ] Segment duration comes from YAML config.
- [ ] Output folder is camera-wise/date-wise/hour-wise.
- [ ] Worker monitors FFmpeg process.
- [ ] Worker supports restart attempts.
- [ ] Worker logs FFmpeg failures.

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

- [ ] FFmpeg command follows expected pattern.

---

## 10. Storage Audit

Expected structure:

```txt
/data/recordings/{camera_id}/{yyyy-mm-dd}/{hour}/{camera_id}_{yyyymmdd}_{hhmmss}.mp4
```

Checklist:

- [ ] Storage root comes from YAML config.
- [ ] Service creates folders automatically.
- [ ] Recording files are `.mp4`.
- [ ] Disk writable check exists.
- [ ] Free disk check exists.
- [ ] Retention config exists.
- [ ] Cleanup job exists or is planned.
- [ ] Playback cannot access files outside storage root.

---

## 11. Playback Audit

### APIs

```txt
GET /api/v1/playback/search
GET /api/v1/playback/{camera_id}/files
GET /api/v1/playback/{camera_id}/file
```

Checklist:

- [ ] Playback search validates token.
- [ ] Playback search filters by camera ID.
- [ ] Playback search filters by date/time.
- [ ] Playback returns playback URLs.
- [ ] Playback file serving works.
- [ ] Path traversal is blocked.
- [ ] Missing file returns 404.

Expected search response:

```json
{
  "status": true,
  "cameraId": "CAM-101",
  "files": []
}
```

Status:

- [ ] Playback response follows expected format.

---

## 12. YAML Config Audit

Required file:

```txt
config/config.yaml
```

Checklist:

- [ ] `app` section exists.
- [ ] `java_api` section exists.
- [ ] `security` section exists.
- [ ] `mediamtx` section exists.
- [ ] `recording` section exists.
- [ ] `worker` section exists.
- [ ] `storage` section exists.
- [ ] `database` section exists.
- [ ] `database.enabled` is false by default.
- [ ] No important value is hardcoded in Python code.

---

## 13. Logging Audit

Checklist:

- [ ] Logs are structured.
- [ ] Logs include timestamp.
- [ ] Logs include level.
- [ ] Logs include camera ID where applicable.
- [ ] Logs include stream/recording action.
- [ ] Logs mask RTSP credentials.
- [ ] Logs capture Java API errors.
- [ ] Logs capture FFmpeg errors.
- [ ] Logs capture storage errors.

Critical security check:

- [ ] Full RTSP URL with password is never printed.

---

## 14. Production Readiness Audit

Checklist:

- [ ] Dockerfile exists.
- [ ] docker-compose.yml exists.
- [ ] FFmpeg is installed in container or host.
- [ ] MediaMTX service is defined.
- [ ] Recording storage is mounted as volume.
- [ ] YAML config is mounted externally.
- [ ] Restart policy exists.
- [ ] CORS is configured.
- [ ] API timeout is configured.
- [ ] Java API retry count is configured.
- [ ] Graceful shutdown is implemented.
- [ ] Active FFmpeg workers are stopped on shutdown.

---

## 15. 300 Camera Scalability Audit

Checklist:

- [ ] FastAPI does not stream video bytes.
- [ ] MediaMTX handles live video fanout.
- [ ] FFmpeg handles recording as background process.
- [ ] Max live streams is configurable.
- [ ] Max recording workers is configurable.
- [ ] Duplicate camera recording is blocked.
- [ ] CPU-heavy transcoding is avoided.
- [ ] Disk capacity is checked.
- [ ] Storage retention is configurable.
- [ ] Future multi-server scaling is documented.

---

## 16. Testing Audit

Checklist:

- [ ] Config loader test exists.
- [ ] Auth middleware test exists.
- [ ] Java client mock test exists.
- [ ] Camera service test exists.
- [ ] MediaMTX service test exists or mock exists.
- [ ] FFmpeg command builder test exists.
- [ ] Process manager test exists.
- [ ] Playback file search test exists.
- [ ] Path traversal test exists.

---

## 17. Missing Items Report Template

After audit, fill this section.

### Completed Items

```txt
- 
```

### Missing Items

```txt
- 
```

### Bugs Found

```txt
- 
```

### Security Issues

```txt
- 
```

### Performance Risks

```txt
- 
```

### Next Required Fixes

```txt
1. 
2. 
3. 
```

---

## 18. Final Audit Decision

Choose one:

```txt
[ ] PASS - Ready for integration testing
[ ] PARTIAL PASS - Core flow works but missing production items
[ ] FAIL - Major architecture or security issues found
```

Reviewer notes:

```txt

```
