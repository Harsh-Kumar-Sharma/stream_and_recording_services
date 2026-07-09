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
- Playback search, date-wise listing, and safe MP4 serving APIs
- Storage writable/free-space checks and retention cleanup helper

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

## Docker

```powershell
cd python-media-service
docker compose config --quiet
docker compose up --build
```

The compose stack starts:

- `python-media-service` on port `8000`
- `mock-java-api` on host port `8081` for local integration checks
- `mediamtx` RTSP on `8554`, HLS on `8888`, WebRTC on `8889`, API on `9997`

Recording storage is mounted at:

```txt
python-media-service/storage/recordings
```

Local integration token:

```txt
Authorization: Bearer mock-valid-token
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

Playback endpoints:

```txt
GET /api/v1/playback/search?cameraId=CAM-101
GET /api/v1/playback/{camera_id}/files?date=2026-07-09
GET /api/v1/playback/{camera_id}/file?path=<encoded-path>
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
