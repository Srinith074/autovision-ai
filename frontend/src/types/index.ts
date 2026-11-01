export type VehicleClass = 'Car' | 'Motorcycle' | 'Bus' | 'Truck' | 'Bicycle';

export interface HealthStatus {
  status: string;
  system: string;
  compute_device: string;
  model_loaded: string;
  sample_video_available: boolean;
}

export interface TrackedVehicle {
  track_id: number;
  class: string;
  confidence: number;
  first_frame: number;
  last_frame: number;
}

export interface DetectionResult {
  session_id: string;
  source_name: string;
  status: 'processing' | 'completed' | 'failed';
  progress_percent: number;
  processed_frames: number;
  total_frames: number;
  current_fps: number;
  total_vehicles: number;
  class_counts: {
    Car: number;
    Truck: number;
    Bus: number;
    Motorcycle: number;
    Bicycle: number;
  };
  mean_confidence: number;
  duration_seconds: number;
  video_url: string;
  csv_url: string;
  tracked_vehicles: TrackedVehicle[];
  error?: string | null;
  available?: boolean;
}
