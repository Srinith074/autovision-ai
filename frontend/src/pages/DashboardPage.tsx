import React from 'react';
import {
  Car,
  Truck,
  Bus,
  Bike,
  TrendingUp,
  Upload,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Play
} from 'lucide-react';
import { DetectionResult } from '../types';

interface DashboardPageProps {
  latestResult: DetectionResult | null;
  onNavigateToDetection: () => void;
  onNavigateToResults: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  latestResult,
  onNavigateToDetection,
  onNavigateToResults,
}) => {
  const hasAnalysis = Boolean(latestResult && latestResult.status === 'completed' && latestResult.total_vehicles !== undefined);

  const totalVehicles = hasAnalysis ? latestResult!.total_vehicles : 0;
  const carCount = hasAnalysis ? latestResult!.class_counts.Car || 0 : 0;
  const truckCount = hasAnalysis ? latestResult!.class_counts.Truck || 0 : 0;
  const busCount = hasAnalysis ? latestResult!.class_counts.Bus || 0 : 0;
  const motorcycleCount = hasAnalysis ? latestResult!.class_counts.Motorcycle || 0 : 0;
  const bicycleCount = hasAnalysis ? latestResult!.class_counts.Bicycle || 0 : 0;

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Hero Welcome Card */}
      <div className="p-7 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0b1329] to-slate-900 border border-slate-800 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            B.Tech Deep Learning Course Project
          </div>
          <h2 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight m-0">
            AutoVision AI – Autonomous Vehicle Detection
          </h2>
          <p className="text-xs lg:text-sm text-slate-400 max-w-2xl leading-relaxed m-0">
            A deep-learning-driven intelligent vehicle monitoring prototype utilizing Ultralytics YOLOv8 object detection, OpenCV video stream processing, and multi-object tracking to detect, classify, and count vehicles in roadway footage.
          </p>
        </div>

        <button
          onClick={onNavigateToDetection}
          className="flex items-center gap-2 px-5 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all cursor-pointer shrink-0"
        >
          <Upload className="w-4 h-4" />
          <span>Upload Video</span>
        </button>
      </div>

      {/* Primary KPI Detection Statistics */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider m-0">
            Current Analysis Detection Statistics
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            {hasAnalysis ? `Session: ${latestResult?.session_id}` : 'No Active Session'}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Total Vehicles */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
              <span>Total Count</span>
              <TrendingUp className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-3xl font-extrabold text-white font-mono">
              {totalVehicles}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Unique Tracked</div>
          </div>

          {/* Cars */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
              <span>Cars</span>
              <Car className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-3xl font-extrabold text-blue-400 font-mono">
              {carCount}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Passenger cars</div>
          </div>

          {/* Trucks */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
              <span>Trucks</span>
              <Truck className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-3xl font-extrabold text-amber-400 font-mono">
              {truckCount}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Heavy freight</div>
          </div>

          {/* Buses */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
              <span>Buses</span>
              <Bus className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-3xl font-extrabold text-emerald-400 font-mono">
              {busCount}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Transit vehicles</div>
          </div>

          {/* Motorcycles */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
              <span>Motorcycles</span>
              <Bike className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-3xl font-extrabold text-purple-400 font-mono">
              {motorcycleCount}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Two-wheelers</div>
          </div>

          {/* Bicycles */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
              <span>Bicycles</span>
              <Bike className="w-4 h-4 text-yellow-400" />
            </div>
            <div className="text-3xl font-extrabold text-yellow-400 font-mono">
              {bicycleCount}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Non-motorized</div>
          </div>
        </div>
      </div>

      {/* Recent Analysis Section */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider m-0">
            Recent Analysis Summary
          </h3>
          {hasAnalysis && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
              <CheckCircle2 className="w-4 h-4" />
              Completed
            </span>
          )}
        </div>

        {hasAnalysis ? (
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1 text-xs">
              <div className="text-slate-200 font-bold text-sm">
                {latestResult?.source_name}
              </div>
              <div className="text-slate-400">
                Duration: <span className="font-mono text-slate-200">{latestResult?.duration_seconds}s</span> • Throughput:{' '}
                <span className="font-mono text-slate-200">{latestResult?.current_fps} FPS</span> • Mean Confidence:{' '}
                <span className="font-mono text-cyan-400 font-semibold">{latestResult?.mean_confidence}%</span>
              </div>
            </div>

            <button
              onClick={onNavigateToResults}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-cyan-300 border border-slate-700 text-xs font-semibold transition-all cursor-pointer"
            >
              <span>View Full Results</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <div className="py-8 text-center space-y-2 border border-dashed border-slate-800 rounded-xl">
            <AlertCircle className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-sm font-semibold text-slate-300">No Video Analyzed Yet</div>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Upload a traffic video or select the benchmark sample video to begin deep learning vehicle detection.
            </p>
            <div className="pt-2">
              <button
                onClick={onNavigateToDetection}
                className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs cursor-pointer"
              >
                Start New Detection
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
