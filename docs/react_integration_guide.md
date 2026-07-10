# React Integration Guide: Python Media Service

## 1. Purpose

This document is for the React developer integrating live stream, recording, and playback features with the Python FastAPI media service.

React should call the Python service directly for:

- Live stream start/stop/status
- Recording start/stop/status
- Playback search and MP4 file playback

React should not call RTSP URLs directly. Python keeps raw RTSP internal and returns browser-safe HLS or MP4 playback URLs.

---

## 2. Local Base URLs

Python API:

```txt
http://localhost:8000
```

MediaMTX HLS output:

```txt
http://localhost:8888
```

Example HLS stream returned by Python:

```txt
http://localhost:8888/cam-CAM-02/index.m3u8
```

---

## 3. Auth Header

All media APIs except health/docs require:

```txt
Authorization: Bearer <token>
```

Current development behavior:

```txt
Any valid Bearer header format is accepted.
Java auth validation is temporarily hardcoded to pass in Python.
```

Example:

```http
Authorization: Bearer dev-token
```

Important production note:

```txt
Java session validation must be restored before production.
```

---

## 4. Camera ID

Use the Java `customDeviceId` as the React camera ID.

Java stream-device sample:

```json
{
  "deviceId": 2,
  "customDeviceId": "CAM-02\n",
  "ipAddress": "192.168.38\n",
  "username": "User1",
  "password": "PassWd",
  "portNumber": 765,
  "rtspUrl": "rtsp://192.168.2"
}
```

React should call Python with:

```txt
CAM-02
```

Python trims newline/space characters internally and also supports matching by numeric `deviceId`, but React should prefer `customDeviceId`.

---

## 5. Error Response Shape

Common error response:

```json
{
  "status": false,
  "message": "Error message",
  "errorCode": "ERROR_CODE",
  "details": {}
}
```

Common errors:

```txt
401 AUTH_TOKEN_MISSING
404 CAMERA_NOT_FOUND
409 RECORDING_ALREADY_RUNNING
429 MAX_LIVE_STREAMS_REACHED
429 MAX_RECORDING_WORKERS_REACHED
503 RECORDING_DISABLED
507 STORAGE_NOT_AVAILABLE
```

---

## 6. Health Check

Request:

```http
GET http://localhost:8000/api/v1/health
```

No auth header required.

Use this to check if Python is running before enabling media UI controls.

---

## 7. Live Streaming

### Start Stream

Request:

```http
POST http://localhost:8000/api/v1/streams/CAM-02/start
Authorization: Bearer dev-token
```

Success response:

```json
{
  "status": true,
  "cameraId": "CAM-02",
  "cameraName": "CAM-02",
  "streamStatus": "started",
  "streamType": "hls",
  "streamUrl": "http://localhost:8888/cam-CAM-02/index.m3u8",
  "startedAt": "2026-07-10T08:30:00.000000+00:00",
  "lastError": null
}
```

React should use `streamUrl` in an HLS-capable player.

### Stream Status

Request:

```http
GET http://localhost:8000/api/v1/streams/CAM-02/status
Authorization: Bearer dev-token
```

Inactive response:

```json
{
  "status": true,
  "cameraId": "CAM-02",
  "streamStatus": "inactive",
  "streamType": "hls",
  "streamUrl": null,
  "lastError": null
}
```

### Stop Stream

Request:

```http
POST http://localhost:8000/api/v1/streams/CAM-02/stop
Authorization: Bearer dev-token
```

Response:

```json
{
  "status": true,
  "cameraId": "CAM-02",
  "streamStatus": "stopped"
}
```

### List Streams

Request:

```http
GET http://localhost:8000/api/v1/streams
Authorization: Bearer dev-token
```

Response:

```json
{
  "status": true,
  "streams": [],
  "count": 0
}
```

---

## 8. HLS Playback In React

Browsers do not all play `.m3u8` directly. Use `hls.js` for Chrome/Edge/Firefox.

Example:

```tsx
import Hls from "hls.js";
import { useEffect, useRef } from "react";

type Props = {
  streamUrl: string | null;
};

export function HlsVideo({ streamUrl }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !streamUrl) return;

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = streamUrl;
      return;
    }

    if (!Hls.isSupported()) return;

    const hls = new Hls();
    hls.loadSource(streamUrl);
    hls.attachMedia(video);

    return () => hls.destroy();
  }, [streamUrl]);

  return <video ref={videoRef} controls autoPlay muted playsInline style={{ width: "100%" }} />;
}
```

---

## 9. Recording

Recording can be enabled/disabled by Python environment:

```txt
MEDIA_SERVICE__RECORDING__ENABLED=true
MEDIA_SERVICE__RECORDING__ENABLED=false
```

If recording is disabled, React receives:

```json
{
  "status": false,
  "message": "Recording service is disabled",
  "errorCode": "RECORDING_DISABLED",
  "details": {}
}
```

### Start Recording

Request:

```http
POST http://localhost:8000/api/v1/recorders/CAM-02/start
Authorization: Bearer dev-token
```

Success response:

```json
{
  "status": true,
  "cameraId": "CAM-02",
  "cameraName": "CAM-02",
  "pid": 12345,
  "recordingStatus": "recording",
  "startedAt": "2026-07-10T08:30:00.000000+00:00",
  "stoppedAt": null,
  "restartCount": 0,
  "latestOutputFile": null,
  "storagePath": "storage/recordings/CAM-02/2026-07-10/14",
  "lastError": null
}
```

### Recording Status

Request:

```http
GET http://localhost:8000/api/v1/recorders/CAM-02/status
Authorization: Bearer dev-token
```

Not running response:

```json
{
  "status": true,
  "cameraId": "CAM-02",
  "pid": null,
  "recordingStatus": "not_running",
  "restartCount": 0,
  "latestOutputFile": null,
  "lastError": null
}
```

### Stop Recording

Request:

```http
POST http://localhost:8000/api/v1/recorders/CAM-02/stop
Authorization: Bearer dev-token
```

Response:

```json
{
  "status": true,
  "cameraId": "CAM-02",
  "recordingStatus": "stopped",
  "pid": null
}
```

### List Recorders

Request:

```http
GET http://localhost:8000/api/v1/recorders
Authorization: Bearer dev-token
```

Response:

```json
{
  "status": true,
  "recordingEnabled": true,
  "recorders": [],
  "count": 0
}
```

---

## 10. Playback

### Search Playback Files

Request:

```http
GET http://localhost:8000/api/v1/playback/search?cameraId=CAM-02
Authorization: Bearer dev-token
```

Optional time range:

```http
GET http://localhost:8000/api/v1/playback/search?cameraId=CAM-02&from=2026-07-10T10:00:00&to=2026-07-10T11:00:00
Authorization: Bearer dev-token
```

Response:

```json
{
  "status": true,
  "cameraId": "CAM-02",
  "files": [
    {
      "fileName": "CAM-02_20260710_103000.mp4",
      "cameraId": "CAM-02",
      "sizeBytes": 215911,
      "modifiedAt": "2026-07-10T10:30:00",
      "playbackUrl": "/api/v1/playback/CAM-02/file?path=encoded-token",
      "token": "encoded-token"
    }
  ],
  "count": 1
}
```

If `playbackUrl` is relative, React should prefix it with the Python API base URL:

```ts
const mediaApiBaseUrl = "http://localhost:8000";
const absolutePlaybackUrl = `${mediaApiBaseUrl}${file.playbackUrl}`;
```

### List Files For Date

Request:

```http
GET http://localhost:8000/api/v1/playback/CAM-02/files?date=2026-07-10
Authorization: Bearer dev-token
```

### Play MP4 File

Use the `playbackUrl` returned from search/list in a normal video element:

```tsx
<video src={absolutePlaybackUrl} controls style={{ width: "100%" }} />
```

Do not build file-system paths in React. Always use the returned `playbackUrl` or `token`.

---

## 11. Suggested React API Helper

```ts
const MEDIA_API_BASE_URL = "http://localhost:8000";

async function mediaRequest<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${MEDIA_API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init.headers || {}),
    },
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok || data?.status === false) {
    throw new Error(data?.message || `Media API failed with ${response.status}`);
  }

  return data as T;
}

export function startStream(cameraId: string, token: string) {
  return mediaRequest(`/api/v1/streams/${encodeURIComponent(cameraId)}/start`, token, {
    method: "POST",
  });
}

export function stopStream(cameraId: string, token: string) {
  return mediaRequest(`/api/v1/streams/${encodeURIComponent(cameraId)}/stop`, token, {
    method: "POST",
  });
}

export function startRecording(cameraId: string, token: string) {
  return mediaRequest(`/api/v1/recorders/${encodeURIComponent(cameraId)}/start`, token, {
    method: "POST",
  });
}

export function stopRecording(cameraId: string, token: string) {
  return mediaRequest(`/api/v1/recorders/${encodeURIComponent(cameraId)}/stop`, token, {
    method: "POST",
  });
}

export function searchPlayback(cameraId: string, token: string) {
  return mediaRequest(`/api/v1/playback/search?cameraId=${encodeURIComponent(cameraId)}`, token);
}
```

---

## 12. Integration Checklist

- Use Python API base URL `http://localhost:8000`.
- Send `Authorization: Bearer <token>` on all protected media APIs.
- Use Java `customDeviceId` as `camera_id`, for example `CAM-02`.
- Use `streamUrl` from start-stream response for HLS playback.
- Use `hls.js` for `.m3u8` playback in Chrome/Edge/Firefox.
- Use returned `playbackUrl` for MP4 playback.
- Handle `RECORDING_DISABLED` by disabling/hiding recording controls.
- Do not show raw RTSP URLs in React.
- Do not construct recording file-system paths in React.
- Remember auth is temporarily hardcoded to pass and must be restored before production.

