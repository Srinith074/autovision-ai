"""
AutoVision AI - SQLite Database Interface and Analytics Engine
Provides persistent storage for detection sessions, tracked vehicle events, and detailed telemetry.
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.app.core.config import DATABASE_PATH

def get_db():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and indexes if they do not exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detection_sessions (
        id TEXT PRIMARY KEY,
        source_type TEXT NOT NULL,
        source_name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL,
        total_vehicles INTEGER DEFAULT 0,
        car_count INTEGER DEFAULT 0,
        truck_count INTEGER DEFAULT 0,
        bus_count INTEGER DEFAULT 0,
        motorcycle_count INTEGER DEFAULT 0,
        bicycle_count INTEGER DEFAULT 0,
        avg_speed REAL DEFAULT 0.0,
        duration_seconds REAL DEFAULT 0.0,
        fps REAL DEFAULT 0.0,
        total_frames INTEGER DEFAULT 0,
        processed_frames INTEGER DEFAULT 0,
        model_name TEXT DEFAULT 'yolov8n.pt',
        conf_threshold REAL DEFAULT 0.30,
        output_video_path TEXT DEFAULT '',
        report_csv_path TEXT DEFAULT '',
        is_calibrated INTEGER DEFAULT 0,
        meters_per_pixel REAL DEFAULT 0.05
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicle_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        track_id INTEGER NOT NULL,
        vehicle_class TEXT NOT NULL,
        confidence REAL NOT NULL,
        first_frame INTEGER NOT NULL,
        last_frame INTEGER NOT NULL,
        first_seen_ts TEXT,
        last_seen_ts TEXT,
        direction TEXT DEFAULT 'Southbound (Down)',
        speed_kmh REAL,
        is_counted INTEGER DEFAULT 1,
        lane_id TEXT DEFAULT 'Lane 1',
        snapshot_path TEXT DEFAULT '',
        trajectory_json TEXT DEFAULT '[]',
        FOREIGN KEY (session_id) REFERENCES detection_sessions (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detection_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        frame_number INTEGER NOT NULL,
        timestamp_sec REAL NOT NULL,
        track_id INTEGER NOT NULL,
        vehicle_class TEXT NOT NULL,
        confidence REAL NOT NULL,
        bbox_x1 REAL NOT NULL,
        bbox_y1 REAL NOT NULL,
        bbox_x2 REAL NOT NULL,
        bbox_y2 REAL NOT NULL,
        direction TEXT,
        speed_kmh REAL,
        FOREIGN KEY (session_id) REFERENCES detection_sessions (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_session ON detection_records(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON vehicle_events(session_id);")
    conn.commit()
    conn.close()

# Session Management
def create_session(session_data: Dict[str, Any]) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO detection_sessions (
        id, source_type, source_name, created_at, status,
        total_vehicles, car_count, truck_count, bus_count, motorcycle_count, bicycle_count,
        avg_speed, duration_seconds, fps, total_frames, processed_frames,
        model_name, conf_threshold, output_video_path, report_csv_path,
        is_calibrated, meters_per_pixel
    ) VALUES (
        :id, :source_type, :source_name, :created_at, :status,
        :total_vehicles, :car_count, :truck_count, :bus_count, :motorcycle_count, :bicycle_count,
        :avg_speed, :duration_seconds, :fps, :total_frames, :processed_frames,
        :model_name, :conf_threshold, :output_video_path, :report_csv_path,
        :is_calibrated, :meters_per_pixel
    )
    """, session_data)
    conn.commit()
    conn.close()
    return session_data["id"]

def update_session(session_id: str, updates: Dict[str, Any]):
    conn = get_db()
    cursor = conn.cursor()
    fields = [f"{k} = :{k}" for k in updates.keys()]
    query = f"UPDATE detection_sessions SET {', '.join(fields)} WHERE id = :session_id"
    params = {**updates, "session_id": session_id}
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detection_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def list_sessions(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM detection_sessions
        ORDER BY datetime(created_at) DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_session(session_id: str) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detection_records WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM vehicle_events WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM detection_sessions WHERE id = ?", (session_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# Vehicle Events & Telemetry Records
def insert_vehicle_event(event: Dict[str, Any]):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO vehicle_events (
        session_id, track_id, vehicle_class, confidence,
        first_frame, last_frame, first_seen_ts, last_seen_ts,
        direction, speed_kmh, is_counted, lane_id, snapshot_path, trajectory_json
    ) VALUES (
        :session_id, :track_id, :vehicle_class, :confidence,
        :first_frame, :last_frame, :first_seen_ts, :last_seen_ts,
        :direction, :speed_kmh, :is_counted, :lane_id, :snapshot_path, :trajectory_json
    )
    """, event)
    conn.commit()
    conn.close()

def insert_detection_records_batch(records: List[Dict[str, Any]]):
    if not records:
        return
    conn = get_db()
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO detection_records (
        session_id, frame_number, timestamp_sec, track_id,
        vehicle_class, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
        direction, speed_kmh
    ) VALUES (
        :session_id, :frame_number, :timestamp_sec, :track_id,
        :vehicle_class, :confidence, :bbox_x1, :bbox_y1, :bbox_x2, :bbox_y2,
        :direction, :speed_kmh
    )
    """, records)
    conn.commit()
    conn.close()

def get_session_events(session_id: str) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicle_events WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["trajectory"] = json.loads(d.get("trajectory_json") or "[]")
        except Exception:
            d["trajectory"] = []
        result.append(d)
    return result

def get_session_records(session_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detection_records WHERE session_id = ? ORDER BY frame_number ASC, track_id ASC LIMIT ?", (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Analytics Aggregation Engine
def get_analytics_overview() -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        COUNT(*) as total_sessions,
        COALESCE(SUM(total_vehicles), 0) as total_vehicles,
        COALESCE(SUM(car_count), 0) as total_cars,
        COALESCE(SUM(truck_count), 0) as total_trucks,
        COALESCE(SUM(bus_count), 0) as total_buses,
        COALESCE(SUM(motorcycle_count), 0) as total_motorcycles,
        COALESCE(SUM(bicycle_count), 0) as total_bicycles,
        COALESCE(AVG(CASE WHEN is_calibrated = 1 AND avg_speed > 0 THEN avg_speed END), 0.0) as overall_avg_speed,
        COALESCE(AVG(fps), 0.0) as overall_avg_fps
    FROM detection_sessions
    WHERE status = 'completed'
    """)
    totals = dict(cursor.fetchone())

    # Category distribution
    categories = [
        {"name": "Car", "count": totals["total_cars"], "color": "#0080ff"},
        {"name": "Truck", "count": totals["total_trucks"], "color": "#ffc800"},
        {"name": "Bus", "count": totals["total_buses"], "color": "#80ff00"},
        {"name": "Motorcycle", "count": totals["total_motorcycles"], "color": "#c800ff"},
        {"name": "Bicycle", "count": totals["total_bicycles"], "color": "#ffff00"},
    ]

    # Direction breakdown
    cursor.execute("""
    SELECT direction, COUNT(*) as count
    FROM vehicle_events
    WHERE direction IS NOT NULL AND direction != ''
    GROUP BY direction
    """)
    directions = [{"direction": row["direction"], "count": row["count"]} for row in cursor.fetchall()]

    # Hourly distribution based on session created_at
    cursor.execute("""
    SELECT strftime('%H:00', created_at) as hour, SUM(total_vehicles) as count
    FROM detection_sessions
    WHERE status = 'completed'
    GROUP BY hour
    ORDER BY hour ASC
    """)
    hourly = [{"hour": row["hour"], "vehicles": row["count"]} for row in cursor.fetchall()]

    # Recent completed sessions
    cursor.execute("""
    SELECT id, source_name, created_at, total_vehicles, avg_speed, is_calibrated, duration_seconds
    FROM detection_sessions
    ORDER BY datetime(created_at) DESC
    LIMIT 5
    """)
    recent_sessions = [dict(r) for r in cursor.fetchall()]

    # Latest detected vehicle snapshots
    cursor.execute("""
    SELECT track_id, vehicle_class, confidence, direction, speed_kmh, snapshot_path, first_seen_ts
    FROM vehicle_events
    WHERE snapshot_path IS NOT NULL AND snapshot_path != ''
    ORDER BY id DESC
    LIMIT 8
    """)
    latest_vehicles = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "summary": totals,
        "categories": categories,
        "directions": directions,
        "hourly_activity": hourly,
        "recent_sessions": recent_sessions,
        "latest_vehicles": latest_vehicles
    }
