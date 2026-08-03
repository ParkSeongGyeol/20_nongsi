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
