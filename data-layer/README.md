# ClimateShield Data Layer (`/data-layer`)

The Data Layer is responsible for environmental observation telemetry ingestion (NASA POWER, IMD-style weather, Sentinel-2 / NDVI proxies) and management of anonymized MSME borrower portfolio seed profiles and 10-year rolling historical baselines.

---

## 1. Key Components

### 1.1 Ingestion Connectors (`data_layer.ingestion`)
- **NASA POWER Connector (`NASAPowerWeatherProvider`)**: Ingests point meteorological telemetry with automated retries, exponential backoff, timeout controls, and `-999` sentinel missing value filtering.
- **IMD Stub (`IMDWeatherProvider`)**: Demonstrates seamless provider swapability via the `WeatherProvider` abstract interface.
- **Resilient Fallback Generator (`SyntheticWeatherProvider`)**: High-fidelity offline simulation for testing.
- **Vegetation Health Proxy (`SentinelNDVIProvider`)**: Models seasonal NDVI curves across Indian crop calendars (Rabi/Kharif).

### 1.2 Baseline Storage & Analytics (`data_layer.baselines`)
- **Historical Baseline Calculator (`HistoricalBaselineCalculator`)**: Computes monthly mean rainfall ($\mu$), standard deviation ($\sigma$), 95th percentile extreme threshold ($P_{95}$), and healthy NDVI.
- **Baseline Repository (`InMemoryBaselineStore`)**: Pre-seeded with 10-year monthly baselines across 7 core SFL lending districts (Gorakhpur, Varanasi, Lucknow, Patna, Muzaffarpur, Ludhiana, Jaipur).

### 1.3 Synthetic MSME Borrower Portfolio (`data_layer.borrowers`)
- **Seed Generator (`generate_synthetic_borrower_dataset`)**: Produces realistic synthetic borrower records across MSME sectors (`AGRI_ALLIED`, `DAIRY_LIVESTOCK`, `HANDLOOMS_TEXTILES`, `FOOD_PROCESSING`, `RETAIL_MICRO_ENTERPRISE`, `SERVICES_LIGHT_MANUFACTURING`).
- **Data Minimization & Compliance**: All records are explicitly tagged as synthetic demo data with anonymized identifiers and centroid geolocations.

### 1.4 Public Facade (`data_layer.service.DataLayerService`)
The single authoritative public interface for the Data Layer. External consumers (such as `risk-engine`) query:
- `get_district_baseline(district_id, month)`
- `get_weather_observations(lat, lon, start_date, end_date, provider)`
- `get_vegetation_index(lat, lon, date)`
- `list_borrowers(district_id, sector)`
- `get_borrower(borrower_id)`
- `get_portfolio_summary()`

---

## 2. Running Unit Tests
```bash
pytest data-layer/tests -v
```
Verifies coordinate validation, date range bounding, synthetic provider outputs, and public facade querying.
