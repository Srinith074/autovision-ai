"""
AutoVision AI - Deep Learning Detection Engine
Encapsulates Ultralytics YOLO with COCO vehicle class filtering.
"""
import os
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional
from ultralytics import YOLO
from app.core.config import SUPPORTED_CLASSES, MODELS_DIR

# Reverse lookup: name -> class_id
CLASS_NAME_TO_ID = {name: cid for cid, name in SUPPORTED_CLASSES.items()}

class YOLODetector:
    _instance = None
    _loaded_model_name = None

    def __init__(self, model_name: str = "yolov8n.pt"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = self._resolve_model_path(model_name)
        print(f"[AutoVision YOLO] Loading {self.model_path} on device: {self.device}")
        self.model = YOLO(str(self.model_path))
        self.model_name = model_name

    def _resolve_model_path(self, model_name: str) -> Path:
        # Check models/ directory first
        local_in_models = MODELS_DIR / model_name
        if local_in_models.exists():
            return local_in_models
        # Check current working dir
        local_curr = Path(model_name)
        if local_curr.exists():
            return local_curr
        # Fallback to model name (ultralytics will load/download)
        return Path(model_name)

    @classmethod
    def get_detector(cls, model_name: str = "yolov8n.pt") -> "YOLODetector":
        if cls._instance is None or cls._loaded_model_name != model_name:
            cls._instance = YOLODetector(model_name)
            cls._loaded_model_name = model_name
        return cls._instance

    def detect_and_track(
        self,
        frame,
        conf: float = 0.30,
        iou: float = 0.45,
        selected_classes: Optional[List[str]] = None,
        persist: bool = True
    ):
        """
        Runs object detection and ByteTrack tracking on a single frame.
        Returns parsed detection bounding boxes and tracking IDs.
        """
        if selected_classes is None:
            selected_classes = list(SUPPORTED_CLASSES.values())

        # Map class names to class IDs
        target_class_ids = [
            CLASS_NAME_TO_ID[name] for name in selected_classes if name in CLASS_NAME_TO_ID
        ]
        if not target_class_ids:
            target_class_ids = list(SUPPORTED_CLASSES.keys())

        # Track with ByteTrack
        results = self.model.track(
            source=frame,
            conf=conf,
            iou=iou,
            classes=target_class_ids,
            persist=persist,
            verbose=False,
            device=self.device
        )

        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is None or len(boxes) == 0:
                continue

            for box in boxes:
                cls_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                track_id = int(box.id[0].item()) if box.id is not None else -1
                cls_name = SUPPORTED_CLASSES.get(cls_id, "vehicle")

                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]

                detections.append({
                    "track_id": track_id,
                    "class": cls_name,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2],
                    "centroid": [(x1 + x2) / 2.0, (y1 + y2) / 2.0]
                })

        return detections
