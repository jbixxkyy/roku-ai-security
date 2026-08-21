import cv2
import numpy as np
from pathlib import Path
from config import CONFIDENCE_THRESHOLD, MOTION_SENSITIVITY, MOTION_THRESHOLD_PERCENT, ALERT_CLASSES, CLASS_LABELS

_MODEL = None
_YOLO_AVAILABLE = False

try:
    import onnxruntime as ort
    MODEL_PATH = Path(__file__).parent / "yolo11n.onnx"
    if MODEL_PATH.exists():
        _MODEL = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
        _INPUT_NAME = _MODEL.get_inputs()[0].name
        _OUTPUT_NAME = _MODEL.get_outputs()[0].name
        _YOLO_AVAILABLE = True
        print("YOLO ONNX model loaded")
    else:
        print("yolo11n.onnx not found - AI detection disabled")
except Exception as e:
    print(f"YOLO load failed: {e}")

_YOLO_CLASSES = [
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

_ALERT_CLASSES = set([
    "person", "car", "truck", "motorcycle", "bicycle",
    "dog", "cat", "bird", "bear"
])

_CLASS_LABELS = {
    "person": "Person", "car": "Vehicle", "truck": "Vehicle",
    "motorcycle": "Vehicle", "bicycle": "Vehicle",
    "dog": "Pet", "cat": "Pet", "bird": "Pet", "bear": "Animal",
}


def _letterbox(im, new_shape=(640, 640), color=(114, 114, 114)):
    shape = im.shape[:2]
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw /= 2; dh /= 2
    if shape[::-1] != new_unpad:
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return im, r, (dw, dh)


def detect_objects(frame_bytes: bytes) -> list[dict]:
    if not _YOLO_AVAILABLE or _MODEL is None:
        return []
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return []
    img, ratio, (dw, dh) = _letterbox(frame)
    img = img[:, :, ::-1].transpose(2, 0, 1)
    img = np.ascontiguousarray(img, dtype=np.float32) / 255.0
    img = img[np.newaxis, ...]
    outputs = _MODEL.run([_OUTPUT_NAME], {_INPUT_NAME: img})[0]
    outputs = outputs[0]
    detections = []
    for det in outputs:
        conf = det[4]
        if conf < CONFIDENCE_THRESHOLD:
            continue
        cls_id = int(np.argmax(det[5:]))
        cls_conf = det[5 + cls_id]
        if cls_conf < CONFIDENCE_THRESHOLD:
            continue
        cls_name = _YOLO_CLASSES[cls_id]
        x1, y1, x2, y2 = det[:4]
        x1 = (x1 - dw) / ratio
        y1 = (y1 - dh) / ratio
        x2 = (x2 - dw) / ratio
        y2 = (y2 - dh) / ratio
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        x1 = max(0, min(x1, frame.shape[1]))
        y1 = max(0, min(y1, frame.shape[0]))
        x2 = max(0, min(x2, frame.shape[1]))
        y2 = max(0, min(y2, frame.shape[0]))
        detections.append({
            "class": cls_name,
            "label": _CLASS_LABELS.get(cls_name, cls_name),
            "confidence": round(float(conf * cls_conf), 3),
            "bbox": [x1, y1, x2, y2],
            "alert": cls_name in _ALERT_CLASSES,
        })
    return detections


def detect_motion(prev_frame: np.ndarray, curr_frame: np.ndarray) -> tuple[bool, float]:
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(prev_gray, curr_gray)
    _, thresh = cv2.threshold(diff, MOTION_SENSITIVITY, 255, cv2.THRESH_BINARY)
    non_zero = cv2.countNonZero(thresh)
    total = thresh.size
    change_pct = (non_zero / total) * 100
    return change_pct > MOTION_THRESHOLD_PERCENT, round(change_pct, 2)


def frame_bytes_to_ndarray(frame_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(frame_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


def annotate_frame(frame_bytes: bytes, detections: list[dict]) -> bytes:
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return frame_bytes
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        color = (0, 0, 255) if det["alert"] else (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f'{det["label"]} {det["confidence"]:.0%}'
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(frame, (x1, y1 - h - 10), (x1 + w, y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    _, buf = cv2.imencode(".png", frame)
    return buf.tobytes()