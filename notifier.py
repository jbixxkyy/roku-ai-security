import time
import requests
from config import DISCORD_WEBHOOK_URL, NOTIFICATION_COOLDOWN


_last_notification = {}


def send_discord_alert(
    camera_name: str,
    detections: list[dict],
    image_bytes: bytes | None = None,
    event_type: str = "detection",
) -> bool:
    if not DISCORD_WEBHOOK_URL:
        return False
    now = time.time()
    key = f"{camera_name}:{event_type}"
    if now - _last_notification.get(key, 0) < NOTIFICATION_COOLDOWN:
        return False
    _last_notification[key] = now
    alert_items = [d for d in detections if d.get("alert")]
    if not alert_items and event_type == "detection":
        return False
    labels = [d["label"] for d in alert_items]
    unique_labels = list(dict.fromkeys(labels))
    if event_type == "motion":
        content = f"**Motion detected** on `{camera_name}`"
    else:
        content = f"**{', '.join(unique_labels)}** detected on `{camera_name}`"
    payload = {"username": "Roku Security AI", "content": content}
    files = {}
    if image_bytes:
        files = {"file": ("snapshot.png", image_bytes, "image/png")}
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files, timeout=10)
        return resp.status_code in (200, 204)
    except Exception:
        return False
