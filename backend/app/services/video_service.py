"""
AutoVision AI - Video Processing Service
Executes deep learning video inference, tracking, annotated output generation,
snapshot harvesting, and CSV report creation.
"""
import os
import cv2
import csv
import json
import time
import uuid
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import numpy as np

from app.core.config import (
    VIDEOS_DIR, SNAPSHOTS_DIR, REPORTS_DIR, BASE_DIR
)
from app.detection.yolo_detector import YOLODetector
from app.tracking.tracker import TrafficTracker
from app.database.database import (
    create_session, update_session, insert_vehicle_event, insert_detection_records_batch
)

# In-memory session registry for real-time progress and cancellation
active_sessions: Dict[str, Dict[str, Any]] = {}
stop_signals: Dict[str, bool] = {}

class VideoProcessingService:
    @staticmethod
    def start_processing_job(
        video_path: str,
        source_name: str,
        model_name: str = "yolov8n.pt",
        conf_threshold: float = 0.30,
        iou_threshold: float = 0.45,
        selected_classes: Optional[list] = None,
        enable_tracking: bool = True,
        enable_counting: bool = True,
        counting_line_ratio: float = 0.55,
        is_calibrated: bool = False,
        meters_per_pixel: float = 0.05,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> str:
        session_id = f"sess_{uuid.uuid4().hex[:10]}"

        # Initialize session in database
        initial_data = {
            "id": session_id,
            "source_type": "video",
            "source_name": source_name,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "processing",
            "total_vehicles": 0,
            "car_count": 0,
            "truck_count": 0,
            "bus_count": 0,
            "motorcycle_count": 0,
            "bicycle_count": 0,
            "avg_speed": 0.0,
            "duration_seconds": 0.0,
            "fps": 0.0,
            "total_frames": 0,
            "processed_frames": 0,
            "model_name": model_name,
            "conf_threshold": conf_threshold,
            "output_video_path": "",
            "report_csv_path": "",
            "is_calibrated": 1 if is_calibrated else 0,
            "meters_per_pixel": meters_per_pixel
        }
        create_session(initial_data)

        # In-memory tracking state
        active_sessions[session_id] = {
            "session_id": session_id,
            "status": "processing",
            "progress_percent": 0.0,
            "current_fps": 0.0,
            "processed_frames": 0,
            "total_frames": 0,
            "total_vehicles": 0,
            "category_counts": {"car": 0, "truck": 0, "bus": 0, "motorcycle": 0, "bicycle": 0},
            "avg_speed": None,
            "is_calibrated": is_calibrated,
            "output_video_url": None,
            "report_csv_url": None,
            "error": None
        }
        stop_signals[session_id] = False

        # Start processing thread
        thread = threading.Thread(
            target=VideoProcessingService._worker_process,
            args=(
                session_id, video_path, source_name, model_name,
                conf_threshold, iou_threshold, selected_classes,
                enable_tracking, enable_counting, counting_line_ratio,
                is_calibrated, meters_per_pixel, progress_callback
            ),
            daemon=True
        )
        thread.start()

        return session_id

    @staticmethod
    def stop_processing_job(session_id: str) -> bool:
        if session_id in stop_signals:
            stop_signals[session_id] = True
            if session_id in active_sessions:
                active_sessions[session_id]["status"] = "stopping"
            return True
        return False

    @staticmethod
    def get_session_status(session_id: str) -> Optional[Dict[str, Any]]:
        return active_sessions.get(session_id)

    @staticmethod
    def _worker_process(
        session_id: str,
        video_path: str,
        source_name: str,
        model_name: str,
        conf_threshold: float,
        iou_threshold: float,
        selected_classes: Optional[list],
        enable_tracking: bool,
        enable_counting: bool,
        counting_line_ratio: float,
        is_calibrated: bool,
        meters_per_pixel: float,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]]
    ):
        cap = None
        writer = None
        try:
            detector = YOLODetector.get_detector(model_name)
            tracker = TrafficTracker(
                counting_line_ratio=counting_line_ratio,
                is_calibrated=is_calibrated,
                meters_per_pixel=meters_per_pixel
            )

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise RuntimeError(f"Could not open video file: {video_path}")

            frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            source_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

            # Prepare Output Video Path
            out_filename = f"{session_id}_annotated.mp4"
            out_path = VIDEOS_DIR / out_filename

            # Codec: try mp4v which is universally supported on Windows OpenCV
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(str(out_path), fourcc, source_fps, (frame_w, frame_h))

            # Prepare CSV report
            csv_filename = f"{session_id}_report.csv"
            csv_path = REPORTS_DIR / csv_filename

            update_session(session_id, {
                "total_frames": total_frames,
                "fps": round(source_fps, 2)
            })

            frame_idx = 0
            start_time = time.time()
            records_batch = []
            speed_measurements = []

            # Process loop
            while cap.isOpened():
                if stop_signals.get(session_id, False):
                    print(f"[AutoVision AI] Stop signal received for {session_id}")
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                curr_timestamp = frame_idx / source_fps

                # YOLO Detection & Tracking
                detections = detector.detect_and_track(
                    frame,
                    conf=conf_threshold,
                    iou=iou_threshold,
                    selected_classes=selected_classes,
                    persist=enable_tracking
                )

                # Tracker Update
                active_vehicles = tracker.update(
                    detections,
                    frame_idx=frame_idx,
                    timestamp=curr_timestamp,
                    frame_shape=(frame_h, frame_w),
                    enable_counting=enable_counting
                )

                # Vehicle Snapshot Harvesting (capture first time counted or clear view)
                for v in active_vehicles:
                    t_id = v["track_id"]
                    traj = tracker.trajectories.get(t_id)
                    if traj and not traj.snapshot_saved and len(traj.positions) >= 6:
                        x1, y1, x2, y2 = [int(c) for c in v["bbox"]]
                        # Clamp
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(frame_w, x2), min(frame_h, y2)
                        if (x2 - x1) > 20 and (y2 - y1) > 20:
                            crop = frame[y1:y2, x1:x2]
                            snap_name = f"{session_id}_{t_id}.jpg"
                            snap_file = SNAPSHOTS_DIR / snap_name
                            cv2.imwrite(str(snap_file), crop)
                            traj.snapshot_saved = True
                            traj.snapshot_rel_path = f"/outputs/snapshots/{snap_name}"

                    # Collect speed for session average
                    if v["speed_kmh"] is not None:
                        speed_measurements.append(v["speed_kmh"])

                    # Collect per-frame telemetry for report
                    records_batch.append({
                        "session_id": session_id,
                        "frame_number": frame_idx,
                        "timestamp_sec": round(curr_timestamp, 3),
                        "track_id": v["track_id"],
                        "vehicle_class": v["class"],
                        "confidence": round(v["confidence"], 3),
                        "bbox_x1": round(v["bbox"][0], 1),
                        "bbox_y1": round(v["bbox"][1], 1),
                        "bbox_x2": round(v["bbox"][2], 1),
                        "bbox_y2": round(v["bbox"][3], 1),
                        "direction": v["direction"],
                        "speed_kmh": v["speed_kmh"]
                    })

                # Annotate & write frame
                annotated_frame = tracker.annotate_frame(
                    frame, active_vehicles, fps=source_fps, frame_idx=frame_idx
                )
                writer.write(annotated_frame)

                # Periodic batch insert to DB
                if len(records_batch) >= 100:
                    insert_detection_records_batch(records_batch)
                    records_batch = []

                # Periodic progress update
                if frame_idx % 10 == 0 or frame_idx == total_frames:
                    elapsed = time.time() - start_time
                    current_fps = round(frame_idx / elapsed, 1) if elapsed > 0 else 0.0
                    progress_pct = round((frame_idx / total_frames) * 100, 1)
                    avg_speed = round(float(np.mean(speed_measurements)), 1) if speed_measurements else None

                    status_update = {
                        "session_id": session_id,
                        "status": "processing",
                        "progress_percent": progress_pct,
                        "current_fps": current_fps,
                        "processed_frames": frame_idx,
                        "total_frames": total_frames,
                        "total_vehicles": tracker.total_counted,
                        "category_counts": tracker.category_counts.copy(),
                        "avg_speed": avg_speed,
                        "is_calibrated": is_calibrated,
                        "output_video_url": f"/outputs/videos/{out_filename}",
                        "report_csv_url": f"/reports/{csv_filename}",
                        "error": None
                    }
                    active_sessions[session_id].update(status_update)
                    if progress_callback:
                        progress_callback(status_update)

            # Flush remaining records
            if records_batch:
                insert_detection_records_batch(records_batch)

            # Insert vehicle event summaries into SQLite
            for t_id, traj in tracker.trajectories.items():
                insert_vehicle_event({
                    "session_id": session_id,
                    "track_id": t_id,
                    "vehicle_class": traj.vehicle_class,
                    "confidence": round(float(np.mean(traj.confidences)), 3) if traj.confidences else 0.5,
                    "first_frame": traj.first_frame,
                    "last_frame": traj.last_frame,
                    "first_seen_ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time + traj.first_timestamp)),
                    "last_seen_ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time + traj.last_timestamp)),
                    "direction": traj.direction,
                    "speed_kmh": traj.speed_kmh,
                    "is_counted": 1 if traj.is_counted else 0,
                    "lane_id": traj.lane_id,
                    "snapshot_path": traj.snapshot_rel_path,
                    "trajectory_json": json.dumps([p[:2] for p in traj.positions])
                })

            # Generate Final CSV Report
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer_csv = csv.writer(f)
                writer_csv.writerow([
                    "Vehicle ID", "Vehicle Class", "Avg Confidence",
                    "Movement Direction", "Estimated Speed (km/h)", "Counted",
                    "Lane", "First Frame", "Last Frame", "Snapshot Path"
                ])
                for t_id, traj in sorted(tracker.trajectories.items()):
                    writer_csv.writerow([
                        t_id,
                        traj.vehicle_class,
                        round(float(np.mean(traj.confidences)), 3) if traj.confidences else "n.a.",
                        traj.direction,
                        traj.speed_kmh if traj.speed_kmh is not None else "n.a. (uncalibrated)",
                        "YES" if traj.is_counted else "NO",
                        traj.lane_id,
                        traj.first_frame,
                        traj.last_frame,
                        traj.snapshot_rel_path
                    ])

            # Calculate Final Aggregates
            total_duration = time.time() - start_time
            overall_fps = round(frame_idx / total_duration, 2) if total_duration > 0 else 0.0
            overall_avg_speed = round(float(np.mean(speed_measurements)), 1) if speed_measurements else 0.0

            final_status = "stopped" if stop_signals.get(session_id, False) else "completed"

            final_session_data = {
                "status": final_status,
                "total_vehicles": tracker.total_counted,
                "car_count": tracker.category_counts.get("car", 0),
                "truck_count": tracker.category_counts.get("truck", 0),
                "bus_count": tracker.category_counts.get("bus", 0),
                "motorcycle_count": tracker.category_counts.get("motorcycle", 0),
                "bicycle_count": tracker.category_counts.get("bicycle", 0),
                "avg_speed": overall_avg_speed,
                "duration_seconds": round(total_duration, 2),
                "fps": overall_fps,
                "processed_frames": frame_idx,
                "output_video_path": f"/outputs/videos/{out_filename}",
                "report_csv_path": f"/reports/{csv_filename}"
            }
            update_session(session_id, final_session_data)

            # Update in-memory registry
            active_sessions[session_id].update({
                "status": final_status,
                "progress_percent": 100.0,
                "processed_frames": frame_idx,
                "current_fps": overall_fps,
                "output_video_url": f"/outputs/videos/{out_filename}",
                "report_csv_url": f"/reports/{csv_filename}"
            })

            if progress_callback:
                progress_callback(active_sessions[session_id])

            print(f"[AutoVision AI] Completed session {session_id}: {tracker.total_counted} vehicles detected.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            err_msg = str(e)
            update_session(session_id, {"status": "failed"})
            if session_id in active_sessions:
                active_sessions[session_id]["status"] = "failed"
                active_sessions[session_id]["error"] = err_msg
        finally:
            if cap:
                cap.release()
            if writer:
                writer.release()
