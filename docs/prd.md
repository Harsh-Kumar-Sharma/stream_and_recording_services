# PRD: Python FastAPI Media Service

## 1. Product Name

Python FastAPI Media Service for Camera Live Streaming, Recording, and Playback.

---

## 2. Purpose

The purpose of this service is to provide a dedicated media backend for CCTV/IP camera live streaming, video recording, and playback.

The React frontend will call the Python FastAPI media service directly for stream, playback, and recording operations. The Python service will validate the frontend bearer token by calling the Java API server. After successful validation, Python will get camera RTSP/device information from the Java API server and then use MediaMTX for live streaming and FFmpeg background workers for recording.

This service is designed to support around 300 live cameras.

---

## 3. Users

### Primary Users

- Control room operators
- System administrators
- Monitoring dashboard users
- Technical support team

### System Users

- React frontend dashboard
- Java API server
- Python FastAPI media server
- MediaMTX server
- FFmpeg recording workers
- RTSP IP cameras

---

## 4. Current System Context

The complete system has three major parts:

```txt
React Frontend
   ↓
Python FastAPI Media Service
   ↓
Java API Server for token validation and camera info
   ↓
RTSP Cameras / MediaMTX / FFmpeg
```

Important communication rule:

```txt
Frontend does not call Java API directly for live stream or playback.
Frontend calls Python FastAPI directly.
Python validates token by calling Java API.
Python gets camera RTSP/device info from Java API.
```

---

## 5. Core Features Allowed in Scope

### 5.1 Bearer Token Validation

Python FastAPI must validate every protected request using the bearer token from the frontend.

Expected flow:

```txt
1. React sends request to Python with Authorization: Bearer <token>.
2. Python middleware reads the token.
3. Python calls Java API server session validation endpoint.
4. If Java says valid, Python continues the request.
5. If Java says invalid, Python returns 401 Unauthorized.
6. If Java API is unavailable, Python returns 503 Service Unavailable.
```

Python will not validate JWT locally in the current scope.

---

### 5.2 Camera Device Info Fetching

Python FastAPI must get camera device information from Java API server.

Required camera data:

- Camera ID
- Camera name
- RTSP URL
- IP address
- Camera status
- Site ID
- Gantry ID
- Lane ID

Python must never expose raw RTSP URL to the React frontend.

---

### 5.3 Live Streaming

Python FastAPI must provide live stream start, stop, and status APIs.

Live streaming will use MediaMTX.

Camera input:

```txt
RTSP
```

Output stream options:

```txt
HLS for stable browser playback
WebRTC for low-latency live playback if required
```

The first version should support HLS URL generation through MediaMTX.

---

### 5.4 Recording

Python FastAPI must provide recording start, stop, and status APIs.

Recording will use FFmpeg.

Important rule:

```txt
Recording must run in a background worker.
Recording must not run directly inside the FastAPI request thread.
```

FFmpeg will:

- Read RTSP stream
- Save segmented `.mp4` files
- Use time-based file segmentation
- Save recordings camera-wise and date-wise
- Restart on failure based on configuration

---

### 5.5 Playback

Python FastAPI must provide playback APIs to search local recording files and return playback URLs.

Current playback scope:

- Search files by camera ID and date/time
- Return file list
- Return playback URL
- Serve `.mp4` files from local/mounted storage

Future playback scope:

- Timeline-based playback
- HLS playback conversion
- Recording metadata from database

---

### 5.6 YAML-Based Configuration

The service must use YAML configuration for environment settings.

Configuration should include:

- App host/port
- Java API base URL
- Java session validation endpoint
- Java camera device info endpoint
- MediaMTX settings
- FFmpeg path and recording settings
- Worker limits
- Storage path
- Retention policy
- Future database config disabled by default

---

### 5.7 Logging and Error Handling

The service must include structured logs for:

- Token validation result
- Camera info fetch result
- Stream start/stop
- Recording start/stop
- FFmpeg worker start/failure/restart
- Playback request
- Storage error
- Java API unavailable

RTSP username and password must be masked in logs.

---

## 6. Features Not Allowed in Current Scope

The Python service must not include these in the current version:

- User login
- User registration
- Role management
- Permission management
- Camera master CRUD
- Frontend dashboard business APIs
- Direct frontend access to Java for media flow
- Database dependency as a mandatory requirement
- RTSP URL exposure to frontend
- Video analytics
- Object detection
- ANPR/VIDS/ATTC model processing
- Complex timeline UI
- Cloud object storage integration unless added later

---

## 7. Functional Requirements

### FR-1: Auth Middleware

The service must have FastAPI middleware to validate bearer token by calling Java API.

Acceptance criteria:

- Missing token returns 401.
- Invalid token returns 401.
- Java validation API error returns 503.
- Valid token continues request.
- User/session information can be attached to request context.

---

### FR-2: Start Live Stream

The service must start or prepare live stream for a camera.

API:

```txt
POST /api/v1/streams/{camera_id}/start
```

Acceptance criteria:

- Validate token through Java.
- Fetch camera RTSP/device info from Java.
- Configure or verify MediaMTX path.
- Return stream URL to frontend.
- Do not return raw RTSP URL.

---

### FR-3: Stop Live Stream

The service must stop or mark a stream inactive where applicable.

API:

```txt
POST /api/v1/streams/{camera_id}/stop
```

Acceptance criteria:

- Validate token.
- Stop stream session or clear MediaMTX path if configured dynamically.
- Return success response.

---

### FR-4: Stream Status

The service must return stream status for a camera.

API:

```txt
GET /api/v1/streams/{camera_id}/status
```

Acceptance criteria:

- Validate token.
- Return whether stream is active.
- Return stream URL if active.
- Return last error if available.

---

### FR-5: Start Recording

The service must start a recording worker for a camera.

API:

```txt
POST /api/v1/recorders/{camera_id}/start
```

Acceptance criteria:

- Validate token.
- Fetch camera RTSP/device info from Java.
- Start FFmpeg in background worker.
- Return response immediately.
- Maintain runtime process state.
- Prevent duplicate recording process for same camera.

---

### FR-6: Stop Recording

The service must stop active recording for a camera.

API:

```txt
POST /api/v1/recorders/{camera_id}/stop
```

Acceptance criteria:

- Validate token.
- Stop FFmpeg process safely.
- Update runtime state.
- Return stopped response.

---

### FR-7: Recording Status

The service must return recording worker status.

API:

```txt
GET /api/v1/recorders/{camera_id}/status
```

Acceptance criteria:

- Return recording status.
- Return process ID if active.
- Return started time.
- Return restart count.
- Return latest output file path if available.

---

### FR-8: Playback Search

The service must search local recording files.

API:

```txt
GET /api/v1/playback/search?cameraId=CAM-101&from=2026-07-09T10:00:00&to=2026-07-09T11:00:00
```

Acceptance criteria:

- Validate token.
- Search file system by camera/date/time.
- Return matching files.
- Return playback URLs.

---

### FR-9: Health APIs

The service must expose health endpoints.

APIs:

```txt
GET /health
GET /api/v1/health
```

Acceptance criteria:

- Basic health returns service status.
- Detailed health returns MediaMTX reachability, storage availability, and active worker counts.

---

## 8. Non-Functional Requirements

### NFR-1: Scalability

The service should be designed for around 300 cameras.

Rules:

- Do not stream video bytes through FastAPI.
- Use MediaMTX for live stream delivery.
- Use FFmpeg background workers for recording.
- Use process limits from YAML.
- Avoid CPU-heavy transcoding by default.

---

### NFR-2: Performance

- API requests should return quickly.
- Recording should run in background.
- Use `-c:v copy` for FFmpeg recording where possible.
- Use RTSP over TCP by default for stable connections.

---

### NFR-3: Security

- RTSP URLs must not be exposed to frontend.
- RTSP credentials must be masked in logs.
- Bearer token must be validated before protected operations.
- Java API communication timeout must be configured.
- File path traversal must be blocked in playback APIs.

---

### NFR-4: Reliability

- FFmpeg failures should be detected.
- Restart should happen based on retry config.
- Duplicate workers for the same camera should be blocked.
- Disk free-space checks should be available before recording.

---

### NFR-5: Maintainability

- Use clean FastAPI project structure.
- Separate routes, services, workers, schemas, and utilities.
- Use YAML config.
- Add clear README and API docs.

---

## 9. Expected API Summary

```txt
GET  /health
GET  /api/v1/health
POST /api/v1/streams/{camera_id}/start
POST /api/v1/streams/{camera_id}/stop
GET  /api/v1/streams/{camera_id}/status
GET  /api/v1/streams
POST /api/v1/recorders/{camera_id}/start
POST /api/v1/recorders/{camera_id}/stop
GET  /api/v1/recorders/{camera_id}/status
GET  /api/v1/recorders
GET  /api/v1/playback/search
GET  /api/v1/playback/{camera_id}/files
GET  /api/v1/playback/{camera_id}/file
```

---

## 10. Final Success Criteria

The project is successful when:

- React can call Python stream API directly.
- Python validates token using Java API.
- Python fetches camera RTSP/device info from Java.
- Python starts MediaMTX stream and returns live URL.
- React can play the live URL.
- Python starts FFmpeg recording in background.
- FFmpeg writes segmented `.mp4` files.
- Python can search and serve playback files.
- No raw RTSP URL is exposed to frontend.
- YAML config controls app, Java API, MediaMTX, FFmpeg, worker, and storage settings.
