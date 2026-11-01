"""
AutoVision AI - Deep Learning Detection Pipeline
Processes uploaded traffic videos using Ultralytics YOLOv8 with ByteTrack tracking.
"""
import os
import cv2
import csv
import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from ultralytics import YOLO

# Supported COCO vehicle classes
SUPPORTED_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck",
    1: "Bicycle"
}

# BGR color palette for annotation
CLASS_COLORS = {
    "Car": (255, 128, 0),        # Vibrant Blue
    "Truck": (0, 200, 255),      # Amber
    "Bus": (0, 255, 128),        # Lime
    "Motorcycle": (255, 0, 200), # Magenta
    "Bicycle": (0, 255, 255)     # Yellow
}

class DetectionPipeline:
    def __init__(self, model_path: Optional[str] = None):
        """
        Initializes the YOLOv8 detection model from a local path or model name.
        If a local file is missing, Ultralytics automatically downloads the weights.
        """
        if not model_path:
            model_path = os.environ.get("MODEL_PATH", "models/yolov8n.pt")
        
        # If specified local path doesn't exist, check root or fall back to standard model name
        if not os.path.exists(model_path):
            if os.path.exists("yolov8n.pt"):
                model_path = "yolov8n.pt"
            elif Path(model_path).name.endswith(".pt"):
                # Pass model name (e.g. yolov8n.pt); Ultralytics will auto-download if absent
                model_path = Path(model_path).name

        print(f"[AutoVision AI] Loading detection model: {model_path}")
        self.model = YOLO(model_path)

    def process_video(
        self,
        input_video_path: str,
        output_video_path: str,
        output_csv_path: str,
        conf_threshold: float = 0.30,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Any]:
        """
        Executes frame-by-frame YOLOv8 detection and tracking.
        Writes annotated MP4 video and structured CSV results.
        """
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open input video: {input_video_path}")

        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

        # Universal MP4 codec for web playback
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        writer = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_w, frame_h))

        # Target class IDs
        target_class_ids = list(SUPPORTED_CLASSES.keys())

        # Tracking and count accumulators
        tracked_vehicles: Dict[int, Dict[str, Any]] = {}
        unique_vehicle_ids = set()
        class_counts = {"Car": 0, "Truck": 0, "Bus": 0, "Motorcycle": 0, "Bicycle": 0}

        frame_idx = 0
        start_time = time.time()

        try:
            while cap.isOpened():
                if should_stop and should_stop():
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1

                # Run YOLO tracking with ByteTrack
                results = self.model.track(
                    source=frame,
                    conf=conf_threshold,
                    classes=target_class_ids,
                    persist=True,
                    verbose=False
                )

                annotated_frame = frame.copy()

                # Process detections in current frame
                current_frame_dets = []
                for r in results:
                    boxes = r.boxes
                    if boxes is None or len(boxes) == 0:
                        continue

                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())
                        track_id = int(box.id[0].item()) if box.id is not None else -1
                        cls_name = SUPPORTED_CLASSES.get(cls_id, "Vehicle")
                        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]

                        # Register unique tracked vehicle
                        if track_id != -1:
                            if track_id not in tracked_vehicles:
                                tracked_vehicles[track_id] = {
                                    "track_id": track_id,
                                    "class": cls_name,
                                    "confidences": [conf],
                                    "first_frame": frame_idx,
                                    "last_frame": frame_idx,
                                }
                                unique_vehicle_ids.add(track_id)
                                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                            else:
                                tracked_vehicles[track_id]["confidences"].append(conf)
                                tracked_vehicles[track_id]["last_frame"] = frame_idx

                        # Draw bounding box
                        color = CLASS_COLORS.get(cls_name, (0, 255, 0))
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

                        # Label badge
                        id_label = f"#{track_id} " if track_id != -1 else ""
                        label = f"{id_label}{cls_name.upper()} {int(conf * 100)}%"
                        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                        badge_y1 = max(0, y1 - th - 8)
                        cv2.rectangle(annotated_frame, (x1, badge_y1), (x1 + tw + 8, y1), (15, 23, 42), -1)
                        cv2.rectangle(annotated_frame, (x1, badge_y1), (x1 + tw + 8, y1), color, 1)
                        cv2.putText(
                            annotated_frame,
                            label,
                            (x1 + 4, y1 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.45,
                            (255, 255, 255),
                            1,
                            cv2.LINE_AA
                        )

                # Overlay HUD panel (top-left)
                hud_w, hud_h = 240, 85
                cv2.rectangle(annotated_frame, (10, 10), (10 + hud_w, 10 + hud_h), (11, 17, 32), -1)
                cv2.rectangle(annotated_frame, (10, 10), (10 + hud_w, 10 + hud_h), (30, 41, 59), 1)

                cv2.putText(
                    annotated_frame,
                    "AutoVision AI Detector",
                    (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.48,
                    (6, 182, 212),
                    1,
                    cv2.LINE_AA
                )
                cv2.putText(
                    annotated_frame,
                    f"Vehicles Counted: {len(unique_vehicle_ids)}",
                    (20, 52),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.54,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )
                counts_line = f"C:{class_counts['Car']} T:{class_counts['Truck']} B:{class_counts['Bus']} M:{class_counts['Motorcycle']}"
                cv2.putText(
                    annotated_frame,
                    counts_line,
                    (20, 72),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.38,
                    (148, 163, 184),
                    1,
                    cv2.LINE_AA
                )

                writer.write(annotated_frame)

                # Send periodic progress updates
                if progress_callback and (frame_idx % 10 == 0 or frame_idx == total_frames):
                    elapsed = time.time() - start_time
                    current_fps = round(frame_idx / elapsed, 1) if elapsed > 0 else 0.0
                    progress_pct = round((frame_idx / total_frames) * 100, 1)
                    progress_callback({
                        "processed_frames": frame_idx,
                        "total_frames": total_frames,
                        "progress_percent": progress_pct,
                        "current_fps": current_fps,
                        "total_vehicles": len(unique_vehicle_ids),
                        "class_counts": class_counts.copy()
                    })

        finally:
            cap.release()
            writer.release()

        total_duration = time.time() - start_time
        overall_fps = round(frame_idx / total_duration, 1) if total_duration > 0 else 0.0

        # Calculate average confidence across all detections
        all_confs = []
        for v in tracked_vehicles.values():
            all_confs.extend(v["confidences"])
        mean_confidence = round(float(np.mean(all_confs)) * 100, 1) if all_confs else 0.0

        # Export structured CSV report
        with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
            writer_csv = csv.writer(f)
            writer_csv.writerow([
                "Vehicle ID",
                "Vehicle Class",
                "Mean Confidence (%)",
                "First Seen Frame",
                "Last Seen Frame",
                "Total Frames Tracked"
            ])
            for t_id in sorted(tracked_vehicles.keys()):
                v = tracked_vehicles[t_id]
                c_mean = round(float(np.mean(v["confidences"])) * 100, 1)
                writer_csv.writerow([
                    t_id,
                    v["class"],
                    c_mean,
                    v["first_frame"],
                    v["last_frame"],
                    v["last_frame"] - v["first_frame"] + 1
                ])

        # Return full summary
        return {
            "total_frames": frame_idx,
            "duration_seconds": round(total_duration, 1),
            "fps": overall_fps,
            "total_vehicles": len(unique_vehicle_ids),
            "class_counts": class_counts,
            "mean_confidence": mean_confidence,
            "tracked_vehicles": [
                {
                    "track_id": t_id,
                    "class": v["class"],
                    "confidence": round(float(np.mean(v["confidences"])) * 100, 1),
                    "first_frame": v["first_frame"],
                    "last_frame": v["last_frame"]
                }
                for t_id, v in sorted(tracked_vehicles.items())
            ]
        }
