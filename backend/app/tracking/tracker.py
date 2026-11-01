"""
AutoVision AI - Multi-Object Vehicle Tracker & Traffic Telemetry
Handles persistent tracking history, virtual counting lines, direction estimation,
calibrated speed physics, lane localization, and visual annotations.
"""
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from app.core.config import CLASS_COLORS

class VehicleTrajectory:
    def __init__(self, track_id: int, vehicle_class: str, initial_bbox: List[float], frame_idx: int, timestamp: float):
        self.track_id = track_id
        self.vehicle_class = vehicle_class
        self.positions: List[Tuple[float, float, int, float]] = []  # (x, y, frame_idx, timestamp)
        self.bboxes: List[List[float]] = []
        self.confidences: List[float] = []
        self.first_frame = frame_idx
        self.last_frame = frame_idx
        self.first_timestamp = timestamp
        self.last_timestamp = timestamp
        self.is_counted = False
        self.direction = "Southbound (Down)"
        self.speed_kmh: Optional[float] = None
        self.speed_samples: List[float] = []
        self.lane_id = "Lane 1"
        self.snapshot_saved = False
        self.snapshot_rel_path: str = ""

        # Initial append
        x1, y1, x2, y2 = initial_bbox
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        self.positions.append((cx, cy, frame_idx, timestamp))
        self.bboxes.append(initial_bbox)

    def update(
        self,
        bbox: List[float],
        confidence: float,
        frame_idx: int,
        timestamp: float,
        is_calibrated: bool,
        meters_per_pixel: float,
        frame_width: int
    ):
        self.last_frame = frame_idx
        self.last_timestamp = timestamp
        self.bboxes.append(bbox)
        self.confidences.append(confidence)

        x1, y1, x2, y2 = bbox
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        self.positions.append((cx, cy, frame_idx, timestamp))

        # Keep max 50 history points for memory efficiency
        if len(self.positions) > 50:
            self.positions.pop(0)
            self.bboxes.pop(0)

        # Estimate direction
        if len(self.positions) >= 5:
            start_x, start_y = self.positions[0][0], self.positions[0][1]
            curr_x, curr_y = cx, cy
            dy = curr_y - start_y
            dx = curr_x - start_x

            if abs(dy) >= abs(dx):
                if dy > 8:
                    self.direction = "Southbound (Down)"
                elif dy < -8:
                    self.direction = "Northbound (Up)"
            else:
                if dx > 8:
                    self.direction = "Eastbound (Right)"
                elif dx < -8:
                    self.direction = "Westbound (Left)"

        # Calculate Lane based on X position
        if frame_width > 0:
            lane_ratio = cx / frame_width
            if lane_ratio < 0.35:
                self.lane_id = "Lane 1 (Left)"
            elif lane_ratio < 0.65:
                self.lane_id = "Lane 2 (Center)"
            else:
                self.lane_id = "Lane 3 (Right)"

        # Estimate Speed if Calibrated
        if is_calibrated and len(self.positions) >= 8:
            # Measure displacement over past 6-12 frames
            past_idx = max(0, len(self.positions) - 8)
            px, py, pf, pt = self.positions[past_idx]

            dt = timestamp - pt
            if dt > 0.15:  # At least 150ms window
                pixel_disp = np.hypot(cx - px, cy - py)
                real_meters = pixel_disp * meters_per_pixel
                instant_speed_kmh = (real_meters / dt) * 3.6

                # Sanity bound for road traffic speed: 5 to 180 km/h
                if 5.0 <= instant_speed_kmh <= 180.0:
                    self.speed_samples.append(instant_speed_kmh)
                    if len(self.speed_samples) > 10:
                        self.speed_samples.pop(0)
                    self.speed_kmh = round(float(np.median(self.speed_samples)), 1)


class TrafficTracker:
    def __init__(
        self,
        counting_line_ratio: float = 0.55,
        is_calibrated: bool = False,
        meters_per_pixel: float = 0.05
    ):
        self.counting_line_ratio = counting_line_ratio
        self.is_calibrated = is_calibrated
        self.meters_per_pixel = meters_per_pixel

        self.trajectories: Dict[int, VehicleTrajectory] = {}
        self.total_counted = 0
        self.category_counts: Dict[str, int] = {
            "car": 0, "truck": 0, "bus": 0, "motorcycle": 0, "bicycle": 0
        }
        self.counted_ids: set[int] = set()

    def update(
        self,
        detections: List[Dict[str, Any]],
        frame_idx: int,
        timestamp: float,
        frame_shape: Tuple[int, int],
        enable_counting: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Updates tracking state with current frame detections.
        Returns list of active tracked vehicles with direction & speed info.
        """
        frame_h, frame_w = frame_shape[:2]
        line_y = int(frame_h * self.counting_line_ratio)

        active_vehicles = []

        for det in detections:
            track_id = det["track_id"]
            if track_id == -1:
                continue

            v_class = det["class"]
            conf = det["confidence"]
            bbox = det["bbox"]

            if track_id not in self.trajectories:
                self.trajectories[track_id] = VehicleTrajectory(
                    track_id, v_class, bbox, frame_idx, timestamp
                )

            traj = self.trajectories[track_id]
            prev_y = traj.positions[-1][1] if traj.positions else (bbox[1] + bbox[3]) / 2.0

            traj.update(
                bbox, conf, frame_idx, timestamp,
                self.is_calibrated, self.meters_per_pixel, frame_w
            )

            curr_y = traj.positions[-1][1]

            # Virtual Line Crossing Detection
            if enable_counting and not traj.is_counted and track_id not in self.counted_ids:
                # Crossed from above to below or below to above within margin
                if (prev_y <= line_y <= curr_y) or (prev_y >= line_y >= curr_y) or abs(curr_y - line_y) < 12:
                    traj.is_counted = True
                    self.counted_ids.add(track_id)
                    self.total_counted += 1
                    self.category_counts[v_class] = self.category_counts.get(v_class, 0) + 1

            active_vehicles.append({
                "track_id": track_id,
                "class": v_class,
                "confidence": conf,
                "bbox": bbox,
                "centroid": traj.positions[-1][:2],
                "direction": traj.direction,
                "speed_kmh": traj.speed_kmh,
                "is_counted": traj.is_counted,
                "lane_id": traj.lane_id,
                "trajectory": [p[:2] for p in traj.positions]
            })

        return active_vehicles

    def annotate_frame(
        self,
        frame: np.ndarray,
        active_vehicles: List[Dict[str, Any]],
        fps: float,
        frame_idx: int,
        show_line: bool = True
    ) -> np.ndarray:
        """
        Draws high-contrast command-center annotations on the video frame.
        """
        annotated = frame.copy()
        frame_h, frame_w = annotated.shape[:2]
        line_y = int(frame_h * self.counting_line_ratio)

        # 1. Draw Virtual Counting Line
        if show_line:
            # Subtle glowing guide
            cv2.line(annotated, (0, line_y), (frame_w, line_y), (6, 182, 212), 2, cv2.LINE_AA)
            cv2.line(annotated, (0, line_y - 1), (frame_w, line_y - 1), (255, 200, 0), 1, cv2.LINE_AA)
            # Label
            cv2.putText(
                annotated,
                f"COUNTING LINE (Y={line_y})",
                (15, line_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (6, 182, 212),
                1,
                cv2.LINE_AA
            )

        # 2. Draw Tracked Vehicles
        for v in active_vehicles:
            x1, y1, x2, y2 = [int(c) for c in v["bbox"]]
            v_class = v["class"]
            t_id = v["track_id"]
            conf = v["confidence"]
            direction = v["direction"]
            speed = v["speed_kmh"]
            is_counted = v["is_counted"]

            color_bgr = CLASS_COLORS.get(v_class, {}).get("bgr", (0, 255, 0))

            # Bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color_bgr, 2, cv2.LINE_AA)

            # Draw Centroid and Trajectory Trail
            trail = v["trajectory"]
            if len(trail) > 1:
                pts = np.array(trail, np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated, [pts], False, color_bgr, 1, cv2.LINE_AA)

            # Header Badge
            speed_text = f" {speed}km/h" if speed is not None else ""
            status_indicator = " [COUNTED]" if is_counted else ""
            label = f"#{t_id} {v_class.upper()} {int(conf*100)}%{speed_text}{status_indicator}"

            (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
            badge_y1 = max(0, y1 - th - 8)
            badge_y2 = y1

            cv2.rectangle(annotated, (x1, badge_y1), (x1 + tw + 8, badge_y2), (15, 23, 42), -1)
            cv2.rectangle(annotated, (x1, badge_y1), (x1 + tw + 8, badge_y2), color_bgr, 1)
            cv2.putText(
                annotated,
                label,
                (x1 + 4, badge_y2 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

            # Direction Arrow
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            if "Down" in direction or "South" in direction:
                cv2.arrowedLine(annotated, (cx, cy - 8), (cx, cy + 8), (0, 255, 255), 1, tipLength=0.4)
            elif "Up" in direction or "North" in direction:
                cv2.arrowedLine(annotated, (cx, cy + 8), (cx, cy - 8), (0, 255, 255), 1, tipLength=0.4)

        # 3. Command Center HUD Overlay (Top-Left)
        overlay_w, overlay_h = 240, 95
        cv2.rectangle(annotated, (10, 10), (10 + overlay_w, 10 + overlay_h), (11, 17, 32), -1)
        cv2.rectangle(annotated, (10, 10), (10 + overlay_w, 10 + overlay_h), (30, 41, 59), 1)

        cv2.putText(
            annotated,
            "AUTOPILOT / AUTOVISION AI",
            (20, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (6, 182, 212),
            1,
            cv2.LINE_AA
        )
        cv2.putText(
            annotated,
            f"Vehicles Counted: {self.total_counted}",
            (20, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        counts_str = f"C:{self.category_counts['car']} T:{self.category_counts['truck']} B:{self.category_counts['bus']} M:{self.category_counts['motorcycle']}"
        cv2.putText(
            annotated,
            counts_str,
            (20, 68),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (148, 163, 184),
            1,
            cv2.LINE_AA
        )

        calib_str = f"FPS: {fps:.1f} | Calibrated: {'YES' if self.is_calibrated else 'NO'}"
        cv2.putText(
            annotated,
            calib_str,
            (20, 88),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (52, 211, 153) if self.is_calibrated else (251, 191, 36),
            1,
            cv2.LINE_AA
        )

        return annotated
