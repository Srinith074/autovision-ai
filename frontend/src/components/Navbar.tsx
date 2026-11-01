import React from 'react';
import { Cpu, RefreshCw, Upload, Shield } from 'lucide-react';
import { HealthStatus } from '../types';

interface NavbarProps {
  pageTitle: string;
  health: HealthStatus | null;
  isBackendConnected: boolean;
  onRefreshHealth: () => void;
  onNavigateToUpload: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  pageTitle,
  health,
  isBackendConnected,
  onRefreshHealth,
  onNavigateToUpload,
}) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-[#090d16]/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      <div>
        <h1 className="text-base font-bold text-white flex items-center gap-2 m-0 tracking-tight">
          <span>{pageTitle}</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
            YOLOv8
          </span>
        </h1>
      </div>

      <div className="flex items-center gap-3">
        {/* Backend Connectivity Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              isBackendConnected ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-500'
            }`}
          />
          <span className="text-slate-300 font-medium">
            {isBackendConnected ? 'FastAPI Connected' : 'Disconnected'}
          </span>
          <button
            onClick={onRefreshHealth}
            title="Refresh connection"
            className="text-slate-500 hover:text-cyan-400 transition-colors ml-1 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Compute Device */}
        {health && (
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-400">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>{health.compute_device}</span>
          </div>
        )}

        {/* Quick Upload Button */}
        <button
          onClick={onNavigateToUpload}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/20 transition-all cursor-pointer"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Upload Video</span>
        </button>
      </div>
    </header>
  );
};
