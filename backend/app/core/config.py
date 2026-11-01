"""
AutoVision AI - Configuration and Application Settings
"""
import os
from pathlib import Path
from pydantic import BaseModel

FILE_PARENT4 = Path(__file__).resolve().parent.parent.parent.parent
FILE_PARENT3 = Path(__file__).resolve().parent.parent.parent
CWD = Path.cwd().resolve()

if (FILE_PARENT4 / "input_video.mp4").exists():
    BASE_DIR = FILE_PARENT4
elif (FILE_PARENT3 / "input_video.mp4").exists():
    BASE_DIR = FILE_PARENT3
elif (CWD / "input_video.mp4").exists():
    BASE_DIR = CWD
else:
    BASE_DIR = FILE_PARENT4

UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
SNAPSHOTS_DIR = OUTPUTS_DIR / "snapshots"
REPORTS_DIR = BASE_DIR / "reports"
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = BASE_DIR / "autovision.db"

# Ensure runtime directories exist
for folder in [UPLOADS_DIR, OUTPUTS_DIR, VIDEOS_DIR, SNAPSHOTS_DIR, REPORTS_DIR, MODELS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# COCO Vehicle Class ID Mapping (YOLO)
SUPPORTED_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    1: "bicycle"
}

# Default Color Map for Vehicle Classes (BGR for OpenCV, Hex for UI)
CLASS_COLORS = {
    "car": {"bgr": (255, 128, 0), "hex": "#0080ff"},        # Vibrant Blue
    "truck": {"bgr": (0, 200, 255), "hex": "#ffc800"},      # Amber / Orange
    "bus": {"bgr": (0, 255, 128), "hex": "#80ff00"},        # Lime / Green
    "motorcycle": {"bgr": (255, 0, 200), "hex": "#c800ff"}, # Violet
    "bicycle": {"bgr": (0, 255, 255), "hex": "#ffff00"}      # Yellow
}

class SystemConfig(BaseModel):
    app_name: str = "AutoVision AI"
    version: str = "2.0.0"
    model_name: str = "yolov8n.pt"
    default_conf: float = 0.30
    default_iou: float = 0.45
    default_line_ratio: float = 0.60  # Horizontal counting line at 60% of frame height
    default_meters_per_pixel: float = 0.05  # Calibrated for highway reference (~20 pixels = 1 meter)
    max_video_size_mb: int = 250
    allowed_extensions: list[str] = [".mp4", ".avi", ".mov", ".mkv"]

settings = SystemConfig()
