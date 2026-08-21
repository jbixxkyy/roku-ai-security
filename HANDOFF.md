# Roku Smart Home Camera - AI Security System Handoff

## Current Status: Two Separate Projects

### 1. `roku-camera-viewer` ✅ COMPLETE
**Location:** `D:\hardrive gaming pc\roku-camera-viewer\`

Reverse-engineered Roku Smart Home camera streaming. Fully working.

**What works:**
- `login.py` - Interactive Roku login (saves `storage_state.json`)
- `snap.py` - Headless frame capture via WebRTC (1920x1080 PNGs)
- API endpoints documented in README

**Test it:**
```bash
cd D:\hardrive gaming pc\roku-camera-viewer
uv run python login.py      # One-time login
uv run python snap.py       # Capture frames → frames/
```

---

### 2. `roku-ai-security` ⚠️ NEEDS COMPLETION
**Location:** `D:\hardrive gaming pc\roku-ai-security\`

AI-powered security dashboard that builds on the viewer.

**Structure:**
```
roku-ai-security/
├── app.py              # FastAPI + uvicorn web dashboard
├── camera.py           # Reuses roku-camera-viewer's capture logic
├── detector.py         # ONNX Runtime YOLO11 + motion detection
├── notifier.py         # Discord webhook alerts
├── database.py         # SQLite event storage
├── config.py           # All settings
├── index.html          # Web UI
├── pyproject.toml
└── .venv/              # Python 3.13, ONNX Runtime, OpenCV, FastAPI
```

**What works:**
- All Python modules written and importable
- Dependencies installed (ONNX Runtime, OpenCV, FastAPI, uvicorn, playwright)
- Web dashboard template ready

**BLOCKERS:**

| Issue | Details |
|-------|---------|
| **YOLO ONNX model missing** | Need `yolo11n.onnx` in project root. Download failed due to GitHub connectivity. |
| **Playwright browser launch hangs** | `sync_playwright()` times out in venv. Works in `roku-camera-viewer` venv (Python 3.14) but not here (Python 3.13). Likely path/permission issue. |

---

## What Needs to Be Done

### Priority 1: Fix Playwright in `roku-ai-security`
```bash
# The venv is at .venv (Python 3.13)
# Playwright chromium is at %USERPROFILE%\AppData\Local\ms-playwright\chromium-1234
# Check if playwright can find the browser
```

**Root cause:** The `roku-camera-viewer` uses Python 3.14 venv and works perfectly. The `roku-ai-security` uses Python 3.13 venv and Playwright hangs on import/launch. May need to:
- Set `PLAYWRIGHT_BROWSERS_PATH` env var
- Or use the same Python 3.14 venv (but torch doesn't work on 3.14)
- Or copy the browser binary locally

### Priority 2: Get YOLO ONNX Model
```bash
# Download yolo11n.onnx (2.6MB) from:
# https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11n.onnx
# Place in roku-ai-security/
```

### Priority 3: Test Full Pipeline
```bash
cd D:\hardrive gaming pc\roku-ai-security
# 1. Copy storage_state.json from roku-camera-viewer (or re-login)
cp ../roku-camera-viewer/storage_state.json .

# 2. Run dashboard
uv run uvicorn app:app --host 0.0.0.0 --port 8000

# 3. Open http://localhost:8000
```

---

## Key Files to Review

### `camera.py` - Capture Logic
Reuses the exact working logic from `roku-camera-viewer`. Uses Playwright headless to:
1. Load `storage_state.json` 
2. Navigate to `cameras.roku.com`
3. Wait for WebRTC `<video>` element
4. Screenshot the video element

### `detector.py` - AI + Motion
- **YOLO via ONNX Runtime** (if `yolo11n.onnx` exists)
- **Motion detection** via OpenCV frame differencing (works without YOLO)
- Falls back gracefully if model missing

### `app.py` - FastAPI Dashboard
- `/` - Web UI with live feed, stats, events
- `/api/stream` - Latest annotated frame (PNG)
- `/api/status` - Camera status + detection results
- `/api/events` - Event history from SQLite
- `/api/snapshot` - Download current frame
- Background `capture_loop()` runs every 2s

### `config.py` - All Tunables
Environment variables (see `.env.example`):
- `DISCORD_WEBHOOK_URL` - For alerts
- `CONFIDENCE_THRESHOLD` - YOLO confidence (0.5)
- `MOTION_SENSITIVITY` - OpenCV threshold (25)
- `MOTION_THRESHOLD_PERCENT` - % changed pixels (1.5%)
- `CAPTURE_INTERVAL` - Seconds between frames (2.0)

---

## Quick Test Plan

1. **Verify Playwright works:**
   ```bash
   cd roku-ai-security
   uv run python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); print(b.version); b.close(); p.stop()"
   ```

2. **Add YOLO model** (download and place in root)

3. **Copy session:**
   ```bash
   cp ../roku-camera-viewer/storage_state.json .
   ```

4. **Run:**
   ```bash
   uv run uvicorn app:app --host 0.0.0.0 --port 8000
   ```

5. **Open browser:** http://localhost:8000

---

## Architecture Notes

- **No PyTorch** - Uses ONNX Runtime (works on Python 3.13)
- **Single camera** - Currently targets the first online camera ("Camera" at 192.168.1.156)
- **Event types:** `motion` (pixel diff) + `detection` (YOLO alerts)
- **Discord alerts** - Cooldown 30s per camera/event-type
- **Storage:** SQLite + PNG snapshots in `snapshots/`

---

## Contact / Context

- **Roku cameras:** 2x SCS11-00X (rebranded Wyze)
  - "Camera" - Online, 192.168.1.156
  - "3d printer" - Often offline, 192.168.1.161
- **Auth:** Roku account with 2FA (no "remember me" → session expires)
- **Streaming:** WebRTC via `/smarthome/api/v1/signaling` (SDP offer/answer)

The core reverse-engineering is done and working in `roku-camera-viewer`. The AI layer just needs the two blockers above resolved.