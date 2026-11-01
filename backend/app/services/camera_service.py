"""
AutoVision AI - Live Camera & Video Stream Service
Handles real-time webcam feeds, RTSP streams, and virtual test feeds with real-time detection & tracking.
"""
import cv2
import time
import threading
import numpy as np
from typing import Dict, Any, Optional, Generator
from app.core.config import BASE_DIR
from app.detection.yolo_detector import YOLODetector
from app.tracking.tracker import TrafficTracker

class CameraStreamManager:
    _instance = None

    def __init__(self):
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.is_paused = False
        self.current_source = "0"
        self.detector = YOLODetector.get_detector()
        self.tracker = TrafficTracker()
        self.lock = threading.Lock()
        self.current_frame: Optional[np.ndarray] = None
        self.fps = 0.0
        self.frame_idx = 0
        self.start_time = 0.0
        self.active_vehicles = []
        self.error_message: Optional[str] = None
        self.thread: Optional[threading.Thread] = None

        # Configurable params
        self.conf_threshold = 0.30
        self.selected_classes = ["car", "truck", "bus", "motorcycle", "bicycle"]
        self.enable_tracking = True
        self.enable_counting = True
        self.counting_line_ratio = 0.60
        self.is_calibrated = False
        self.meters_per_pixel = 0.05

    @classmethod
    def get_manager(cls) -> "CameraStreamManager":
        if cls._instance is None:
            cls._instance = CameraStreamManager()
        return cls._instance

    @staticmethod
    def list_available_sources() -> list[Dict[str, Any]]:
        sources = []
        # Check standard webcams 0 and 1
        for idx in [0, 1]:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if cv2.CAP_DSHOW else cv2.VideoCapture(idx)
            if cap.isOpened():
                sources.append({
                    "id": str(idx),
                    "name": f"Physical Camera {idx} (USB/Integrated Webcam)",
                    "type": "hardware",
                    "available": True
                })
                cap.release()
            else:
                sources.append({
                    "id": str(idx),
                    "name": f"Physical Camera {idx} (Not Detected / Disconnected)",
                    "type": "hardware",
                    "available": False
                })

        # Add sample virtual stream as explicit testing feed
        sample_path = BASE_DIR / "input_video.mp4"
        sources.append({
            "id": "sample_stream",
            "name": "Virtual Traffic Stream (input_video.mp4 Highway Feed)",
            "type": "virtual_sample",
            "available": sample_path.exists()
        })
        return sources

    def start_camera(
        self,
        source_id: str = "0",
        conf: float = 0.30,
        selected_classes: Optional[list] = None,
        enable_tracking: bool = True,
        enable_counting: bool = True,
        counting_line_ratio: float = 0.60,
        is_calibrated: bool = False,
        meters_per_pixel: float = 0.05
    ) -> Dict[str, Any]:
        with self.lock:
            if self.is_running:
                self.stop_camera()

            self.current_source = source_id
            self.conf_threshold = conf
            self.selected_classes = selected_classes or ["car", "truck", "bus", "motorcycle", "bicycle"]
            self.enable_tracking = enable_tracking
            self.enable_counting = enable_counting
            self.counting_line_ratio = counting_line_ratio
            self.is_calibrated = is_calibrated
            self.meters_per_pixel = meters_per_pixel

            self.tracker = TrafficTracker(
                counting_line_ratio=counting_line_ratio,
                is_calibrated=is_calibrated,
                meters_per_pixel=meters_per_pixel
            )

            # Open video source
            if source_id == "sample_stream":
                sample_file = BASE_DIR / "input_video.mp4"
                if not sample_file.exists():
                    self.error_message = "Sample video input_video.mp4 not found."
                    return {"success": False, "error": self.error_message}
                self.cap = cv2.VideoCapture(str(sample_file))
            else:
                try:
                    dev_index = int(source_id)
                    self.cap = cv2.VideoCapture(dev_index)
                except ValueError:
                    self.cap = cv2.VideoCapture(source_id)

            if not self.cap or not self.cap.isOpened():
                self.error_message = f"Failed to access camera source '{source_id}'. Please check camera hardware or USB permissions."
                return {"success": False, "error": self.error_message}

            self.is_running = True
            self.is_paused = False
            self.error_message = None
            self.frame_idx = 0
            self.start_time = time.time()

            self.thread = threading.Thread(target=self._capture_and_process_loop, daemon=True)
            self.thread.start()

            return {"success": True, "source": source_id}

    def stop_camera(self):
        with self.lock:
            self.is_running = False
            self.is_paused = False
            if self.cap:
                self.cap.release()
                self.cap = None
            self.current_frame = None

    def pause_camera(self):
        with self.lock:
            self.is_paused = True

    def resume_camera(self):
        with self.lock:
            self.is_paused = False

    def update_config(self, conf: Optional[float] = None, classes: Optional[list] = None, line_ratio: Optional[float] = None):
        with self.lock:
            if conf is not None:
                self.conf_threshold = conf
            if classes is not None:
                self.selected_classes = classes
            if line_ratio is not None:
                self.counting_line_ratio = line_ratio
                self.tracker.counting_line_ratio = line_ratio

    def _capture_and_process_loop(self):
        fps_counter = 0
        fps_timer = time.time()

        while self.is_running:
            if self.is_paused:
                time.sleep(0.05)
                continue

            ret, frame = self.cap.read()
            if not ret:
                # If virtual sample feed, loop video continuously
                if self.current_source == "sample_stream":
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    self.error_message = "Camera stream disconnected or ended."
                    self.is_running = False
                    break

            self.frame_idx += 1
            curr_time = time.time()

            # YOLO detection and tracking
            detections = self.detector.detect_and_track(
                frame,
                conf=self.conf_threshold,
                selected_classes=self.selected_classes,
                persist=self.enable_tracking
            )

            # Tracker update
            h, w = frame.shape[:2]
            active_vehicles = self.tracker.update(
                detections,
                frame_idx=self.frame_idx,
                timestamp=curr_time - self.start_time,
                frame_shape=(h, w),
                enable_counting=self.enable_counting
            )

            # Compute actual FPS
            fps_counter += 1
            if time.time() - fps_timer >= 1.0:
                self.fps = round(fps_counter / (time.time() - fps_timer), 1)
                fps_counter = 0
                fps_timer = time.time()

            # Annotate
            annotated = self.tracker.annotate_frame(
                frame, active_vehicles, fps=self.fps, frame_idx=self.frame_idx
            )

            with self.lock:
                self.current_frame = annotated
                self.active_vehicles = active_vehicles

            # Moderate frame loop to prevent 100% CPU lock in simulation
            time.sleep(0.02)

    def get_latest_frame_jpeg(self) -> Optional[bytes]:
        with self.lock:
            if self.current_frame is None:
                return None
            ret, jpeg = cv2.imencode('.jpg', self.current_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            return jpeg.tobytes() if ret else None

    def get_live_telemetry(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "is_running": self.is_running,
                "is_paused": self.is_paused,
                "current_source": self.current_source,
                "fps": self.fps,
                "total_vehicles": self.tracker.total_counted,
                "category_counts": self.tracker.category_counts.copy(),
                "active_vehicles": len(self.active_vehicles),
                "is_calibrated": self.is_calibrated,
                "error": self.error_message
            }
