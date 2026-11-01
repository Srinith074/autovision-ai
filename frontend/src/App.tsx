import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, PageId } from './components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { DetectionPage } from './pages/DetectionPage';
import { ResultsPage } from './pages/ResultsPage';
import { AboutPage } from './pages/AboutPage';
import { api } from './services/api';
import { HealthStatus, DetectionResult } from './types';

export function App() {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [latestResult, setLatestResult] = useState<DetectionResult | null>(null);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  useEffect(() => {
    checkHealthAndResult();
    const interval = setInterval(checkHealthAndResult, 8000);
    return () => clearInterval(interval);
  }, []);

  const checkHealthAndResult = async () => {
    try {
      const healthData = await api.getHealth();
      setHealth(healthData);
      setIsBackendConnected(true);

      const latest = await api.getLatestResult();
      if (latest && latest.session_id) {
        setLatestResult(latest);
      }
    } catch (err) {
      setIsBackendConnected(false);
    }
  };

  const handleDetectionComplete = async (sessionId: string) => {
    try {
      const res = await api.getResults(sessionId);
      setLatestResult(res);
    } catch (err) {
      console.error('Failed to fetch completed results:', err);
    }
  };

  const pageTitles: Record<PageId, string> = {
    dashboard: 'AutoVision AI Dashboard',
    detection: 'Vehicle Detection Pipeline',
    results: 'Detection Results & Download',
    about: 'About Project & Methodology',
  };

  return (
    <div className="flex min-h-screen bg-[#070b14] text-slate-100 antialiased selection:bg-cyan-500 selection:text-slate-950">
      {/* 4-Page Sidebar */}
      <Sidebar currentPage={currentPage} onSelectPage={setCurrentPage} />

      {/* Main View Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar
          pageTitle={pageTitles[currentPage]}
          health={health}
          isBackendConnected={isBackendConnected}
          onRefreshHealth={checkHealthAndResult}
          onNavigateToUpload={() => setCurrentPage('detection')}
        />

        <main className="flex-1 p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {currentPage === 'dashboard' && (
            <DashboardPage
              latestResult={latestResult}
              onNavigateToDetection={() => setCurrentPage('detection')}
              onNavigateToResults={() => setCurrentPage('results')}
            />
          )}

          {currentPage === 'detection' && (
            <DetectionPage
              onDetectionComplete={handleDetectionComplete}
              onNavigateToResults={() => setCurrentPage('results')}
            />
          )}

          {currentPage === 'results' && (
            <ResultsPage
              result={latestResult}
              onNavigateToDetection={() => setCurrentPage('detection')}
            />
          )}

          {currentPage === 'about' && <AboutPage />}
        </main>
      </div>
    </div>
  );
}

export default App;
