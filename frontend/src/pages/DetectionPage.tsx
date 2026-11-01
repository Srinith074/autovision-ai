import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  FileVideo,
  Play,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sliders,
  ArrowRight,
  Eye
} from 'lucide-react';
import { api } from '../services/api';
import { DetectionResult } from '../types';

interface DetectionPageProps {
  onDetectionComplete: (sessionId: string) => void;
  onNavigateToResults: () => void;
}

export const DetectionPage: React.FC<DetectionPageProps> = ({
  onDetectionComplete,
  onNavigateToResults,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [originalVideoUrl, setOriginalVideoUrl] = useState<string | null>(null);
  const [uploadedPath, setUploadedPath] = useState<string | null>(null);
  const [useSample, setUseSample] = useState<boolean>(true);
  const [sampleInfo, setSampleInfo] = useState<{ filename: string; size_mb: number } | null>(null);

  // Settings
  const [confThreshold, setConfThreshold] = useState<number>(0.30);

  // Execution state
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<DetectionResult | null>(null);
  const [uploadLoading, setUploadLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.getSampleVideo()
      .then(info => setSampleInfo({ filename: info.filename, size_mb: info.size_mb }))
      .catch(() => setSampleInfo(null));
  }, []);

  // Poll progress when processing
  useEffect(() => {
    let interval: any = null;
    if (isProcessing && currentSessionId) {
      interval = setInterval(async () => {
        try {
          const res = await api.getStatus(currentSessionId);
          setStatus(res);
          if (res.status === 'completed') {
            setIsProcessing(false);
            onDetectionComplete(currentSessionId);
          } else if (res.status === 'failed') {
            setIsProcessing(false);
            setErrorMessage(res.error || 'Video processing encountered an error.');
          }
        } catch (err) {
          // ignore transient poll errors
        }
      }, 750);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isProcessing, currentSessionId]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setUseSample(false);
    setUploadLoading(true);
    setErrorMessage(null);

    // Create local object URL for previewing original video
    const objectUrl = URL.createObjectURL(file);
    setOriginalVideoUrl(objectUrl);

    try {
      const res = await api.uploadVideo(file);
      setUploadedPath(res.video_path);
    } catch (err: any) {
      setErrorMessage(err.message || 'Video upload failed.');
      setSelectedFile(null);
      setOriginalVideoUrl(null);
    } finally {
      setUploadLoading(false);
    }
  };

  const handleStartDetection = async () => {
    setErrorMessage(null);
    setIsProcessing(true);
    setStatus(null);

    try {
      const res = await api.startDetection({
        video_path: uploadedPath || undefined,
        use_sample: useSample,
        conf_threshold: confThreshold,
      });
      setCurrentSessionId(res.session_id);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to start detection pipeline.');
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight m-0 flex items-center gap-2">
          <FileVideo className="w-5 h-5 text-blue-400" />
          <span>Vehicle Detection & Video Processing</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Upload traffic video footage or use the benchmark sample to execute the deep learning YOLOv8 detection pipeline.
        </p>
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Upload and Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Step 1: Video Selection */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider m-0">
            1. Select Input Video
          </h3>

          {/* Benchmark Video Option */}
          <div
            onClick={() => {
              setUseSample(true);
              setSelectedFile(null);
              setOriginalVideoUrl(null);
              setUploadedPath(null);
            }}
            className={`p-4 rounded-xl border text-xs cursor-pointer transition-all ${
              useSample
                ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-200'
                : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between font-semibold mb-1">
              <span>Benchmark Highway Video</span>
              {useSample && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono">
                  ACTIVE
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-400">
              input_video.mp4 {sampleInfo ? `(${sampleInfo.size_mb} MB)` : ''}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">
              Ready-to-run highway traffic video with cars, buses, and trucks.
            </div>
          </div>

          {/* Upload Box */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className={`p-6 rounded-xl border-2 border-dashed text-center text-xs cursor-pointer transition-all ${
              !useSample && selectedFile
                ? 'bg-blue-500/10 border-blue-500/50 text-blue-200'
                : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp4,.avi,.mov"
              onChange={handleFileUpload}
              className="hidden"
            />
            <Upload className="w-8 h-8 mx-auto mb-2 text-slate-500" />
            {uploadLoading ? (
              <div className="text-cyan-400 font-semibold flex items-center justify-center gap-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Uploading File...
              </div>
            ) : selectedFile ? (
              <div>
                <div className="font-semibold text-slate-200">{selectedFile.name}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready
                </div>
              </div>
            ) : (
              <div>
                <div className="font-semibold text-slate-300">Drag & Drop or Click to Upload</div>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  Supports MP4, AVI, MOV (Max 250MB)
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Step 2: Settings & Execution */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md space-y-5">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider m-0 flex items-center gap-2">
            <Sliders className="w-3.5 h-3.5 text-cyan-400" />
            <span>2. Detection Settings & Run</span>
          </h3>

          {/* Confidence Slider */}
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between text-slate-300">
              <span>Confidence Threshold:</span>
              <span className="font-mono text-cyan-400 font-bold">{Math.round(confThreshold * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.90"
              step="0.05"
              value={confThreshold}
              onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
              disabled={isProcessing}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <div className="text-[10px] text-slate-500">
              Higher values filter out uncertain bounding box candidates.
            </div>
          </div>

          {/* Model Info */}
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs space-y-1">
            <div className="text-slate-300 font-semibold">Active Model: YOLOv8 Nano</div>
            <div className="text-[10px] text-slate-400">
              Classes: <span className="text-cyan-300">Car, Motorcycle, Bus, Truck, Bicycle</span>
            </div>
          </div>

          {/* Start Detection Action */}
          <div className="pt-2">
            <button
              onClick={handleStartDetection}
              disabled={isProcessing || uploadLoading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/25 transition-all cursor-pointer disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{isProcessing ? 'Processing Video...' : 'Start Detection'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Progress & Live Processing Telemetry */}
      {(isProcessing || status) && (
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <div className="text-xs text-slate-400 font-mono">
                Session ID: {status?.session_id || currentSessionId}
              </div>
              <div className="text-sm font-bold text-white mt-0.5">
                {status?.status === 'completed' ? 'Analysis Complete' : 'Processing Frames with YOLOv8...'}
              </div>
            </div>

            {status?.status === 'completed' && (
              <button
                onClick={onNavigateToResults}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs cursor-pointer shadow-md"
              >
                <span>View Full Results</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Progress Bar */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-slate-300">
                Frames: {status?.processed_frames || 0} / {status?.total_frames || '...'}
              </span>
              <span className="font-mono text-cyan-400">{status?.progress_percent || 0}%</span>
            </div>
            <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
                style={{ width: `${status?.progress_percent || 0}%` }}
              />
            </div>
          </div>

          {/* Real-time counters */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400">Total Counted</div>
              <div className="text-xl font-bold text-cyan-400 font-mono mt-0.5">
                {status?.total_vehicles || 0}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400">Processing Rate</div>
              <div className="text-xl font-bold text-emerald-400 font-mono mt-0.5">
                {status?.current_fps || 0} FPS
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400">Cars Detected</div>
              <div className="text-xl font-bold text-blue-400 font-mono mt-0.5">
                {status?.class_counts?.Car || 0}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400">Trucks Detected</div>
              <div className="text-xl font-bold text-amber-400 font-mono mt-0.5">
                {status?.class_counts?.Truck || 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Video Previews Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Original Video Preview */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
            <Eye className="w-3.5 h-3.5 text-cyan-400" />
            <span>Original Video Preview</span>
          </div>
          <div className="rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 aspect-video flex items-center justify-center shadow-lg">
            {originalVideoUrl ? (
              <video src={originalVideoUrl} controls className="w-full h-full object-contain" />
            ) : useSample ? (
              <div className="text-center p-6 space-y-2">
                <FileVideo className="w-8 h-8 text-cyan-400 mx-auto" />
                <div className="text-xs text-slate-300 font-semibold">input_video.mp4</div>
                <div className="text-[10px] text-slate-500">Benchmark highway traffic sample</div>
              </div>
            ) : (
              <div className="text-xs text-slate-500">No original video selected</div>
            )}
          </div>
        </div>

        {/* Processed Video Preview */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Annotated Output Preview</span>
          </div>
          <div className="rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 aspect-video flex items-center justify-center shadow-lg">
            {status?.status === 'completed' && status.video_url ? (
              <video src={api.resolveUrl(status.video_url)} controls className="w-full h-full object-contain" />
            ) : (
              <div className="text-xs text-slate-500 text-center p-6">
                Processed video with bounding boxes will render here after detection completes.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
