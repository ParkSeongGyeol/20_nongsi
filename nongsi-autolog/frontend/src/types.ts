export type WorkState =
  | "OFFLINE"
  | "IDLE"
  | "MOVING"
  | "SPRAYING"
  | "PRESSURE_FAULT"
  | "SENSOR_FAULT"
  | "SESSION_FINISHED";

export interface Reading {
  id: number;
  device_id: string;
  sequence: number;
  timestamp: string;
  received_at: string;
  imu_rms: number | null;
  pump_current_a: number | null;
  pressure_bar: number | null;
  pressure_valid: boolean | null;
  battery_voltage: number | null;
  battery_percent: number | null;
  signal_rssi: number | null;
  source: string;
  version: string;
  quality_flag: string;
}

export interface DeviceSnapshot {
  device_id: string;
  online: boolean;
  last_seen_seconds: number;
  state: WorkState;
  raw_state: WorkState;
  previous_state: WorkState;
  state_changed: boolean;
  confidence: number;
  reason: string;
  features: {
    vibration_rms_avg?: number | null;
    pump_current_a_avg?: number | null;
    pressure_bar_avg?: number | null;
  };
  state_source: string;
  state_version: string;
  state_id: number | null;
  reading: Reading;
}

export type StreamStatus = "connecting" | "connected" | "reconnecting";

export interface Catalog {
  farms: Array<{ farm_id: string; name: string; center: [number, number] }>;
  parcels: Array<{ parcel_id: string; farm_id: string; name: string; crop: string }>;
  devices: Array<{ device_id: string; name: string; device_type: string }>;
  input_materials: Array<{
    material_id: string;
    event_type: string;
    name: string;
    description: string;
  }>;
  nozzles: Array<{ device_id: string; nozzle_id: string }>;
}

export interface LocationPoint {
  sequence: number;
  timestamp: string;
  latitude: number;
  longitude: number;
  accuracy_m: number | null;
  state: WorkState;
  is_spraying: boolean;
  pressure_fault: boolean;
  source: "browser_gnss" | "demo_route";
  quality_flag: string;
}

export interface WorkSession {
  session_id: string;
  farm_id: string;
  parcel_id: string;
  device_id: string;
  crop: string;
  event_type: string;
  input_material_id: string | null;
  product_name: string | null;
  dilution_ratio: number | null;
  nozzle_id: string;
  location_mode: "browser" | "demo";
  status: "ACTIVE" | "FINISHED";
  start_time: string;
  end_time: string | null;
  locations: LocationPoint[];
  event: WorkEvent | null;
}

export interface WorkEvent {
  event_id: string;
  session_id: string;
  farm_id: string;
  parcel_id: string;
  device_id: string;
  crop: string;
  event_type: string;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  spray_duration_seconds: number;
  estimated_spray_liters: number;
  estimation_notice: string;
  geometry: { type: "LineString"; coordinates: [number, number][] };
  location_quality: { point_count: number; available: boolean };
  sensor_evidence: string[];
  pressure_summary: {
    average_bar: number | null;
    minimum_bar: number | null;
    fault_duration_seconds: number;
  };
  weather_summary: {
    provider: string;
    simulated: boolean;
    rain_approach_minutes: number | null;
    forecast_rain_mm: number;
    maximum_wind_ms: number;
    observed_at: string;
  };
  risk: {
    rain_exposure: "low" | "medium" | "high";
    wind_drift: "low" | "medium" | "high";
    pressure_fault: "low" | "medium" | "high";
  };
  risk_explanations: string[];
  confidence: number;
  confidence_notice: string;
  farmer_confirmed: boolean;
}
