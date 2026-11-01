import { HealthStatus, DetectionResult } from '../types';

/**
 * AutoVision AI - Production API Client
 * Configurable via VITE_API_URL with automatic fallback to deployed Render backend.
 */
const DEFAULT_API_HOST = 'https://autovision-ai-0xcx.onrender.com';
const envApiUrl = import.meta.env.VITE_API_URL?.trim();
const rawHost = (envApiUrl || DEFAULT_API_HOST).replace(/\/$/, '');

// Normalize host URL (remove trailing /api if user added it to the root)
export const API_HOST_URL = rawHost.endsWith('/api') ? rawHost.slice(0, -4) : rawHost;
export const API_BASE_URL = `${API_HOST_URL}/api`;

/**
 * Resolves any relative API or media path against API_HOST_URL.
 * Handles both absolute URLs and relative paths cleanly.
 */
export const resolveApiUrl = (path: string): string => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_HOST_URL}${cleanPath}`;
};

export const api = {
  hostUrl: API_HOST_URL,
  baseUrl: API_BASE_URL,
  resolveUrl: resolveApiUrl,

  getVideoDownloadUrl(sessionId: string): string {
    return resolveApiUrl(`/api/download/video/${sessionId}`);
  },

  getCsvDownloadUrl(sessionId: string): string {
    return resolveApiUrl(`/api/download/csv/${sessionId}`);
  },

  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`Backend offline (${res.status})`);
    return res.json();
  },

  async getSampleVideo(): Promise<{ filename: string; size_mb: number; description: string }> {
    const res = await fetch(`${API_BASE_URL}/sample-video`);
    if (!res.ok) throw new Error('Benchmark sample video unavailable on backend');
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
    const res = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `Upload failed with HTTP ${res.status}` }));
      throw new Error(err.detail || 'Video upload failed');
    }
    const data = await res.json();
    if (!data.video_path) {
      throw new Error('Upload succeeded but server did not return video_path');
    }
    return data;
  },

  async startDetection(params: {
    video_path?: string;
    use_sample?: boolean;
    conf_threshold?: number;
  }): Promise<{ success: boolean; session_id: string; status: string; message: string }> {
    const res = await fetch(`${API_BASE_URL}/detect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `Detection failed with HTTP ${res.status}` }));
      throw new Error(err.detail || 'Failed to start detection');
    }
    return res.json();
  },

  async getStatus(sessionId: string): Promise<DetectionResult> {
    const res = await fetch(`${API_BASE_URL}/status/${sessionId}`);
    if (!res.ok) throw new Error(`Status check failed: HTTP ${res.status}`);
    return res.json();
  },

  async getResults(sessionId: string): Promise<DetectionResult> {
    const res = await fetch(`${API_BASE_URL}/results/${sessionId}`);
    if (!res.ok) throw new Error(`Results retrieval failed: HTTP ${res.status}`);
    return res.json();
  },

  async getLatestResult(): Promise<DetectionResult> {
    const res = await fetch(`${API_BASE_URL}/latest-result`);
    if (!res.ok) throw new Error('Failed to fetch latest result');
    return res.json();
  },
};
