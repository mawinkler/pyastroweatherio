# Changelog

## (2026-05-29)

### New Features

#### GFS Supplementary Data

Open-Meteo exposes `lifted_index`, `cape`, `boundary_layer_height`, and `visibility` only for the `gfs_seamless` model (GFS — Global Forecast System, NOAA's global numerical weather prediction model). A second, lightweight Open-Meteo request is now made in parallel with the primary model fetch — always targeting `gfs_seamless` — so these physically superior inputs are available regardless of which primary model the user has selected.

- **`_retrieve_data_gfs`** (`client.py`): New method that fetches `lifted_index`, `cape`, `boundary_layer_height`, and `visibility` from GFS. Failure is non-fatal; the columns are filled with `NaN` and the surface-based fallbacks are used instead.
- **`_retrieve_data`** (`client.py`): `_retrieve_data_uptonight`, the primary Open-Meteo fetch, and the new GFS fetch now run in a single `asyncio.gather` call, reducing total wall-clock fetch time. GFS columns are merged into the main DataFrame before the atmospheric calculations.
- **Seeing with GFS PBL height** (`client.py`, `helper_functions.py`): `_calculate_seeing` passes `gfs_boundary_layer_height` to `calculate_seeing` when the column is present. The PBL height dominates the quality score (60 % weight) via a logistic on the log-scale centred at 600 m; wind weight is reduced from 35 % to 5 % to avoid double-counting boundary-layer stability. The surface-only path is unchanged and used as fallback.
- **Lifted index from GFS** (`client.py`): `_calculate_lifted_index` uses `gfs_lifted_index` directly from the DataFrame instead of the Bolton approximation. Bolton is retained as a per-row fallback for any `NaN` values.
- **Fog from GFS visibility** (`client.py`): Fog density is derived from `gfs_visibility` (metres → `[0, 1]` via `1 − vis/10 000`) when the GFS column is available and non-NaN, falling back to `calculate_fog_density` otherwise.
- **`LocationDataModel` / `LocationData` — `gfs_supplementary_data` field** (`client.py`, `dataclasses.py`): Added `gfs_supplementary_data: bool` to `LocationDataModel` (TypedDict) and `LocationData`. The field is `True` when the GFS fetch succeeded and the NWP columns were merged into the weather DataFrame, and `False` when the fetch failed. Exposes GFS availability to consumers (e.g. the HA binary sensor) without them having to inspect DataFrame columns directly.

#### CAMS Aerosol Optical Depth (AOD)

Saharan dust, wildfire smoke, and volcanic ash can degrade transparency significantly yet were not reflected in the forecast. AOD at 550 nm is now fetched from the **CAMS model via the Open-Meteo Air Quality API** (`https://air-quality-api.open-meteo.com/v1/air-quality`) — no API key required, consistent with the existing no-registration philosophy.

- **`_retrieve_data_aod`** (`client.py`): New method that fetches hourly `aerosol_optical_depth` from CAMS. Called in parallel with the GFS and primary Open-Meteo fetches; failure is non-fatal (column filled with NaN, existing transparency model used unchanged).
- **`_get_condition`** (`client.py`): Converts AOD to magnitude extinction using the Bouguer-Lambert law at zenith (`mag ≈ AOD × AOD_TO_MAG_FACTOR`, new constant `AOD_TO_MAG_FACTOR = 1.086` in `const.py`). The effective transparency is `max(modelled_transparency, aod_mag)`, so aerosols only worsen the score — they cannot inflate it. Reference values: AOD 0.05 (clean sky) → 0.05 mag (negligible); AOD 0.3 (moderate haze) → 0.33 mag; AOD 1.0 (heavy dust) → capped at 1.0 mag (MAG_DEGRATION_MAX).
- **`ConditionDataModel` / `ConditionData`** (`dataclasses.py`): Added `aerosol_optical_depth: float` field, exposing the raw AOD value for use in sensor entities.
- **`BASE_URL_OPENMETEO_AQ`** (`const.py`): New constant for the Open-Meteo Air Quality API endpoint.

#### Moon position per forecast hour

- **`_get_condition`** (`client.py`, `dataclasses.py`, `helper_functions.py`): Previously, moon altitude and azimuth were computed once for the current time and reused for all forecast hours. Moon altitude and illuminance are now calculated at each forecast timestamp via new `AstronomicalRoutines.moon_altitude_at(dt)` and `moon_illuminance_at(dt)` methods. Both values are exposed as `moon_altitude` and `moon_illuminance` fields on `ConditionData` and, through it, on `ForecastData`. A shared private `_moon_illuminance(alt_rad, phase_pct)` static method is used by both the forecast path and `_is_moon_dark_whole_night`.

### Improvements

#### Condition scoring overhaul (`_calc_condition_percentage`)

Five independent improvements to the sky-quality scoring formula in `client.py` and `const.py`:

- **Hard precipitation veto**: Any measurable precipitation (`≥ PRECIP_VETO_THRESHOLD = 0.1 mm/h`) immediately returns `0`. The previous soft penalty allowed rain to coexist with a non-zero score; any precipitation makes astronomical observation impossible regardless of other factors. The old `PRECIP_MAX` constant is superseded by `PRECIP_VETO_THRESHOLD`.

- **Non-linear seeing normalisation**: Seeing is now scaled as `(arcsec / SEEING_MAX)² × 100` instead of linearly. The quadratic curve means excellent seeing (0.5–1.0 arcsec) barely penalises the score (1.6 % and 6.2 % respectively), while poor seeing (3.0–4.0 arcsec) dominates (56–100 %). The previous linear mapping over-penalised good nights.

- **Non-linear transparency normalisation**: Magnitude degradation is now scaled as `(mag / MAG_DEGRATION_MAX)^1.5 × 100`. Very clean air (0.1 mag) produces only a 3.2 % penalty (was 10 %); the curve steepens towards the bad end so that haze at 0.8 mag scores 71.6 % (was 80 %).

- **Multiplicative cloud/fog ceiling**: An explicit ceiling `max_possible = (1 − cloud_clearness) × (1 − fog_clearness) × 100` is applied: 100 % effective cloud cover caps the condition at 0 regardless of how good the other factors are; 50 % cloud cover limits the score to at most 50 %. Previously, secondary factors (seeing, transparency, wind) could partially compensate for high cloud cover.

- **Moon illuminance penalty**: The lunar illuminance proxy (`phase_fraction × sin(altitude)`) is now fed into `_calc_condition_percentage` and deducted from the score at `MOON_PENALTY_WEIGHT = 40` points maximum. A full moon at zenith (illuminance = 1.0) subtracts 40 points; a waxing crescent at 30° altitude subtracts roughly 5 points; a moon below the horizon subtracts nothing. Added constants `MOON_PENALTY_WEIGHT`, `DEW_SPREAD_THRESHOLD`, `DEW_PENALTY_MAX`, and `PRECIP_VETO_THRESHOLD` to `const.py`.

- **Dew-risk penalty**: When the temperature–dewpoint spread falls below `DEW_SPREAD_THRESHOLD = 3.0 °C`, a penalty of up to `DEW_PENALTY_MAX = 15` points is applied (linear: 0 pts at 3 °C spread, 15 pts at 0 °C spread). A near-zero spread signals imminent condensation on optics — a critical issue for astrophotography even without visible fog.

- **Multi-layer cloud opacity** (`client.py`): Cloud cover was scored as `max(high, medium, low)` after weakening, which underestimates opacity when multiple independent layers are present. Replaced with the physical transmittance product `1 − (1−h)(1−m)(1−l)`, where each layer's blocking fraction is weighted by its configured weakening factor. Example: three layers at 50 % previously scored 50 %; they now correctly score 87.5 %.

#### Atmospheric calculations promoted to default

The experimental variants are now the only implementations. Key improvements in the promoted implementations:

- Seeing uses PBL height from GFS when available (dominant signal at 60 % weight); falls back to a surface-only heuristic with wind, humidity, dewpoint depression, and cloud cover.
- Magnitude degradation uses the Pogson relation (`mag_loss = −2.5·log₁₀(transparency)`) and internally calls the improved seeing and lifted-index methods.
- Fog density uses a logistic saturation score (RH + dewpoint depression) with exponential wind-dispersal decay; GFS visibility overrides the estimate when available.
- Lifted index prefers direct GFS NWP output; Bolton (1980) approximation fills any missing slots.
- The `experimental_features` flag is preserved for backward compatibility but no longer changes calculation behaviour; a debug-level log message is emitted if it is still set to `True`.

#### Other improvements

- **Physically tuned cloud-layer weakening defaults** (`const.py`): The three per-layer weakening defaults were previously all `1.0` (100 % impact), treating cirrus and stratus identically. New defaults reflect the actual optical depth of each layer type: high (cirrus) → `0.40`, medium (altocumulus) → `0.70`, low (stratus/fog) → `1.00`. Existing configurations that have been explicitly set by the user are unaffected.
- **`SEEING_MAX` raised from 2.5 to 4.0 arcseconds** (`const.py`): The promoted seeing model maps quality to a `[0.7, 4.0]` arcsec range internally, but the old `SEEING_MAX = 2.5` cap was clamping all values above 2.5 — preventing the model from expressing poor-to-terrible seeing (2.5–4.0 arcsec). The cap and normalization factor are now aligned with the model's actual output range. The `SEEING` bin array has been updated to match: eight equal-width bins from 0.5 to 4.0 arcsec.
- **`_is_moon_dark_whole_night` — dark-night criterion** (`helper_functions.py`): Replaced the independent phase / altitude thresholds (`DARK_NIGHT_MAX_MOON_PHASE`, `DARK_NIGHT_MAX_MOON_ALT`) with a single integrated lunar illuminance proxy: `illuminance = (phase / 100) × max(0, sin(altitude_rad))`. The night qualifies as dark when the peak illuminance over the whole night stays below `DARK_NIGHT_MAX_ILLUMINANCE = 0.05`. The old logic accepted a full moon sitting 3° above the horizon as a "dark night" (altitude < 5° threshold satisfied) and could override a bright-moon-above-horizon result using only phase average.
- **`const.py` — astronomical constants** (`const.py`): Added new `# Astronomical constants` section with named constants: `AU_TO_KM`, `MOON_MEAN_DISTANCE_KM`, `MOON_MEAN_ANGULAR_SIZE_DEG`, `LUNAR_MONTH_DAYS`, `KELVIN_OFFSET`.

### Tests

- Added `tests/test_calculations.py`: 27 unit tests for `AtmosphericRoutines` covering all public and internal calculation methods. Tests require no network access and run in < 0.01 s.
  - `_calculate_adjusted_pressure`: sea-level identity, altitude monotonicity.
  - `_calculate_vapor_pressure`: temperature monotonicity, 0 °C reference value.
  - `calculate_dew_point`: saturation (RH=100), typical value, below-temperature invariant.
  - `calculate_lifted_index`: range check, None-on-missing.
  - `calculate_seeing`: range check, overcast > clear ordering, None-on-missing.
  - `calculate_fog_density`: clear is low, saturated is high, wind dispersal.
  - `magnitude_degradation`: range check, overcast > clear ordering, None-on-missing.
