import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
ROKU_VIEWER_DIR = BASE_DIR.parent / "roku-camera-viewer"
STORAGE_STATE = ROKU_VIEWER_DIR / "storage_state.json"
SNAPSHOTS_DIR = BASE_DIR / "snapshots"
RECORDINGS_DIR = BASE_DIR / "recordings"
DATABASE_PATH = BASE_DIR / "events.db"
FRAMES_DIR = ROKU_VIEWER_DIR / "frames"

SNAPSHOTS_DIR.mkdir(exist_ok=True)
RECORDINGS_DIR.mkdir(exist_ok=True)

CAMERAS_URL = "https://cameras.roku.com/"
LEAVES_API = "/smarthome/api/v1/leaves"
STREAMS_API = "/smarthome/api/v1/leaves/{device_id}/streams?leafType=device"
SIGNALING_API = "/smarthome/api/v1/signaling"

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
NOTIFICATION_COOLDOWN = int(os.getenv("NOTIFICATION_COOLDOWN", "30"))

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
MOTION_SENSITIVITY = int(os.getenv("MOTION_SENSITIVITY", "25"))
MOTION_THRESHOLD_PERCENT = float(os.getenv("MOTION_THRESHOLD_PERCENT", "1.5"))
CAPTURE_INTERVAL = float(os.getenv("CAPTURE_INTERVAL", "2.0"))

AI_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep",
    "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
    "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
    "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
    "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv",
    "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
    "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush"
]

ALERT_CLASSES = [
    "person", "car", "truck", "motorcycle", "bicycle",
    "dog", "cat", "bird", "bear"
]

CLASS_LABELS = {
    "person": "Person",
    "car": "Vehicle",
    "truck": "Vehicle",
    "motorcycle": "Vehicle",
    "bicycle": "Vehicle",
    "dog": "Pet",
    "cat": "Pet",
    "bird": "Pet",
    "bear": "Animal",
}
