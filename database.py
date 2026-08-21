import sqlite3
import time
import json
from pathlib import Path
from config import DATABASE_PATH


def init_db():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                detections TEXT,
                snapshot_path TEXT,
                timestamp REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_camera ON events(camera_name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)
        """)
        conn.commit()


def log_event(
    camera_name: str,
    event_type: str,
    detections: list[dict] | None = None,
    snapshot_path: str | None = None,
) -> int:
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO events (camera_name, event_type, detections, snapshot_path, timestamp) VALUES (?, ?, ?, ?, ?)",
            (camera_name, event_type, json.dumps(detections or []), snapshot_path, time.time()),
        )
        conn.commit()
        return cursor.lastrowid


def get_events(
    camera_name: str | None = None,
    event_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    query = "SELECT * FROM events WHERE 1=1"
    params = []
    if camera_name:
        query += " AND camera_name = ?"
        params.append(camera_name)
    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_event_stats() -> dict:
    with sqlite3.connect(DATABASE_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        by_type = dict(conn.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type").fetchall())
        by_camera = dict(conn.execute("SELECT camera_name, COUNT(*) FROM events GROUP BY camera_name").fetchall())
        today_start = time.time() - (time.time() % 86400)
        today_count = conn.execute("SELECT COUNT(*) FROM events WHERE timestamp > ?", (today_start,)).fetchone()[0]
    return {
        "total_events": total,
        "today_events": today_count,
        "by_type": by_type,
        "by_camera": by_camera,
    }


init_db()
