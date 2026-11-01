"""
AutoVision AI - Test Detection and Tracking Pipeline
Tests YOLOv8 inference, vehicle class filtering, and tracking on input_video.mp4.
"""
import os
import sys
import time
import cv2
from ultralytics import YOLO

# COCO vehicle class mappings
VEHICLE_CLASS_IDS = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    1: "bicycle"
}

def main():
    print("=" * 60)
    print("AutoVision AI: Validating Detection & Tracking Pipeline")
    print("=" * 60)

    model_name = "yolov8n.pt"
    print(f"[INFO] Initializing model: {model_name}")
    start_time = time.time()
    model = YOLO(model_name)
    print(f"[INFO] Model loaded in {time.time() - start_time:.2f}s")

    video_path = "input_video.mp4"
    if not os.path.exists(video_path):
        print(f"[ERROR] Sample video not found at {video_path}")
        sys.exit(1)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video: {video_path}")
        sys.exit(1)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"[INFO] Video resolution: {width}x{height}, FPS: {fps:.1f}, Frames: {total_frames}")

    # Process first 30 frames to test detection and tracking
    frames_to_test = 30
    frame_count = 0
    detected_vehicles = []
    unique_ids = set()

    print(f"[INFO] Running YOLO tracking on first {frames_to_test} frames...")
    infer_start = time.time()

    while cap.isOpened() and frame_count < frames_to_test:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        # Run tracking (ByteTrack built into ultralytics)
        results = model.track(
            source=frame,
            classes=list(VEHICLE_CLASS_IDS.keys()),
            persist=True,
            conf=0.25,
            verbose=False
        )

        for r in results:
            boxes = r.boxes
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    track_id = int(box.id[0].item()) if box.id is not None else -1
                    cls_name = VEHICLE_CLASS_IDS.get(cls_id, "vehicle")

                    if track_id != -1:
                        unique_ids.add(track_id)

                    detected_vehicles.append({
                        "frame": frame_count,
                        "class": cls_name,
                        "conf": round(conf, 3),
                        "track_id": track_id,
                        "xyxy": [round(float(c), 1) for c in box.xyxy[0].tolist()]
                    })

    cap.release()
    elapsed = time.time() - infer_start
    actual_fps = frame_count / elapsed if elapsed > 0 else 0

    print("-" * 60)
    print(f"[SUCCESS] Processed {frame_count} frames in {elapsed:.2f}s (~{actual_fps:.1f} FPS)")
    print(f"[RESULTS] Total detections recorded: {len(detected_vehicles)}")
    print(f"[RESULTS] Unique tracking IDs assigned: {len(unique_ids)} -> {sorted(list(unique_ids))}")

    # Breakdown by class
    breakdown = {}
    for d in detected_vehicles:
        breakdown[d["class"]] = breakdown.get(d["class"], 0) + 1
    print(f"[RESULTS] Detections by class: {breakdown}")
    print("=" * 60)

if __name__ == "__main__":
    main()
