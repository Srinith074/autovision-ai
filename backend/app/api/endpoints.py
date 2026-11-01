"""
AutoVision AI - FastAPI REST Endpoints & Streaming Controllers
"""
import os
import shutil
import time
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Response
from fastapi.responses import StreamingResponse, FileResponse
import torch

from backend.app.core.config import (
    UPLOADS_DIR, REPORTS_DIR, BASE_DIR, settings
)
from backend.app.schemas.schemas import (
    StartDetectionRequest, CameraConfigRequest
)
from backend.app.database.database import (
    list_sessions, get_session, delete_session,
    get_session_events, get_analytics_overview
)
from backend.app.services.video_service import VideoProcessingService
from backend.app.services.camera_service import CameraStreamManager

router = APIRouter(prefix="/api")

# --- System Health & Diagnostics ---
@router.get("/health")
def get_health():
    device = "CUDA GPU" if torch.cuda.is_available() else "CPU"
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Intel/AMD CPU"
    return {
        "status": "online",
        "app_name": settings.app_name,
        "version": settings.version,
        "compute_device": device,
        "device_name": gpu_name,
        "model_loaded": settings.model_name,
        "sample_video_available": (BASE_DIR / "input_video.mp4").exists(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# --- Video Upload & Sample Video ---
@router.get("/video/sample")
def get_sample_video_info():
    sample_path = BASE_DIR / "input_video.mp4"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample input_video.mp4 not found.")
    size_mb = round(sample_path.stat().st_size / (1024 * 1024), 2)
    return {
        "available": True,
        "filename": "input_video.mp4",
        "size_mb": size_mb,
        "path": str(sample_path),
        "description": "Highway Traffic Sample (Ahmet Özlü benchmark dataset)"
    }

@router.post("/video/upload")
async def upload_video(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed: {', '.join(settings.allowed_extensions)}"
        )

    clean_name = f"{int(time.time())}_{file.filename}"
    target_path = UPLOADS_DIR / clean_name

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size_mb = round(target_path.stat().st_size / (1024 * 1024), 2)
    if size_mb > settings.max_video_size_mb:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.max_video_size_mb} MB."
        )

    return {
        "success": True,
        "filename": clean_name,
        "original_name": file.filename,
        "size_mb": size_mb,
        "video_path": str(target_path)
    }

# --- Video Detection Control ---
@router.post("/detection/start")
def start_detection(req: StartDetectionRequest):
    # Resolve video path
    if req.use_sample or not req.video_path:
        sample_file = BASE_DIR / "input_video.mp4"
        if not sample_file.exists():
            raise HTTPException(status_code=400, detail="Sample video not available.")
        target_video = str(sample_file)
        source_name = "input_video.mp4 (Sample)"
    else:
        target_video = req.video_path
        if not os.path.exists(target_video):
            raise HTTPException(status_code=400, detail=f"Specified video path does not exist: {target_video}")
        source_name = Path(target_video).name

    # Handle dynamic calibration calculation if reference distance is provided
    meters_per_pixel = req.meters_per_pixel
    is_calibrated = req.is_calibrated
    if req.reference_distance_m and req.reference_pixel_span and req.reference_pixel_span > 0:
        meters_per_pixel = req.reference_distance_m / req.reference_pixel_span
        is_calibrated = True

    session_id = VideoProcessingService.start_processing_job(
        video_path=target_video,
        source_name=source_name,
        model_name=req.model_name,
        conf_threshold=req.conf_threshold,
        iou_threshold=req.iou_threshold,
        selected_classes=req.selected_classes,
        enable_tracking=req.enable_tracking,
        enable_counting=req.enable_counting,
        counting_line_ratio=req.counting_line_ratio,
        is_calibrated=is_calibrated,
        meters_per_pixel=meters_per_pixel
    )

    return {
        "success": True,
        "session_id": session_id,
        "status": "processing",
        "message": f"Detection started for {source_name}"
    }

@router.post("/detection/stop/{session_id}")
def stop_detection(session_id: str):
    success = VideoProcessingService.stop_processing_job(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Active session not found or already ended.")
    return {"success": True, "session_id": session_id, "status": "stopping"}

@router.get("/detection/status/{session_id}")
def get_detection_status(session_id: str):
    active_status = VideoProcessingService.get_session_status(session_id)
    if active_status:
        return active_status

    # Fallback to database if finished
    db_session = get_session(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    return {
        "session_id": db_session["id"],
        "status": db_session["status"],
        "progress_percent": 100.0 if db_session["status"] in ["completed", "stopped"] else 0.0,
        "current_fps": db_session["fps"],
        "processed_frames": db_session["processed_frames"],
        "total_frames": db_session["total_frames"],
        "total_vehicles": db_session["total_vehicles"],
        "category_counts": {
            "car": db_session["car_count"],
            "truck": db_session["truck_count"],
            "bus": db_session["bus_count"],
            "motorcycle": db_session["motorcycle_count"],
            "bicycle": db_session["bicycle_count"]
        },
        "avg_speed": db_session["avg_speed"] if db_session["is_calibrated"] else None,
        "is_calibrated": bool(db_session["is_calibrated"]),
        "output_video_url": db_session["output_video_path"],
        "report_csv_url": db_session["report_csv_path"],
        "error": None
    }

@router.get("/detection/results/{session_id}")
def get_detection_results(session_id: str):
    db_session = get_session(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    events = get_session_events(session_id)

    # Class breakdown for charts
    categories = [
        {"name": "Car", "count": db_session["car_count"], "color": "#0080ff"},
        {"name": "Truck", "count": db_session["truck_count"], "color": "#ffc800"},
        {"name": "Bus", "count": db_session["bus_count"], "color": "#80ff00"},
        {"name": "Motorcycle", "count": db_session["motorcycle_count"], "color": "#c800ff"},
        {"name": "Bicycle", "count": db_session["bicycle_count"], "color": "#ffff00"},
    ]

    # Direction breakdown
    dir_counts = {}
    lane_counts = {}
    for ev in events:
        d = ev.get("direction") or "Unknown"
        dir_counts[d] = dir_counts.get(d, 0) + 1
        ln = ev.get("lane_id") or "Lane 1"
        lane_counts[ln] = lane_counts.get(ln, 0) + 1

    return {
        "session": db_session,
        "vehicle_events": events,
        "charts": {
            "categories": categories,
            "directions": [{"direction": k, "count": v} for k, v in dir_counts.items()],
            "lanes": [{"lane": k, "count": v} for k, v in lane_counts.items()]
        }
    }

@router.get("/detection/sessions")
def list_history(limit: int = 50, offset: int = 0):
    return {"sessions": list_sessions(limit, offset)}

@router.delete("/detection/sessions/{session_id}")
def delete_history_session(session_id: str):
    success = delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"success": True, "deleted_id": session_id}

# --- Analytics Overview ---
@router.get("/analytics/overview")
def get_analytics():
    return get_analytics_overview()

# --- Reports & CSV Download ---
@router.get("/reports/{session_id}")
def download_csv_report(session_id: str):
    csv_filename = f"{session_id}_report.csv"
    csv_file = REPORTS_DIR / csv_filename
    if not csv_file.exists():
        raise HTTPException(status_code=404, detail="Report CSV not found.")
    return FileResponse(
        path=str(csv_file),
        filename=csv_filename,
        media_type="text/csv"
    )

# --- Live Camera & MJPEG Streaming ---
@router.get("/camera/sources")
def get_camera_sources():
    return {"sources": CameraStreamManager.list_available_sources()}

@router.post("/camera/start")
def start_camera_feed(req: CameraConfigRequest):
    cam = CameraStreamManager.get_manager()
    res = cam.start_camera(
        source_id=req.source_id,
        conf=req.conf_threshold,
        selected_classes=req.selected_classes,
        enable_tracking=req.enable_tracking,
        enable_counting=req.enable_counting,
        counting_line_ratio=req.counting_line_ratio,
        is_calibrated=req.is_calibrated,
        meters_per_pixel=req.meters_per_pixel
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to start camera"))
    return res

@router.post("/camera/stop")
def stop_camera_feed():
    cam = CameraStreamManager.get_manager()
    cam.stop_camera()
    return {"success": True, "message": "Camera stopped"}

@router.post("/camera/pause")
def pause_camera_feed():
    cam = CameraStreamManager.get_manager()
    cam.pause_camera()
    return {"success": True, "message": "Camera paused"}

@router.post("/camera/resume")
def resume_camera_feed():
    cam = CameraStreamManager.get_manager()
    cam.resume_camera()
    return {"success": True, "message": "Camera resumed"}

@router.get("/camera/telemetry")
def get_camera_telemetry():
    cam = CameraStreamManager.get_manager()
    return cam.get_live_telemetry()

def generate_mjpeg_stream():
    cam = CameraStreamManager.get_manager()
    while cam.is_running:
        frame_bytes = cam.get_latest_frame_jpeg()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.04)

@router.get("/camera/feed")
def get_camera_stream():
    cam = CameraStreamManager.get_manager()
    if not cam.is_running:
        raise HTTPException(status_code=400, detail="Camera stream is not active. Call /api/camera/start first.")
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
