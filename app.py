import asyncio
import time
import base64
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from config import SNAPSHOTS_DIR, CAPTURE_INTERVAL, CONFIDENCE_THRESHOLD
from camera import capture_frame
from detector import detect_objects, detect_motion, frame_bytes_to_ndarray, annotate_frame
from notifier import send_discord_alert
from database import log_event, get_events, get_event_stats


_capture_task = None
_latest_frames: dict[str, bytes] = {}
_latest_annotated: dict[str, bytes] = {}
_latest_detections: dict[str, list[dict]] = {}
_camera_status: dict[str, dict] = {}
_prev_frames: dict[str, object] = {}


async def capture_loop():
    while True:
        try:
            frame_bytes = await asyncio.get_event_loop().run_in_executor(None, capture_frame)
            if frame_bytes is None:
                await asyncio.sleep(CAPTURE_INTERVAL)
                continue
            ts = time.time()
            detections = await asyncio.get_event_loop().run_in_executor(
                None, detect_objects, frame_bytes
            )
            _latest_frames["main"] = frame_bytes
            _latest_detections["main"] = detections
            annotated = await asyncio.get_event_loop().run_in_executor(
                None, annotate_frame, frame_bytes, detections
            )
            _latest_annotated["main"] = annotated
            curr_nd = await asyncio.get_event_loop().run_in_executor(
                None, frame_bytes_to_ndarray, frame_bytes
            )
            if "main" in _prev_frames:
                motion, pct = await asyncio.get_event_loop().run_in_executor(
                    None, detect_motion, _prev_frames["main"], curr_nd
                )
                if motion:
                    save_path = str(SNAPSHOTS_DIR / f"motion_{int(ts)}.png")
                    Path(save_path).write_bytes(frame_bytes)
                    log_event("Camera", "motion", snapshot_path=save_path)
                    send_discord_alert("Camera", [], frame_bytes, "motion")
            _prev_frames["main"] = curr_nd
            alert_dets = [d for d in detections if d.get("alert")]
            if alert_dets:
                save_path = str(SNAPSHOTS_DIR / f"detect_{int(ts)}.png")
                Path(save_path).write_bytes(frame_bytes)
                log_event("Camera", "detection", detections, save_path)
                send_discord_alert("Camera", detections, frame_bytes, "detection")
            _camera_status["main"] = {
                "online": True,
                "last_frame": ts,
                "detection_count": len(detections),
                "alerts": len(alert_dets),
            }
        except Exception as e:
            _camera_status["main"] = {"online": False, "error": str(e)}
        await asyncio.sleep(CAPTURE_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _capture_task
    _capture_task = asyncio.create_task(capture_loop())
    yield
    if _capture_task:
        _capture_task.cancel()


app = FastAPI(title="Roku AI Security", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).parent / "index.html"
    return HTMLResponse(html_path.read_text())


@app.get("/api/status")
async def api_status():
    stats = get_event_stats()
    return JSONResponse({
        "cameras": _camera_status,
        "stats": stats,
        "latest_detections": _latest_detections,
    })


@app.get("/api/stream")
async def api_stream():
    frame = _latest_annotated.get("main") or _latest_frames.get("main")
    if not frame:
        return JSONResponse({"error": "no frame"}, status_code=503)
    return FileResponse(
        __import__("io").BytesIO(frame),
        media_type="image/png",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/api/snapshot")
async def api_snapshot():
    frame = _latest_frames.get("main")
    if not frame:
        return JSONResponse({"error": "no frame"}, status_code=503)
    ts = int(time.time())
    path = SNAPSHOTS_DIR / f"snapshot_{ts}.png"
    path.write_bytes(frame)
    return FileResponse(
        __import__("io").BytesIO(frame),
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=snapshot_{ts}.png"},
    )


@app.get("/api/events")
async def api_events(camera: str = None, event_type: str = None, limit: int = 50):
    events = get_events(camera, event_type, limit)
    return JSONResponse(events)


@app.get("/api/detections")
async def api_detections():
    return JSONResponse(_latest_detections)
