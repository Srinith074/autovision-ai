import urllib.request
import json
import time

REMOTE_BASE = "https://autovision-ai-0xcx.onrender.com"

def test_full_remote_flow():
    print(f"Connecting to live backend: {REMOTE_BASE} ...")

    # 1. Health check
    req = urllib.request.Request(f"{REMOTE_BASE}/api/health")
    with urllib.request.urlopen(req) as res:
        health = json.loads(res.read().decode())
        print(f"[OK] Health check passed: {health['system']} (device: {health['compute_device']})")

    # 2. Sample video check
    req = urllib.request.Request(f"{REMOTE_BASE}/api/sample-video")
    with urllib.request.urlopen(req) as res:
        sample = json.loads(res.read().decode())
        print(f"[OK] Sample video passed: {sample['filename']} ({sample['size_mb']} MB)")

    # 3. Video upload with multipart field 'file'
    boundary = "----WebKitAutoVisionTest123"
    # Create small valid mp4 header/dummy content
    dummy_video_bytes = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42" + b"0" * 2048
    body = (
        b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="file"; filename="integration_test.mp4"\r\n'
        b"Content-Type: video/mp4\r\n\r\n"
        + dummy_video_bytes + b"\r\n"
        b"--" + boundary.encode() + b"--\r\n"
    )

    req = urllib.request.Request(
        f"{REMOTE_BASE}/api/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req) as res:
        upload_res = json.loads(res.read().decode())
        assert upload_res["success"] is True
        assert "video_path" in upload_res
        returned_video_path = upload_res["video_path"]
        print(f"[OK] Upload passed. Returned video_path: {returned_video_path}")

    # 4. Start detection on sample video
    detect_payload = {
        "use_sample": True,
        "conf_threshold": 0.35
    }
    req = urllib.request.Request(
        f"{REMOTE_BASE}/api/detect",
        data=json.dumps(detect_payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as res:
        detect_res = json.loads(res.read().decode())
        assert detect_res["success"] is True
        session_id = detect_res["session_id"]
        print(f"[OK] Detection started. Session ID: {session_id}")

    # 5. Poll status for a few ticks
    for i in range(3):
        time.sleep(1.5)
        req = urllib.request.Request(f"{REMOTE_BASE}/api/status/{session_id}")
        with urllib.request.urlopen(req) as res:
            status = json.loads(res.read().decode())
            print(f"     Poll {i+1}: status={status['status']}, frames={status['processed_frames']}/{status['total_frames']}, progress={status['progress_percent']}%")

    print("\nALL REMOTE INTEGRATION CONTRACTS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_remote_flow()
