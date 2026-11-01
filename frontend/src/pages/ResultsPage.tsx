import React from 'react';
import {
  FileCheck2,
  Download,
  FileSpreadsheet,
  Car,
  Truck,
  Bus,
  Bike,
  TrendingUp,
  RotateCcw,
  AlertCircle
} from 'lucide-react';
import { DetectionResult } from '../types';
import { api, resolveApiUrl } from '../services/api';

interface ResultsPageProps {
  result: DetectionResult | null;
  onNavigateToDetection: () => void;
}

export const ResultsPage: React.FC<ResultsPageProps> = ({
  result,
  onNavigateToDetection,
}) => {
  if (!result || result.status !== 'completed') {
    return (
      <div className="p-12 text-center space-y-3 rounded-2xl bg-slate-900/80 border border-slate-800 max-w-xl mx-auto my-12">
        <AlertCircle className="w-10 h-10 text-slate-600 mx-auto" />
        <h3 className="text-base font-bold text-white m-0">No Completed Detection Results</h3>
        <p className="text-xs text-slate-400 max-w-sm mx-auto">
          Please run a vehicle detection analysis on a traffic video first to view annotated playback and exportable CSV telemetry.
        </p>
        <div className="pt-2">
          <button
            onClick={onNavigateToDetection}
            className="px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs cursor-pointer shadow-lg shadow-cyan-500/20"
          >
            Go to Vehicle Detection
          </button>
        </div>
      </div>
    );
  }

  const classCounts = result.class_counts || { Car: 0, Truck: 0, Bus: 0, Motorcycle: 0, Bicycle: 0 };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header and Download Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight m-0 flex items-center gap-2">
            <FileCheck2 className="w-5 h-5 text-emerald-400" />
            <span>Detection Results & Telemetry</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Session: <span className="font-mono text-cyan-300 font-semibold">{result.session_id}</span> • Source:{' '}
            <span className="text-slate-300">{result.source_name}</span>
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Download Video */}
          <a
            href={api.getVideoDownloadUrl(result.session_id)}
            download
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/20 transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Processed Video</span>
          </a>

          {/* Download CSV */}
          <a
            href={api.getCsvDownloadUrl(result.session_id)}
            download
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs transition-all"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-purple-400" />
            <span>Download CSV Results</span>
          </a>
        </div>
      </div>

      {/* Video Player */}
      <div className="rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 aspect-video shadow-2xl">
        <video
          src={api.getVideoDownloadUrl(result.session_id)}
          controls
          autoPlay
          className="w-full h-full object-contain"
        />
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="text-slate-400 text-xs">Total Vehicles</div>
          <div className="text-2xl font-extrabold text-cyan-400 font-mono mt-1">
            {result.total_vehicles}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Unique Counts</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="text-slate-400 text-xs">Cars</div>
          <div className="text-2xl font-bold text-blue-400 font-mono mt-1">
            {classCounts.Car || 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Passenger cars</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="text-slate-400 text-xs">Trucks</div>
          <div className="text-2xl font-bold text-amber-400 font-mono mt-1">
            {classCounts.Truck || 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Heavy trucks</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="text-slate-400 text-xs">Buses</div>
          <div className="text-2xl font-bold text-emerald-400 font-mono mt-1">
            {classCounts.Bus || 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Transit vehicles</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="text-slate-400 text-xs">Motorcycles</div>
          <div className="text-2xl font-bold text-purple-400 font-mono mt-1">
            {classCounts.Motorcycle || 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Two-wheelers</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="text-slate-400 text-xs">Mean Confidence</div>
          <div className="text-2xl font-bold text-white font-mono mt-1">
            {result.mean_confidence}%
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Model certainty</div>
        </div>
      </div>

      {/* Tracked Vehicles Table */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md overflow-hidden space-y-3 p-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider m-0">
            Detected Vehicles Breakdown
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            {result.tracked_vehicles?.length || 0} instances logged
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-4">Track ID</th>
                <th className="py-2.5 px-3">Vehicle Class</th>
                <th className="py-2.5 px-3">Mean Confidence</th>
                <th className="py-2.5 px-3">First Seen Frame</th>
                <th className="py-2.5 px-4">Last Seen Frame</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px] text-slate-300">
              {result.tracked_vehicles && result.tracked_vehicles.length > 0 ? (
                result.tracked_vehicles.map((v) => (
                  <tr key={v.track_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-4 font-bold text-cyan-400">#{v.track_id}</td>
                    <td className="py-2.5 px-3 font-sans font-semibold text-slate-200 uppercase">{v.class}</td>
                    <td className="py-2.5 px-3">{v.confidence}%</td>
                    <td className="py-2.5 px-3 text-slate-400">{v.first_frame}</td>
                    <td className="py-2.5 px-4 text-slate-400">{v.last_frame}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-500 font-sans">
                    No individual tracking records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={onNavigateToDetection}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Analyze Another Video</span>
          </button>
        </div>
      </div>
    </div>
  );
};
