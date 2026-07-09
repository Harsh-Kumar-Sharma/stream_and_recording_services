# Python Media Service

FastAPI media-control backend for CCTV live streaming, recording, and playback.

Current implementation status:

- FastAPI app scaffold
- YAML configuration loader with validation
- Environment override support with `MEDIA_SERVICE__SECTION__KEY`
- Structured console and file logging
- RTSP credential masking helper
- Basic and detailed health endpoints
- Java API client for token validation and camera device info
- Bearer token middleware for protected APIs
- Camera service active-status validation
- MediaMTX HLS URL/path generation
- Stream start, stop, status, and list APIs
- FFmpeg command builder and background process manager
- Recorder start, stop, status, and list APIs

## Setup

```powershell
cd python-media-service
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
cd python-media-service
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health checks:

```txt
GET http://localhost:8000/health
GET http://localhost:8000/api/v1/health
```

Protected media APIs must send:

```txt
Authorization: Bearer <token>
```

Stream endpoints:

```txt
POST /api/v1/streams/{camera_id}/start
POST /api/v1/streams/{camera_id}/stop
GET  /api/v1/streams/{camera_id}/status
GET  /api/v1/streams
```

Recorder endpoints:

```txt
POST /api/v1/recorders/{camera_id}/start
POST /api/v1/recorders/{camera_id}/stop
GET  /api/v1/recorders/{camera_id}/status
GET  /api/v1/recorders
```

## Configuration

Default config file:

```txt
config/config.yaml
```

Override config path:

```powershell
$env:MEDIA_SERVICE_CONFIG="config/config.yaml"
```

Override individual values:

```powershell
$env:MEDIA_SERVICE__APP__ENVIRONMENT="production"
$env:MEDIA_SERVICE__JAVA_API__BASE_URL="https://api.example.com"
```

## Notes

The Python service must not expose raw RTSP URLs to the frontend. Logging masks RTSP credentials before writing to console or file output.
