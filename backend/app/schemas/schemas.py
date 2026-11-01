"""
AutoVision AI - Pydantic Request & Response Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class StartDetectionRequest(BaseModel):
    video_path: Optional[str] = Field(None, description="Path to uploaded or sample video")
    use_sample: bool = Field(False, description="Whether to use the included input_video.mp4")
    model_name: str = Field("yolov8n.pt", description="YOLO model name")
    conf_threshold: float = Field(0.30, ge=0.05, le=1.0, description="Detection confidence threshold")
    iou_threshold: float = Field(0.45, ge=0.1, le=1.0, description="NMS IoU threshold")
    selected_classes: List[str] = Field(default_factory=lambda: ["car", "truck", "bus", "motorcycle", "bicycle"])
    enable_tracking: bool = Field(True, description="Enable vehicle ID tracking")
    enable_counting: bool = Field(True, description="Enable virtual line counting")
    counting_line_ratio: float = Field(0.55, ge=0.1, le=0.9, description="Horizontal counting line position (ratio of height)")
    is_calibrated: bool = Field(False, description="Whether speed calibration has been set")
    meters_per_pixel: float = Field(0.05, gt=0, description="Metric conversion scale (meters per pixel)")
    reference_distance_m: Optional[float] = Field(None, description="Known reference distance in meters (e.g. 10m marker)")
    reference_pixel_span: Optional[float] = Field(None, description="Pixel span corresponding to reference distance")

class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    progress_percent: float
    current_fps: float
    processed_frames: int
    total_frames: int
    total_vehicles: int
    category_counts: Dict[str, int]
    avg_speed: Optional[float]
    is_calibrated: bool
    output_video_url: Optional[str] = None
    report_csv_url: Optional[str] = None
    error: Optional[str] = None

class DetectionSessionItem(BaseModel):
    id: str
    source_type: str
    source_name: str
    created_at: str
    status: str
    total_vehicles: int
    car_count: int
    truck_count: int
    bus_count: int
    motorcycle_count: int
    bicycle_count: int
    avg_speed: float
    duration_seconds: float
    fps: float
    model_name: str
    conf_threshold: float
    output_video_path: str
    report_csv_path: str
    is_calibrated: int
    meters_per_pixel: float

class CameraConfigRequest(BaseModel):
    source_id: str = Field("0", description="Camera device index (e.g., '0') or 'virtual_sample'")
    conf_threshold: float = Field(0.30, ge=0.05, le=1.0)
    selected_classes: List[str] = Field(default_factory=lambda: ["car", "truck", "bus", "motorcycle", "bicycle"])
    enable_tracking: bool = Field(True)
    enable_counting: bool = Field(True)
    counting_line_ratio: float = Field(0.60)
    is_calibrated: bool = Field(False)
    meters_per_pixel: float = Field(0.05)
