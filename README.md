# AutoVision AI
### Autonomous Vehicle Detection Using Deep Learning
**Third-Year B.Tech Deep Learning Course Project**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Ultralytics YOLOv8](https://img.shields.io/badge/AI_Vision-Ultralytics_YOLOv8-blue.svg)](https://docs.ultralytics.com)
[![OpenCV](https://img.shields.io/badge/Computer_Vision-OpenCV_4-red.svg?logo=opencv&logoColor=white)](https://opencv.org)
[![React 19](https://img.shields.io/badge/Frontend-React_19_+_Vite-61dafb.svg?logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS_v4-38bdf8.svg?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 1. Project Overview & Academic Attribution

**AutoVision AI** is a focused, deep-learning-based vehicle detection academic prototype developed for a third-year B.Tech Deep Learning course. It processes uploaded road traffic videos, extracts frames using OpenCV, runs real-time object detection using a pretrained **Ultralytics YOLOv8** convolutional network, classifies vehicles, renders bounding boxes with confidence scores, tracks vehicles across frames to ensure non-duplicate vehicle counting, and provides downloadable annotated output videos and structured CSV reports.

### Academic Lineage & MIT License Attribution
This project modernizes the open-source repository:
* **Original Repository:** [vehicle_counting_tensorflow](https://github.com/ahmetozlu/vehicle_counting_tensorflow) by **Ahmet Özlü** (2018)
* **Original License:** MIT License (retained in full in [LICENSE](file:///c:/Users/titoo/OneDrive/Documents/projects/vehicle_counting_tensorflow-master/LICENSE))
* **Modernization Summary:** Upgraded from deprecated TensorFlow 1.x frozen protobuf graphs (`ssd_mobilenet_v1_coco_2018_01_28`) to an ultra-fast, multi-class **Ultralytics YOLOv8** model with ByteTrack tracking, FastAPI microservices, and a clean command-center dark dashboard built with React 19, TypeScript, and Tailwind CSS.

---

## 2. Essential Workflow & Features

The complete demonstration follows this straightforward flow:
$$\text{Upload Video} \longrightarrow \text{Run YOLO Detection} \longrightarrow \text{Identify Vehicles} \longrightarrow \text{Draw Bounding Boxes} \longrightarrow \text{Count Vehicles} \longrightarrow \text{Display Results} \longrightarrow \text{Download Processed Video \& CSV}$$

* **Supported Vehicle Classes:**
  * **Car** (COCO #2)
  * **Motorcycle** (COCO #3)
  * **Bus** (COCO #5)
  * **Truck** (COCO #7)
  * **Bicycle** (COCO #1)
* **Accurate Vehicle Counting:** Uses multi-object tracking IDs (`persist=True`) across frames so vehicles are not repeatedly counted on every frame.
* **Format Support:** Supports MP4, AVI, and MOV video uploads (up to 250MB), and includes the benchmark sample video (`input_video.mp4`) for 1-click evaluation without file searching.

---

## 3. Four Streamlined Dashboard Pages

1. **Dashboard:**
   * Project title and B.Tech DL project description.
   * Total vehicles detected in the current/latest analysis.
   * Number of cars, motorcycles, buses, trucks, and bicycles.
   * Quick action button to upload a video.
   * Recent analysis summary card with direct navigation to results.
2. **Vehicle Detection:**
   * Drag-and-drop video upload (MP4, AVI, MOV) with file information (size, filename).
   * One-click option to select the benchmark highway video (`input_video.mp4`).
   * Confidence threshold slider control (10% to 90%).
   * Start detection button.
   * Real-time progress bar (frame counter, percentage, FPS, live vehicle count).
   * Original video preview and processed video preview.
3. **Results:**
   * Annotated output video player with bounding boxes and HUD.
   * Total detected vehicles and class-wise counts.
   * Mean detection confidence percentage.
   * Download processed video button (`.mp4`).
   * Download CSV results button (`.csv`).
   * Detected vehicles breakdown table with Track IDs and active frame ranges.
4. **About Project:**
   * Problem statement on automated traffic monitoring.
   * Project objective.
   * Deep learning methodology (YOLO convolutional network, OpenCV frame decoding, ByteTrack multi-object tracking).
   * Vehicle classification taxonomy and MIT license attribution to Ahmet Özlü.

---

## 4. Technology Stack

* **AI & Computer Vision:** Python 3.13+, PyTorch 2.15, Ultralytics YOLOv8 (`yolov8n.pt` ~6.2MB), OpenCV (`cv2`), NumPy.
* **Backend:** Python FastAPI, Uvicorn, Pydantic v2.
* **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons.

---

## 5. Directory Structure

```
vehicle_counting_tensorflow-master/
├── backend/
│   ├── app/
│   │   ├── detection/
│   │   │   └── pipeline.py     # YOLOv8 inference, ByteTrack tracking & annotations
│   │   └── main.py             # FastAPI REST endpoints & file serving
│   └── requirements.txt        # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # Navbar, Sidebar
│   │   ├── pages/              # Exactly 4 pages:
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── DetectionPage.tsx
│   │   │   ├── ResultsPage.tsx
│   │   │   └── AboutPage.tsx
│   │   ├── services/api.ts     # REST client
│   │   ├── types/index.ts      # TypeScript interfaces
│   │   ├── App.tsx             # Master layout and routing
│   │   └── index.css           # Tailwind CSS dark command-center theme
│   ├── package.json
│   └── vite.config.ts
├── models/
│   └── yolov8n.pt              # Lightweight pretrained YOLO weights (~6.2 MB)
├── outputs/
│   └── videos/                 # Annotated output MP4 videos
├── reports/                    # Exported session CSV reports
├── uploads/                    # User uploaded traffic videos
├── tests/
│   ├── test_detection_pipeline.py # Standalone detection test
│   └── test_academic_flow.py      # End-to-end academic workflow test
├── input_video.mp4             # Benchmark highway traffic video (Ahmet Özlü)
├── LICENSE                     # Original MIT License (c) 2018 Ahmet Özlü
└── README.md                   # Project documentation
```

---

## 6. Installation & Execution Guide

### Step 1: Backend Setup
```bash
# 1. Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies (if not already installed)
pip install -r backend/requirements.txt

# 3. Start FastAPI server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Backend will be live at: `http://127.0.0.1:8000` (API Docs: `http://127.0.0.1:8000/docs`).

### Step 2: Frontend Setup
In a second terminal window:
```bash
cd frontend

# Install packages (if not already installed)
npm install

# Start Vite dev server
npm run dev
```
Open your browser at: `http://127.0.0.1:5173/`.

---

## 7. Verification & Evaluation Results

Run the end-to-end automated academic workflow verification script:

```bash
.\.venv\Scripts\python.exe tests/test_academic_flow.py
```

### Verified Benchmark Output (`input_video.mp4`):
* **Resolution:** 640x352 @ 24.0 FPS (905 total frames)
* **Inference Rate:** ~13.2 FPS on standard CPU
* **Total Vehicles Counted:** 11 unique vehicles
* **Mean Confidence:** 64.1%
* **Processing Duration:** 68.6 seconds
* **Annotated Video Generated:** `outputs/videos/session_8a397d56_annotated.mp4`
* **CSV Report Generated:** `reports/session_8a397d56_report.csv`
* **API Downloads:** Both CSV (352 bytes) and MP4 video (HTTP 200 OK) verified.

---

## 8. Production Deployment Guide (Vercel & Render)

AutoVision AI is pre-configured for zero-friction cloud deployment. See [DEPLOYMENT.md](file:///c:/Users/titoo/OneDrive/Documents/projects/vehicle_counting_tensorflow-master/DEPLOYMENT.md) for full details.

### Render Backend (FastAPI Web Service)
* **Build Command:** `pip install -r backend/requirements.txt`
* **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
* **Health Check Path:** `/api/health`
* **Environment Variables:**
  * `PORT`: Automatically assigned by Render (default 10000)
  * `HOST`: `0.0.0.0`
  * `ALLOWED_ORIGINS`: `https://your-frontend.vercel.app` (All `*.vercel.app` domains automatically allowed by regex)
  * `MODEL_PATH`: `models/yolov8n.pt` (or `yolov8n.pt` to auto-download)
  * `MAX_UPLOAD_SIZE_MB`: `250`

### Vercel Frontend (React 19 + Vite SPA)
* **Root Directory:** `frontend`
* **Build Command:** `npm run build`
* **Output Directory:** `dist`
* **Environment Variable:**
  * `VITE_API_URL`: `https://your-backend.onrender.com`
* **SPA Routing:** Handled via `frontend/vercel.json` rewrites.

#   a u t o v i s i o n - a i  
 