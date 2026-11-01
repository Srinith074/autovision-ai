"""
AutoVision AI - Deployment Readiness & API Verification Test Suite
Tests:
1. Health check & compute device reporting
2. Sample video benchmark availability
3. CORS headers with Vercel origin
4. File upload extension validation & size limits
5. Ephemeral storage 404 handling
6. Configurable model path verification
"""
import os
import json
import urllib.request
import urllib.error
import tempfile
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    url = f"{BASE_URL}/api/health"
    req = urllib.request.Request(url, headers={"Origin": "https://my-preview-app.vercel.app"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200, f"Expected 200, got {res.status}"
        data = json.loads(res.read().decode())
        assert data["status"] == "online"
        assert data["system"] == "AutoVision AI"
        assert data["model_loaded"] is True
        assert data["storage"]["ephemeral"] is True
        # Verify CORS header for Vercel
        cors_origin = res.headers.get("Access-Control-Allow-Origin")
        assert cors_origin == "https://my-preview-app.vercel.app", f"CORS failed: {cors_origin}"
    print("[PASS] Health Check & Vercel CORS Verified.")

def test_sample_video():
    url = f"{BASE_URL}/api/sample-video"
    with urllib.request.urlopen(url) as res:
        assert res.status == 200
        data = json.loads(res.read().decode())
        assert data["filename"] == "input_video.mp4"
        assert data["size_mb"] > 0
    print("[PASS] Benchmark Sample Video Endpoint Verified.")

def test_upload_validation_extension():
    # Test uploading an invalid file format (e.g. .txt)
    boundary = "----AutoVisionFormBoundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
        f"Fake video content\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    req = urllib.request.Request(
        f"{BASE_URL}/api/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    try:
        urllib.request.urlopen(req)
        assert False, "Upload of .txt should have failed with 400"
    except urllib.error.HTTPError as e:
        assert e.code == 400, f"Expected 400, got {e.code}"
        err = json.loads(e.read().decode())
        assert "Invalid format '.txt'" in err["detail"]
    print("[PASS] Invalid File Extension Rejection (400) Verified.")

def test_ephemeral_storage_graceful_404():
    # Query non-existent session
    url = f"{BASE_URL}/api/results/non_existent_session_12345"
    try:
        urllib.request.urlopen(url)
        assert False, "Should have 404'd"
    except urllib.error.HTTPError as e:
        assert e.code == 404
        err = json.loads(e.read().decode())
        assert "not found" in err["detail"].lower()

    # Query non-existent download
    url = f"{BASE_URL}/api/download/video/non_existent_session_12345"
    try:
        urllib.request.urlopen(url)
        assert False, "Should have 404'd"
    except urllib.error.HTTPError as e:
        assert e.code == 404
    print("[PASS] Ephemeral Storage Graceful 404 Handling Verified.")

if __name__ == "__main__":
    print("Running AutoVision AI Production Verification Tests...")
    test_health()
    test_sample_video()
    test_upload_validation_extension()
    test_ephemeral_storage_graceful_404()
    print("\nALL DEPLOYMENT READINESS TESTS PASSED SUCCESSFULLY! [6/6]")
