"""
AutoVision AI - FastAPI Backend Server
Autonomous Vehicle Detection Using Deep Learning
Production-Ready for Render & Vercel Deployments
"""
import os
import time
import uuid
import shutil
import threading
from pathlib import Path
from typing import Dict, Any, Optional

import torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.app.detection.pipeline import DetectionPipeline

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs" / "videos"
REPORTS_DIR = BASE_DIR / "reports"
MODELS_DIR = BASE_DIR / "models"
SAMPLE_VIDEO_PATH = BASE_DIR / "input_video.mp4"

# Environment Configurations
PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "0.0.0.0")
MODEL_PATH = os.environ.get("MODEL_PATH", str(MODELS_DIR / "yolov8n.pt"))
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "250"))
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

# Ensure local directories exist (note: ephemeral on Render)
for d in [UPLOADS_DIR, OUTPUTS_DIR, REPORTS_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="AutoVision AI - Autonomous Vehicle Detection API",
    description="High-performance deep learning vehicle monitoring system powered by YOLOv8 and ByteTrack.",
    version="1.0.0"
)

# Production CORS Configuration
# Accepts explicit origins from ALLOWED_ORIGINS and automatically permits any Vercel domain (*.vercel.app)
raw_origins = os.environ.get("ALLOWED_ORIGINS", "").strip()
allowed_origins_list = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
if raw_origins:
    for origin in raw_origins.split(","):
        clean_origin = origin.strip().rstrip("/")
        if clean_origin and clean_origin not in allowed_origins_list:
            allowed_origins_list.append(clean_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for processed media (handled cleanly if directory is empty)
app.mount("/outputs/videos", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs_videos")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Detection Engine Singleton with Configurable Model Path
pipeline = DetectionPipeline(model_path=MODEL_PATH)

# In-memory session tracking (ephemeral storage aware)
sessions: Dict[str, Dict[str, Any]] = {}
latest_completed_session_id: Optional[str] = None

class DetectionRequest(BaseModel):
    video_path: Optional[str] = None
    use_sample: bool = False
    conf_threshold: float = Field(0.30, ge=0.10, le=0.90)

@app.get("/api/health")
def get_health():
    """
    Health check endpoint for Render health checks and frontend monitoring.
    Reports compute device, model status, and ephemeral storage state.
    """
    device = "CUDA GPU" if torch.cuda.is_available() else "CPU"
    return {
        "status": "online",
        "system": "AutoVision AI",
        "version": "1.0.0",
        "timestamp": time.time(),
        "compute_device": device,
        "model_path": MODEL_PATH,
        "model_loaded": pipeline.model is not None,
        "max_upload_size_mb": MAX_UPLOAD_SIZE_MB,
        "storage": {
            "ephemeral": True,
            "uploads_ready": UPLOADS_DIR.exists(),
            "outputs_ready": OUTPUTS_DIR.exists()
        },
        "sample_video_available": SAMPLE_VIDEO_PATH.exists()
    }

@app.get("/api/sample-video")
def get_sample_video():
    if not SAMPLE_VIDEO_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Benchmark sample video input_video.mp4 is not present on this instance."
        )
    size_mb = round(SAMPLE_VIDEO_PATH.stat().st_size / (1024 * 1024), 2)
    return {
        "filename": "input_video.mp4",
        "size_mb": size_mb,
        "description": "Benchmark Highway Traffic Video"
    }

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format '{ext}'. Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS)).upper()}."
        )

    clean_name = f"{int(time.time())}_{uuid.uuid4().hex[:6]}_{file.filename}"
    target_path = UPLOADS_DIR / clean_name

    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_written = 0

    try:
        with open(target_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_written += len(chunk)
                if total_written > max_bytes:
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed upload limit of {MAX_UPLOAD_SIZE_MB}MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to save video upload: {str(e)}")

    size_mb = round(total_written / (1024 * 1024), 2)

    return {
        "success": True,
        "filename": clean_name,
        "original_name": file.filename,
        "size_mb": size_mb,
        "video_path": str(target_path)
    }

@app.post("/api/detect")
def start_detection(req: DetectionRequest):
    global latest_completed_session_id

    # Resolve input video
    if req.use_sample or not req.video_path:
        if not SAMPLE_VIDEO_PATH.exists():
            raise HTTPException(
                status_code=400,
                detail="Sample video input_video.mp4 is not available on this server instance."
            )
        input_path = str(SAMPLE_VIDEO_PATH)
        source_name = "input_video.mp4 (Benchmark Sample)"
    else:
        input_path = req.video_path
        if not os.path.exists(input_path):
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded video file does not exist on disk: {input_path}"
            )
        source_name = Path(input_path).name

    session_id = f"session_{uuid.uuid4().hex[:8]}"
    out_video_filename = f"{session_id}_annotated.mp4"
    out_video_path = str(OUTPUTS_DIR / out_video_filename)
    out_csv_filename = f"{session_id}_report.csv"
    out_csv_path = str(REPORTS_DIR / out_csv_filename)

    # Initialize session registry (in-memory)
    sessions[session_id] = {
        "session_id": session_id,
        "source_name": source_name,
        "status": "processing",
        "progress_percent": 0.0,
        "processed_frames": 0,
        "total_frames": 0,
        "current_fps": 0.0,
        "total_vehicles": 0,
        "class_counts": {"Car": 0, "Truck": 0, "Bus": 0, "Motorcycle": 0, "Bicycle": 0},
        "mean_confidence": 0.0,
        "duration_seconds": 0.0,
        "video_url": f"/outputs/videos/{out_video_filename}",
        "csv_url": f"/api/download/csv/{session_id}",
        "tracked_vehicles": [],
        "error": None
    }

    # Worker thread
    def worker():
        global latest_completed_session_id
        try:
            def on_progress(p):
                sessions[session_id].update({
                    "processed_frames": p["processed_frames"],
                    "total_frames": p["total_frames"],
                    "progress_percent": p["progress_percent"],
                    "current_fps": p["current_fps"],
                    "total_vehicles": p["total_vehicles"],
                    "class_counts": p["class_counts"]
                })

            summary = pipeline.process_video(
                input_video_path=input_path,
                output_video_path=out_video_path,
                output_csv_path=out_csv_path,
                conf_threshold=req.conf_threshold,
                progress_callback=on_progress
            )

            sessions[session_id].update({
                "status": "completed",
                "progress_percent": 100.0,
                "total_vehicles": summary["total_vehicles"],
                "class_counts": summary["class_counts"],
                "mean_confidence": summary["mean_confidence"],
                "duration_seconds": summary["duration_seconds"],
                "current_fps": summary["fps"],
                "tracked_vehicles": summary["tracked_vehicles"]
            })
            latest_completed_session_id = session_id
            print(f"[AutoVision AI] Completed {session_id} - Total Vehicles: {summary['total_vehicles']}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            sessions[session_id].update({
                "status": "failed",
                "error": str(e)
            })

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    return {
        "success": True,
        "session_id": session_id,
        "status": "processing",
        "message": f"Detection started on {source_name}"
    }

@app.get("/api/status/{session_id}")
def get_session_status(session_id: str):
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Note: Server instances on Render have ephemeral memory."
        )
    return sessions[session_id]

@app.get("/api/results/{session_id}")
def get_session_results(session_id: str):
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session results not found or instance was restarted."
        )
    s = sessions[session_id]
    if s["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Session is currently '{s['status']}'."
        )
    return s

@app.get("/api/latest-result")
def get_latest_result():
    global latest_completed_session_id
    if latest_completed_session_id and latest_completed_session_id in sessions:
        return sessions[latest_completed_session_id]
    completed = [s for s in sessions.values() if s.get("status") == "completed"]
    if completed:
        return completed[-1]
    return {
        "available": False,
        "message": "No detection session has been executed on this instance yet."
    }

@app.get("/api/download/csv/{session_id}")
def download_csv(session_id: str):
    csv_file = REPORTS_DIR / f"{session_id}_report.csv"
    if not csv_file.exists():
        raise HTTPException(
            status_code=404,
            detail="CSV report file not found on disk. Files are ephemeral across Render restarts."
        )
    return FileResponse(
        path=str(csv_file),
        filename=f"AutoVision_{session_id}_results.csv",
        media_type="text/csv"
    )

@app.get("/api/download/video/{session_id}")
def download_video(session_id: str):
    video_file = OUTPUTS_DIR / f"{session_id}_annotated.mp4"
    if not video_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Processed video file not found on disk. Files are ephemeral across Render restarts."
        )
    return FileResponse(
        path=str(video_file),
        filename=f"AutoVision_{session_id}_annotated.mp4",
        media_type="video/mp4"
    )

if __name__ == "__main__":
    import uvicorn
    print(f"[AutoVision AI] Starting server on {HOST}:{PORT}")
    uvicorn.run("backend.app.main:app", host=HOST, port=PORT, reload=False)
