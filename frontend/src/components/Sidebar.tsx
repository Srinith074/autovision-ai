import React from 'react';
import {
  LayoutDashboard,
  ScanEye,
  FileCheck2,
  BookOpen,
  Radar
} from 'lucide-react';

export type PageId = 'dashboard' | 'detection' | 'results' | 'about';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onSelectPage }) => {
  const navItems: { id: PageId; label: string; icon: React.ReactNode; badge?: string }[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <LayoutDashboard className="w-4 h-4 text-cyan-400" />,
    },
    {
      id: 'detection',
      label: 'Vehicle Detection',
      icon: <ScanEye className="w-4 h-4 text-blue-400" />,
      badge: 'YOLO',
    },
    {
      id: 'results',
      label: 'Results & Video',
      icon: <FileCheck2 className="w-4 h-4 text-emerald-400" />,
    },
    {
      id: 'about',
      label: 'About Project',
      icon: <BookOpen className="w-4 h-4 text-purple-400" />,
    },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-[#070b14] flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-950/60 ring-1 ring-cyan-400/30">
            <Radar className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="text-base font-extrabold tracking-wide text-white flex items-center gap-1.5">
              AUTOVISION<span className="text-cyan-400">AI</span>
            </div>
            <div className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">
              Vehicle Detection
            </div>
          </div>
        </div>

        {/* 4 Page Nav List */}
        <nav className="p-3.5 space-y-2 mt-2">
          {navItems.map((item) => {
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectPage(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/15 to-blue-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-950/50'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Course Info Card */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/50">
        <div className="rounded-xl p-3 bg-slate-900/80 border border-slate-800 text-xs space-y-1">
          <div className="flex items-center justify-between text-slate-200 font-bold">
            <span>B.Tech Project</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />
          </div>
          <div className="text-[10px] text-slate-400 leading-tight">
            Third-Year Deep Learning Course Prototype
          </div>
        </div>
      </div>
    </aside>
  );
};
