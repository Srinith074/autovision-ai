# AutoVision AI - Production Deployment Guide
Autonomous Vehicle Detection Using Deep Learning

This guide outlines step-by-step instructions for deploying the **AutoVision AI** application into production using **Render** for the FastAPI backend and **Vercel** for the React 19 + Vite frontend.

---

## Architecture Overview

```
 [ Client Browser ]
        │
        ├─────────────────────────────────────────────────┐
        ▼ (HTTPS)                                         ▼ (HTTPS)
┌──────────────────────────┐                    ┌──────────────────────────┐
│     Vercel Frontend      │                    │      Render Backend      │
│     (React 19 + Vite)    │ ──── API Calls ──> │   (FastAPI + YOLOv8)     │
│  autovision.vercel.app   │                    │ autovision.onrender.com  │
└──────────────────────────┘                    └──────────────────────────┘
                                                              │
                                                ┌─────────────┴─────────────┐
                                                ▼                           ▼
                                      [ YOLOv8 Weights ]          [ Ephemeral Storage ]
                                     (models/yolov8n.pt)          (uploads/ & outputs/)
```

---

## 1. Backend Deployment: Render (FastAPI + YOLOv8)

Render hosts the Python backend as a Web Service.

### Deployment Method A: Using `render.yaml` (Blueprint)
The repository contains a `render.yaml` file in the root directory.
1. Connect your GitHub repository in the Render Dashboard.
2. Select **Blueprints** and choose this repository.
3. Render reads `render.yaml` and provisions the web service automatically.

### Deployment Method B: Manual Web Service Setup
1. In the Render Dashboard, click **New +** -> **Web Service**.
2. Select your cloned GitHub repository.
3. Configure settings:
   * **Name:** `autovision-ai-backend`
   * **Language/Runtime:** `Python 3`
   * **Region:** Any (e.g. `Oregon (US West)` or `Frankfurt (EU)`)
   * **Branch:** `main` (or your active branch)
   * **Root Directory:** `backend` (or leave blank if repository root)
   * **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   * **Start Command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   * **Health Check Path:** `/api/health`

### Environment Variables on Render
Add the following key-value pairs under **Environment** in the Render Dashboard:

| Key | Value | Description |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` | Ensures compatible Python runtime with prebuilt wheels |
| `PORT` | `10000` | (Render sets `$PORT` automatically; backend binds dynamically) |
| `HOST` | `0.0.0.0` | Binds to all network interfaces |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` | Comma-separated list of allowed frontend URLs |
| `MODEL_PATH` | `models/yolov8n.pt` | Path or name (e.g. `yolov8n.pt` auto-downloads if absent) |
| `MAX_UPLOAD_SIZE_MB` | `250` | Maximum video upload size in MB |

> [!TIP]
> **OpenCV on Render Linux:**
> `backend/requirements.txt` specifies `opencv-python-headless>=4.9.0`. This prevents the common Linux container crash (`ImportError: libGL.so.1: cannot open shared object file`) that occurs when GUI OpenCV packages are used on headless cloud instances.

---

## 2. Frontend Deployment: Vercel (React 19 + Vite)

Vercel hosts the single-page application (SPA).

### Step-by-Step Vercel Setup:
1. Log in to [Vercel](https://vercel.com) and click **Add New...** -> **Project**.
2. Import your GitHub repository.
3. In **Project Configuration**:
   * **Framework Preset:** `Vite`
   * **Root Directory:** Click "Edit" and choose `frontend`.
   * **Build Command:** `npm run build` (or Vite default)
   * **Output Directory:** `dist`
   * **Install Command:** `npm install`
4. Under **Environment Variables**, add:
   * **Key:** `VITE_API_URL`
   * **Value:** `https://your-backend-name.onrender.com` *(your actual Render backend URL, without trailing slash)*
5. Click **Deploy**.

> [!NOTE]
> **SPA Client-Side Routing:**
> The repository includes `frontend/vercel.json` with rewrite rules:
> ```json
> {
>   "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
> }
> ```
> This ensures that directly refreshing subpaths like `/detection`, `/results`, or `/about` will not cause 404 errors on Vercel.

---

## 3. Storage Architecture: Handling Ephemeral Disks

Render free and standard Web Services utilize **ephemeral disks**:
* When an instance restarts, re-deploys, or wakes up from auto-sleep, local files stored in `uploads/`, `outputs/videos/`, and `reports/` are wiped clean.
* **AutoVision AI Design Accommodations:**
  1. **Graceful 404 Handling:** All result and download endpoints (`/api/results/{id}`, `/api/download/video/{id}`, `/api/download/csv/{id}`) inspect file existence and return clear HTTP 404 responses explaining the ephemeral lifecycle instead of crashing.
  2. **In-Memory Registry:** Sessions are safely isolated.
  3. **Sample Video Persistence:** The benchmark video `input_video.mp4` is included in git so that users can test the application immediately after a fresh cold start without uploading a separate file.
  4. **Production Persistent Storage (Optional Upgrade):**
     For high-volume multi-tenant deployments requiring long-term video archival, configure Render Persistent Disks (attached to `/outputs` and `/uploads`) or connect an Amazon S3 / Cloudflare R2 bucket.

---

## 4. Production Verification Commands

Run these local commands to verify that production builds and endpoints pass before committing:

### 1. Test Frontend Production Build:
```bash
cd frontend
npm run build
```
*Expected Output:* `✓ built in ~600ms` with zero TypeScript or bundling errors.

### 2. Test Backend Health & Endpoints:
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
In a separate terminal:
```bash
python backend/tests/test_deployment.py
```
*Expected Output:*
```
[PASS] Health Check & Vercel CORS Verified.
[PASS] Benchmark Sample Video Endpoint Verified.
[PASS] Invalid File Extension Rejection (400) Verified.
[PASS] Ephemeral Storage Graceful 404 Handling Verified.

ALL DEPLOYMENT READINESS TESTS PASSED SUCCESSFULLY! [6/6]
```
