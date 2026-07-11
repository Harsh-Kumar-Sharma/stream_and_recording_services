# Small Config And Smooth Playback Runbook

This runbook is for testing one or two cameras on a small local machine.

## Small Runtime Settings

Use small limits while debugging:

```env
MEDIA_SERVICE__WORKER__MAX_LIVE_STREAMS=2
MEDIA_SERVICE__WORKER__MAX_RECORDING_WORKERS=1
MEDIA_SERVICE__RECORDING__ENABLED=false
MEDIA_SERVICE__RECORDING__SEGMENT_DURATION_SECONDS=30
MEDIA_SERVICE__RECORDING__MAX_RESTART_ATTEMPTS=1
MEDIA_SERVICE__RECORDING__RESTART_DELAY_SECONDS=3
```

Enable recording only after live playback is stable:

```env
MEDIA_SERVICE__RECORDING__ENABLED=true
```

## Start Order

From `python-media-service`:

```powershell
docker compose up -d mediamtx mock-java python-media-service
curl.exe --noproxy "*" http://localhost:8000/api/v1/health
```

Then start a stream:

```powershell
curl.exe --noproxy "*" -X POST `
  -H "Authorization: Bearer mock-valid-token" `
  http://localhost:8000/api/v1/streams/CAM-101/start
```

Check MediaMTX path:

```powershell
curl.exe --noproxy "*" http://localhost:9997/v3/paths/list
```

If `itemCount` is `0`, MediaMTX has no active path and playback will show `stream not found`.

## HLS Vs WebRTC

Use HLS when stability is more important than delay:

```txt
http://192.168.0.103:8888/cam-CAM-02/index.m3u8
```

For VLC compatibility, MediaMTX should keep the HLS muxer alive:

```yaml
hlsAlwaysRemux: yes
hlsVariant: mpegts
```

Use WebRTC for real-time viewing:

```txt
http://192.168.0.103:8889/cam-CAM-02/
```

Do not open `/whep` directly in a browser. `/whep` is for a custom WHEP WebRTC player.

## If Playback Is Delayed Or Not Smooth

HLS is not truly real time. Even low-latency HLS can have a few seconds of delay.

For smooth one-camera testing, use the camera substream when possible:

```txt
Resolution: 720p or lower
FPS: 10 to 15
Bitrate: 512 Kbps to 2 Mbps
Encoding: H.264
GOP/keyframe interval: 1 second, or same number as FPS
B-frames: disabled if supported
Audio: disabled for testing
```

If WebRTC is choppy, check:

```txt
1. Windows Firewall allows TCP 8889 and UDP 8189.
2. Browser opens /cam-CAM-02/, not /cam-CAM-02/whep directly.
3. MediaMTX path exists in /v3/paths/list.
4. Docker Desktop CPU is not high.
5. Camera RTSP URL points to a low-bitrate substream.
```

For LAN cameras, `rtsp_transport: tcp` is usually smoother under packet loss. If delay is too high and the network is clean, test `rtsp_transport: udp`.
