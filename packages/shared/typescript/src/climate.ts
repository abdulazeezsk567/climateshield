/**
 * Climate Telemetry and Observation Interfaces.
 */

import { GeoLocation } from './borrower.js';

export enum DataSourceType {
  NASA_POWER = 'NASA_POWER',
  IMD_GRIDDED = 'IMD_GRIDDED',
  SENTINEL_NDVI = 'SENTINEL_NDVI',
  SYNTHETIC_SIMULATOR = 'SYNTHETIC_SIMULATOR',
}

export interface ClimateObservation {
  timestamp: string;
  location: GeoLocation;
  source: DataSourceType;
  precipitation_mm: number;
  temperature_celsius: number;
  relative_humidity_pct?: number;
  wind_speed_kmh?: number;
  ndvi_vegetation_index?: number;
}

export interface ClimateEvent {
  event_id: string;
  timestamp: string;
  district: string;
  state: string;
  source: DataSourceType;
  precipitation_anomaly_pct: number;
  consecutive_dry_days: number;
  consecutive_excess_rain_days: number;
  temperature_anomaly_celsius: number;
  ndvi_anomaly_delta?: number;
  raw_telemetry: Record<string, number>;
}
