import urllib.request
import json
import time

def main():
    payload = {
        "use_sample": True,
        "conf_threshold": 0.28,
        "is_calibrated": True,
        "meters_per_pixel": 0.05
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/detection/start",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    res = json.loads(urllib.request.urlopen(req).read().decode())
    session_id = res["session_id"]
    print(f"Triggered detection session: {session_id}")

    # Monitor for up to 20 seconds
    for _ in range(10):
        time.sleep(2)
        stat = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8000/api/detection/status/{session_id}").read().decode())
        print(f"Frames: {stat['processed_frames']}/{stat['total_frames']} ({stat['progress_percent']}%) | Total Vehicles: {stat['total_vehicles']} | FPS: {stat['current_fps']} | Status: {stat['status']}")
        if stat["status"] in ["completed", "failed", "stopped"]:
            break

if __name__ == "__main__":
    main()
