import urllib.request
import json
import time

def test_flow():
    print("=" * 60)
    print("AutoVision AI - Academic Workflow End-to-End Test")
    print("=" * 60)

    # 1. Health Check
    print("[1/6] Checking API Health...")
    health = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/health").read().decode())
    print(f"      Status: {health['status']} | Model: {health['model_loaded']} | Device: {health['compute_device']}")

    # 2. Sample Video Check
    print("[2/6] Checking Benchmark Video...")
    sample = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/sample-video").read().decode())
    print(f"      Filename: {sample['filename']} | Size: {sample['size_mb']} MB")

    # 3. Start Detection on Benchmark Video
    print("[3/6] Starting YOLOv8 Detection on Benchmark Video...")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/detect",
        data=json.dumps({"use_sample": True, "conf_threshold": 0.30}).encode(),
        headers={"Content-Type": "application/json"}
    )
    start_res = json.loads(urllib.request.urlopen(req).read().decode())
    session_id = start_res["session_id"]
    print(f"      Session Created: {session_id}")

    # 4. Monitor Progress
    print("[4/6] Processing frames and tracking vehicles across frames...")
    completed = False
    for i in range(120):
        time.sleep(1.5)
        status = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8000/api/status/{session_id}").read().decode())
        if i % 6 == 0 or status["status"] in ["completed", "failed"]:
            print(f"      Frame {status['processed_frames']}/{status['total_frames']} ({status['progress_percent']}%) | Total Count: {status['total_vehicles']} | Rate: {status['current_fps']} FPS")
        if status["status"] == "completed":
            completed = True
            break
        elif status["status"] == "failed":
            print(f"      [ERROR] Processing failed: {status.get('error')}")
            return False

    if not completed:
        print("      [TIMEOUT] Processing took longer than test timeout.")
        return False

    # 5. Fetch Final Results
    print("[5/6] Fetching Analysis Results...")
    results = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8000/api/results/{session_id}").read().decode())
    print(f"      Total Vehicles: {results['total_vehicles']}")
    print(f"      Class Breakdown: {results['class_counts']}")
    print(f"      Mean Confidence: {results['mean_confidence']}%")
    print(f"      Duration: {results['duration_seconds']}s at {results['current_fps']} FPS")
    print(f"      Video URL: {results['video_url']}")
    print(f"      CSV URL: {results['csv_url']}")

    # 6. Verify Downloads
    print("[6/6] Verifying CSV and Video Downloads...")
    csv_bytes = urllib.request.urlopen(f"http://127.0.0.1:8000{results['csv_url']}").read()
    print(f"      CSV Download Verified: {len(csv_bytes)} bytes received.")
    video_bytes_header = urllib.request.urlopen(f"http://127.0.0.1:8000/api/download/video/{session_id}")
    print(f"      Video Download Header: {video_bytes_header.status} OK (Content-Type: {video_bytes_header.headers.get('Content-Type')})")

    # 7. Check Latest Result API for Dashboard
    latest = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/latest-result").read().decode())
    assert latest["session_id"] == session_id, "Latest session ID mismatch"
    print("      Latest Result API synced with Dashboard successfully.")

    print("=" * 60)
    print("AutoVision AI: ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_flow()
