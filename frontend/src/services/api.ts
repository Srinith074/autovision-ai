import { HealthStatus, DetectionResult } from '../types';

/**
 * AutoVision AI - API Client
 * Configurable for local dev (Vite proxy) and production (Vercel -> Render).
 * Reads base URL from VITE_API_URL environment variable.
 */
const RAW_API_URL = import.meta.env.VITE_API_URL || '';
export const API_BASE_URL = RAW_API_URL.replace(/\/$/, '');

/**
 * Resolves any relative API or media path against VITE_API_URL if configured.
 * Handles both absolute URLs and relative paths cleanly.
 */
export const resolveApiUrl = (path: string): string => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return API_BASE_URL ? `${API_BASE_URL}${cleanPath}` : cleanPath;
};

const API_BASE = API_BASE_URL ? `${API_BASE_URL}/api` : '/api';

export const api = {
  resolveUrl: resolveApiUrl,

  getVideoDownloadUrl(sessionId: string): string {
    return resolveApiUrl(`/api/download/video/${sessionId}`);
  },

  getCsvDownloadUrl(sessionId: string): string {
    return resolveApiUrl(`/api/download/csv/${sessionId}`);
  },

  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Backend offline');
    return res.json();
  },

  async getSampleVideo(): Promise<{ filename: string; size_mb: number; description: string }> {
    const res = await fetch(`${API_BASE}/sample-video`);
    if (!res.ok) throw new Error('Sample video unavailable');
    return res.json();
  },

  async uploadVideo(file: File): Promise<{
    success: boolean;
    filename: string;
    original_name: string;
    size_mb: number;
    video_path: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async startDetection(params: {
    video_path?: string;
    use_sample?: boolean;
    conf_threshold?: number;
  }): Promise<{ success: boolean; session_id: string; status: string; message: string }> {
    const res = await fetch(`${API_BASE}/detect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to start detection' }));
      throw new Error(err.detail || 'Failed to start detection');
    }
    return res.json();
  },

  async getStatus(sessionId: string): Promise<DetectionResult> {
    const res = await fetch(`${API_BASE}/status/${sessionId}`);
    if (!res.ok) throw new Error('Status not found');
    return res.json();
  },

  async getResults(sessionId: string): Promise<DetectionResult> {
    const res = await fetch(`${API_BASE}/results/${sessionId}`);
    if (!res.ok) throw new Error('Results not found');
    return res.json();
  },

  async getLatestResult(): Promise<DetectionResult> {
    const res = await fetch(`${API_BASE}/latest-result`);
    if (!res.ok) throw new Error('Failed to fetch latest result');
    return res.json();
  },
};
