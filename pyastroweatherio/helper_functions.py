"""Contains Helper functions for AstroWeather."""

import bisect
import logging
import math
from datetime import UTC, datetime, timedelta
from math import degrees as deg

import ephem
from ephem import degree
from typeguard import typechecked
from zoneinfo import ZoneInfo

from pyastroweatherio.const import (
    ASTRONOMICAL_DUSK_DAWN,
    AU_TO_KM,
    CIVIL_DUSK_DAWN,
    DARK_NIGHT_MAX_ILLUMINANCE,
    KELVIN_OFFSET,
    LUNAR_MONTH_DAYS,
    MAG_DEGRATION_MAX,
    MOON_MEAN_ANGULAR_SIZE_DEG,
    MOON_MEAN_DISTANCE_KM,
    NAUTICAL_DUSK_DAWN,
    SEEING_MAX,
)
from pyastroweatherio.dataclasses import (
    DarknessData,
    DarknessDataModel,
    MoonData,
    MoonDataModel,
    SunData,
    SunDataModel,
)

_LOGGER = logging.getLogger(__name__)

# Standard atmosphere (ISA, ICAO Doc 7488/3)
_ISA_TEMP_K = 288.15              # K, standard sea-level temperature
_GRAVITY = 9.80665                # m/s², standard gravitational acceleration
_MOLAR_MASS_AIR = 0.02896         # kg/mol, molar mass of dry air
_GAS_CONSTANT_R = 8.31447         # J/(mol·K), universal gas constant
_STANDARD_LAPSE_RATE_K_M = 0.0065  # K/m, standard temperature lapse rate (6.5 K/km)

# Magnus formula for saturation vapor pressure (Monteith & Unsworth 2008), valid -10 to 50°C
_MAGNUS_A = 17.27
_MAGNUS_B = 237.3    # °C
_MAGNUS_SVP0 = 6.1078  # hPa, saturation vapor pressure at 0°C

# Magnus formula (WMO variant), valid -45 to 60°C — used by dew point and _svp_hpa_magnus
_MAGNUS_A_WMO = 17.62
_MAGNUS_B_WMO = 243.12   # °C
_MAGNUS_SVP0_WMO = 6.112  # hPa

# Mixing ratio constant (ratio of molar masses Mw/Md ≈ 0.622, scaled to g/kg)
_MIXING_RATIO_K = 621.97  # g/kg

# LCL pressure approximation (Clausius-Clapeyron-based)
_LCL_A = 2440    # K
_LCL_B = 0.00029  # K⁻¹


class ConversionFunctions:
    """Convert between different units."""

    async def epoch_to_datetime(self, value) -> str:
        """Converts EPOC time to Date Time String."""

        return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d %H:%M:%S")


class AtmosphericRoutines:
    """Calculate atmospheric attributes."""

    def __init__(
        self,
    ):
        _LOGGER.debug("AtmosphericRoutines calculation mode active")

        # Relative humidity (0.0 to 1.0)
        # Temperature in Celsius
        # Cloud cover fraction (0.0 to 1.0)
        # Wind speed in meters per second
        # Humidity in percent
        # Altitude in meters
        # Dew point temperature in Celsius
        # Air pressure at sea level in hPa
        # aerosol_density in kg/m^3

    # ---------- small internal helpers ----------
    @staticmethod
    def _is_missing(values: dict) -> list[str]:
        return [name for name, val in values.items() if val is None or (isinstance(val, float) and math.isnan(val))]

    @staticmethod
    def _svp_hpa_magnus(Tc: float) -> float:
        """
        Saturation vapor pressure over water (hPa), Magnus-Tetens.
        Good for typical near-surface temps.
        """
        return _MAGNUS_SVP0_WMO * math.exp((_MAGNUS_A_WMO * Tc) / (_MAGNUS_B_WMO + Tc))

    @staticmethod
    def _mixing_ratio_gpkg(e_hpa: float, p_hpa: float) -> float:
        """Mixing ratio (g/kg) from vapor pressure e (hPa) and pressure p (hPa)."""
        denom = max(1e-6, (p_hpa - e_hpa))
        return _MIXING_RATIO_K * (e_hpa / denom)

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    # #####################################################
    # Calculate lifted index
    # #####################################################
    @typechecked
    async def calculate_lifted_index(
        self, temperature, altitude, dew_point_temperature, air_pressure_at_sea_level
    ) -> None | float:
        """
        Returns a rough Lifted Index (LI) proxy in °C, clamped to [-7, +7].

        The Lifted Index measures atmospheric stability: negative = unstable
        (thunderstorm risk), positive = stable. Real LI requires a full sounding;
        this proxy is derived from surface data only.

        Method:
        1. Station pressure estimated via the barometric formula (ISA).
        2. LCL temperature via the Bolton (1980) approximation:
           T_lcl = 1 / (1/(T_d - 56) + ln(T/T_d)/800) + 56  [K]
        3. Parcel lifted dry-adiabatically (κ ≈ 2/7) to LCL, then
           moist-adiabatically (κ_moist ≈ 0.12–0.18, moisture-dependent) to 500 hPa.
        4. Environmental T at 500 hPa estimated from surface T minus a
           standard lapse rate (6.5 K/km) over the ~5.5 km column.

        References: Bolton (1980), MWR 108:1046–1053.
        """
        values = {
            "temperature": temperature,
            "altitude": altitude,
            "dew_point_temperature": dew_point_temperature,
            "air_pressure_at_sea_level": air_pressure_at_sea_level,
        }
        missing = self._is_missing(values)
        if missing:
            _LOGGER.warning(f"calculate_lifted_index: None/NaN inputs: {', '.join(missing)}")
            return None

        T = float(temperature)  # °C
        Td = float(dew_point_temperature)
        alt = float(altitude)
        p0 = float(air_pressure_at_sea_level)  # hPa

        # Estimate station pressure at altitude (use your existing helper)
        # (This uses a standard-atmosphere-like relationship and is good enough here.)
        p_sfc = float(self._calculate_adjusted_pressure(p0, alt))

        # --- LCL temperature approximation (Bolton-style quick form) ---
        # Use Kelvin
        Tk = T + KELVIN_OFFSET
        Tdk = Td + KELVIN_OFFSET
        # Prevent nonsense
        Tdk = min(Tk, max(180.0, Tdk))

        # Approx LCL temperature (K)
        # This is a widely used approximation; stable and simple.
        Tlcl = 1.0 / (1.0 / (Tdk - 56.0) + math.log(Tk / Tdk) / 800.0) + 56.0

        # Approx LCL pressure using Poisson (dry adiabatic) relation
        # p_lcl = p_sfc * (Tlcl/Tk)^(cp/Rd) with cp/Rd ≈ 3.5
        p_lcl = p_sfc * (Tlcl / Tk) ** 3.5

        # Parcel temperature at 500 hPa:
        p_target = 500.0
        if p_lcl <= p_target:
            # LCL above 500 hPa: parcel stays unsaturated to 500
            T_parcel_500 = Tk * (p_target / p_sfc) ** (2.0 / 7.0)  # κ ≈ 0.286
        else:
            # Dry-adiabatic to LCL, then “moist-ish” to 500 hPa.
            # Very simplified moist-adiabatic cooling: use a reduced exponent.
            # κ_moist ~ 0.12–0.18 depending on moisture; use RH proxy via Td depression.
            dT = max(0.0, min(20.0, T - Td))
            k_moist = 0.12 + 0.06 * self._sigmoid((5.0 - dT) / 1.5)  # wetter air => smaller cooling exponent
            T_parcel_500 = Tlcl * (p_target / p_lcl) ** k_moist

        # Environmental temperature at 500 hPa:
        # Without a sounding, use a lapse-rate estimate from surface temperature.
        # 500 hPa height is typically ~5.5 km; use (5.5km - altitude) thickness.
        z500 = 5500.0
        dz = max(0.0, z500 - alt)  # meters
        env_lapse = _STANDARD_LAPSE_RATE_K_M
        T_env_500 = (T + KELVIN_OFFSET) - env_lapse * dz

        # LI = T_env(500) - T_parcel(500), in °C
        LI = T_env_500 - T_parcel_500

        # Clamp like your current implementation
        LI = max(-7.0, min(7.0, float(LI)))

        return LI

    # #####################################################
    # Calculate magnitude degradation based on transparency
    # #####################################################
    @typechecked
    async def magnitude_degradation(
        self, temperature, humidity, cloud_cover, wind_speed, altitude, dew_point_temperature, air_pressure_at_sea_level
    ) -> None | float:
        """
        Estimate stellar magnitude loss due to atmospheric extinction.

        Uses the Pogson relation  mag_loss = −2.5 · log₁₀(transparency)  to
        convert a dimensionless transparency [0,1] to a magnitude penalty.
        Transparency is assembled from five weighted penalties:

          Component         Weight  Notes
          ──────────────────────────────────────────────────────────────────
          Cloud cover         50 %  dominates; raised to power 1.2
          Humidity haze       18 %  logistic ramp above ~75 % RH
          Wind-blown aerosol  12 %  logistic ramp above ~6 m/s
          Lifted-index        10 %  unstable air (LI < −1) increases haze
          Seeing correlation  10 %  poor seeing weakly correlates with haze
          ──────────────────────────────────────────────────────────────────

        Altitude provides a small transparency gain (up to ~12 % at high
        elevations) via  1 − 0.12·(1 − exp(−h/1800)).

        Args:
            temperature: Surface temperature in °C.
            humidity: Relative humidity in %.
            cloud_cover: Cloud cover in %.
            wind_speed: Wind speed in m/s.
            altitude: Station altitude in m above sea level.
            dew_point_temperature: Dew-point temperature in °C.
            air_pressure_at_sea_level: QNH / sea-level pressure in hPa.

        Returns:
            Magnitude loss in mag (0 … MAG_DEGRATION_MAX), or None if any
            required input is missing.
        """
        values = {
            "temperature": temperature,
            "humidity": humidity,
            "cloud_cover": cloud_cover,
            "wind_speed": wind_speed,
            "altitude": altitude,
            "dew_point_temperature": dew_point_temperature,
            "air_pressure_at_sea_level": air_pressure_at_sea_level,
        }
        missing = self._is_missing(values)
        if missing:
            _LOGGER.warning(f"magnitude_degradation: None/NaN inputs: {', '.join(missing)}")
            return None

        # Compute ingredients
        lifted_index = await self.calculate_lifted_index(
            temperature, altitude, dew_point_temperature, air_pressure_at_sea_level
        )
        seeing = await self.calculate_seeing(
            temperature,
            humidity,
            dew_point_temperature,
            wind_speed,
            cloud_cover,
            altitude,
            air_pressure_at_sea_level,
        )

        if lifted_index is None or seeing is None:
            return None

        rh = max(0.0, min(100.0, float(humidity)))
        cc = max(0.0, min(100.0, float(cloud_cover)))
        ws = max(0.0, float(wind_speed))
        alt = max(0.0, float(altitude))

        # Base transparency from simple, bounded components
        # (weights are chosen for stable behavior)
        hum_pen = self._sigmoid((rh - 75.0) / 10.0)  # humidity haze risk
        cloud_pen = (cc / 100.0) ** 1.2  # clouds dominate quickly
        wind_pen = self._sigmoid((ws - 6.0) / 2.5) * 0.4  # blowing aerosols
        li_pen = self._sigmoid((-lifted_index - 1.0) / 2.0) * 0.35  # unstable air -> more haze/cloud risk
        seeing_pen = self._sigmoid((seeing - 2.0) / 0.8) * 0.25  # poor seeing correlates w/ bad transparency sometimes

        # altitude improves transparency a bit (less column)
        alt_gain = 1.0 - 0.12 * (1.0 - math.exp(-alt / 1800.0))

        # Combine into transparency 0..1
        penalty = 0.18 * hum_pen + 0.50 * cloud_pen + 0.12 * wind_pen + 0.10 * li_pen + 0.10 * seeing_pen
        transparency = max(0.02, min(1.0, (1.0 - penalty) * alt_gain))

        # Convert transparency to mag loss (extinction-like)
        mag_loss = -2.5 * math.log10(transparency)

        # Clamp to global max
        mag_loss = min(float(MAG_DEGRATION_MAX), float(mag_loss))
        if mag_loss < 0.0:
            mag_loss = 0.0

        return float(mag_loss)

    # #####################################################
    # Calculate atmospheric seeing
    # #####################################################
    @typechecked
    async def calculate_seeing(
        self, temperature, humidity, dew_point_temperature, wind_speed, cloud_cover, altitude, air_pressure_at_sea_level,
        boundary_layer_height=None,
    ) -> None | float:
        """
        Estimate astronomical seeing (FWHM) in arcseconds.

        When `boundary_layer_height` (GFS NWP output, metres) is supplied it
        becomes the dominant input (60 % weight).  A shallow, stable nocturnal
        boundary layer (< 200 m) indicates excellent seeing; a deep convective
        layer (> 2000 m) indicates poor seeing.  The PBL penalty uses a logistic
        on the log-scale, centred at 600 m:
          pbl_pen = sigmoid((log10(pbl) − log10(600)) / 0.35)

        Wind weight is intentionally reduced to 5 % in this path because PBL
        height already captures boundary-layer stability; keeping the full
        surface-wind penalty would double-count the same physics and
        over-penalise moderate winds (e.g. 6–8 m/s) on otherwise stable nights.

        Without PBL data the function falls back to a surface-only heuristic:

          Penalty               Weight  Model
          ──────────────────────────────────────────────────────────────────────
          Wind turbulence         35 %  Gaussian centred at 3 m/s optimal wind
                                        (σ = 2.5 m/s).
          Humidity haze           25 %  Logistic ramp above ~85 % RH.
          Dewpoint depression     20 %  Logistic ramp above ~8 °C dT.
          Cloud-layer proxy       10 %  (cloud_cover/100)^1.5.
          ──────────────────────────────────────────────────────────────────────

        In both modes an altitude gain factor is applied:
          alt_gain = 1 − 0.12·(1 − exp(−h/1800))

        Quality score → arcseconds:  seeing = 4.0 − 3.3·quality,
        clamped to [0.4, SEEING_MAX].

        Args:
            temperature: Surface temperature in °C.
            humidity: Relative humidity in %.
            dew_point_temperature: Dew-point temperature in °C.
            wind_speed: Wind speed in m/s.
            cloud_cover: Cloud cover in %.
            altitude: Station altitude in m above sea level.
            air_pressure_at_sea_level: QNH / sea-level pressure in hPa.
            boundary_layer_height: NWP planetary boundary layer height in m
                (optional; from GFS).  When provided, dominates the quality score.

        Returns:
            Seeing FWHM in arcseconds (0.4 … SEEING_MAX), or None if any
            required input is missing.
        """
        values = {
            "temperature": temperature,
            "humidity": humidity,
            "dew_point_temperature": dew_point_temperature,
            "wind_speed": wind_speed,
            "cloud_cover": cloud_cover,
            "altitude": altitude,
            "air_pressure_at_sea_level": air_pressure_at_sea_level,
        }
        missing = self._is_missing(values)
        if missing:
            _LOGGER.warning(f"calculate_seeing: None/NaN inputs: {', '.join(missing)}")
            return None

        T = float(temperature)
        Td = float(dew_point_temperature)
        rh = max(0.0, min(100.0, float(humidity)))
        ws = max(0.0, float(wind_speed))
        cc = max(0.0, min(100.0, float(cloud_cover)))
        alt = max(0.0, float(altitude))

        # --- proxies ---
        # Dewpoint depression: very small dT => near-saturation / stable layer; can be good or bad.
        # We use it gently: extremes (very large dT) can correlate with strong radiative cooling + BL turbulence.
        dT = max(0.0, min(25.0, T - Td))

        # Wind: best seeing often with light breeze (mixes BL), worse with dead calm or strong wind
        # U-shaped penalty centered near ~3 m/s.
        wind_opt = 3.0
        wind_sigma = 2.5
        wind_pen = 1.0 - math.exp(-((ws - wind_opt) ** 2) / (2.0 * wind_sigma**2))  # 0 near optimum, ->1 away

        # Humidity: very high RH often accompanies haze/fog layers and BL issues; moderate is fine.
        humid_pen = self._sigmoid((rh - 85.0) / 7.0)  # ramps above ~85%

        # Clouds: weak proxy for turbulence aloft. Keep influence small.
        cloud_pen = (cc / 100.0) ** 1.5

        # Altitude: generally helps a bit.
        alt_gain = 1.0 - 0.12 * (1.0 - math.exp(-alt / 1800.0))  # ~1.0 sea level -> ~0.88 high alt

        # Very large dT (very dry) can mean strong surface cooling at night => local turbulence.
        # Mild penalty that only kicks in past ~8°C depression.
        dry_pen = self._sigmoid((dT - 8.0) / 2.5)

        # --- combine into a "quality" score (higher = better) ---
        pbl = None
        if boundary_layer_height is not None:
            try:
                pbl_val = float(boundary_layer_height)
                if not math.isnan(pbl_val):
                    pbl = max(10.0, pbl_val)
            except (TypeError, ValueError):
                pass

        if pbl is not None:
            # PBL-aware path: boundary layer height dominates (60 %).
            # Wind weight is reduced to 5 % because PBL height already encodes
            # boundary-layer stability — the surface wind penalty would otherwise
            # double-count the same physics and over-penalise moderate winds.
            pbl_pen = self._sigmoid((math.log10(pbl) - math.log10(600.0)) / 0.35)
            quality = 1.0 - 0.60 * pbl_pen - 0.05 * wind_pen - 0.25 * humid_pen - 0.10 * cloud_pen
        else:
            # Surface-only fallback
            quality = 1.0 - 0.35 * wind_pen - 0.25 * humid_pen - 0.10 * cloud_pen - 0.20 * dry_pen

        # Apply altitude improvement
        quality *= alt_gain

        # Clamp quality to sane range
        quality = max(0.05, min(0.98, quality))

        # Map to seeing arcsec: better quality => smaller FWHM
        # Choose a realistic range for forecasts (tunable):
        best = 0.7  # arcsec
        worst = 4.0  # arcsec
        seeing = worst - (worst - best) * quality

        # Clamp to global max
        seeing = max(0.4, min(float(SEEING_MAX), seeing))

        return float(seeing)

    # #####################################################
    # Calculate fog density at 2m
    # #####################################################
    @typechecked
    async def calculate_fog_density(self, temp2m, rh2m, dewpoint2m, wind_speed) -> float:
        """
        Estimate fog likelihood as a dimensionless density in [0, 1].

        The score combines two physical signals:

        1. **Saturation score** — logistic function of RH and dewpoint depression:
              sat_score = 2.2·(RH − 92)/8 − 2.6·(dT − 1.2)/1.8
              sat = sigmoid(sat_score)
           Fog becomes likely when RH exceeds ~92 % AND the dewpoint depression
           dT = T − Td falls below ~1–2 °C.  The logistic ensures a smooth,
           bounded transition rather than a hard threshold.

        2. **Wind dispersal** — exponential decay:
              wind_decay = exp(−wind_speed / 3.0)
           Calm conditions (ws ≈ 0) leave fog intact; moderate winds (ws ≥ 6 m/s)
           suppress the score to < 0.14.

        Final result: fog = sat · wind_decay, clamped to [0, 1].

        This is simpler than the Koschmieder visibility approach used in the
        original version but avoids the instability of the exponential humidity
        term near saturation while still behaving correctly at the extremes.

        Args:
            temp2m: Surface temperature in °C.
            rh2m: Relative humidity in % (clamped to [0, 100] internally).
            dewpoint2m: Dew-point temperature in °C.
            wind_speed: Wind speed in m/s.

        Returns:
            Fog density in [0, 1]; 0.0 if any required input is missing.
        """
        # Validate
        values = {"temp2m": temp2m, "rh2m": rh2m, "dewpoint2m": dewpoint2m, "wind_speed": wind_speed}
        missing = self._is_missing(values)
        if missing:
            _LOGGER.warning(f"calculate_fog_density: None/NaN inputs: {', '.join(missing)}")
            return 0.0

        rh = max(0.0, min(100.0, float(rh2m)))
        T = float(temp2m)
        Td = float(dewpoint2m)
        ws = max(0.0, float(wind_speed))

        # Dewpoint depression in °C
        dT = max(-5.0, min(30.0, T - Td))

        # Core saturation term:
        # - Fog becomes likely when RH is high AND dewpoint depression is small.
        # - Map into 0..1 smoothly.
        sat_score = (
            2.2 * (rh - 92.0) / 8.0  # RH ~92% begins to matter strongly
            - 2.6 * (dT - 1.2) / 1.8  # dT <~ 1–2°C drives fog likelihood
        )
        sat = self._sigmoid(sat_score)

        # Wind dispersal: calm helps fog; moderate wind destroys it.
        # This is a smooth decay; tune the 2.5–4.0 range if you want.
        wind_decay = math.exp(-ws / 3.0)

        # Final, clipped
        fog = sat * wind_decay

        return float(max(0.0, min(1.0, fog)))

    # #####################################################
    # Calculate dew point at 2m
    # #####################################################
    @typechecked
    async def calculate_dew_point(self, temp2m, rh2m) -> float:
        """
        Calculate the dew point temperature given air temperature and relative humidity
        using Magnus formula.

        Parameters:
            temp (float): Air temperature in °C.
            humidity (float): Relative humidity in % (0-100).

        Args:
        - temp2m: Surface temperature in Celsius.
        - rh2m: Humidity in Percent.

        Returns:
        - float: Dew point temperature in °C.
        """
        alpha = math.log(max(rh2m, 1.0) / 100) + (_MAGNUS_A_WMO * temp2m) / (_MAGNUS_B_WMO + temp2m)
        return (_MAGNUS_B_WMO * alpha) / (_MAGNUS_A_WMO - alpha)

    # #####################################################
    # Atmospheric calculations
    # #####################################################
    @typechecked
    def _calculate_adjusted_pressure(self, pressure_sea_level, altitude) -> float:
        """
        Calculate the adjusted pressure at a given altitude above sea level.
        """

        lapse_rate = _STANDARD_LAPSE_RATE_K_M
        temperature_sea_level = _ISA_TEMP_K
        gravity = _GRAVITY
        molar_mass_air = _MOLAR_MASS_AIR
        gas_constant = _GAS_CONSTANT_R

        pressure_adjusted = pressure_sea_level * (1 - (lapse_rate * altitude) / temperature_sea_level) ** (
            (gravity * molar_mass_air) / (gas_constant * lapse_rate)
        )

        return pressure_adjusted

    @typechecked
    def _calculate_vapor_pressure(self, temperature) -> float:
        """
        Calculate the actual or saturation vapor pressure at the surface using the Magnus-Tetens formula.
        If the surface temperature is given, the actual vapor pressure is calculated.
        The dew point temperature calculates ths saturation vapor pressure.

        Used by: lifted index, seeing

        Args:
        - temperature: Surface or dew point temperature in Celsius.

        Returns:
        - e: Actual vapor pressure at the surface in millibars (mb) or hectopascals (hPa).

        Magnus coefficients used: Monteith & Unsworth (2008), valid -10 to 50°C.
        """
        # Calculate vapor pressure using Magnus-Tetens formula
        e = _MAGNUS_SVP0 * math.exp((_MAGNUS_A * temperature) / (temperature + _MAGNUS_B))

        return e

    @typechecked
    def _calculate_water_vapor_pressure(self, dew_point_temperature, humidity) -> float:
        """
        Calculate the water vapor pressure based on temperature and humidity.

        Used by: seeing

        Args:
        - dew_point_temperature: Dew point temperature in Celsius.
        - humidity: Humidity in Percent.

        Returns:
        - water_vapor_pressure: Water vapor pressure at the surface in millibars (mb) or hectopascals (hPa).
        """

        es = self._calculate_vapor_pressure(dew_point_temperature)
        water_vapor_pressure = (humidity / 100) * es

        return water_vapor_pressure

    @typechecked
    def _calculate_mixing_ratio(self, e, air_pressure_at_sea_level) -> float:
        """
        Calculate the mixing ratio.

        Used by: lifted index

        Args:
        - e: Vapor pressure
        - air_pressure_at_sea_level: Air pressure at sea level

        Returns:
        - w: mixing ratio at surface in grams per kilogram
        """

        w = _MIXING_RATIO_K * (e / (air_pressure_at_sea_level - e))

        return w

    @typechecked
    def _calculate_lifting_condensation_level(self, w, air_pressure_at_sea_level) -> float:
        """
        The Lifting Condensation Level is the level at which a parcel becomes saturated. It can be used as
        a reasonable estimate of cloud base height when parcels experience forced ascent.
        Here, we calculate it using the Clausius-Clapeyron equation. This equation relates the saturation vapor
        pressure (e) to the temperature and pressure.
        https://en.wikipedia.org/wiki/Lifted_condensation_level

        Used by: lifted index

        Args:
        - w: Mixing ratio
        - air_pressure_at_sea_level: Air pressure at sea level

        Returns:
        - lcl: LCL in meters
        """

        # Calculate Lifting Condensation Level using the Clausius-Clapeyron equation
        lcl = (_LCL_A * w) / ((air_pressure_at_sea_level - w) * (1 - _LCL_B * air_pressure_at_sea_level))

        return lcl

    @typechecked
    def _calculate_transparency(
        self,
        humidity,
        temperature,
        cloud_cover,
        wind_speed,
        altitude,
        dew_point_temperature,
        air_pressure_at_sea_level,
        lifted_index,
        seeing,
    ) -> float:
        """
        The transparency of the atmosphere calculated by a weighted sum of conditions.

        Used by: magnitude degradation

        Args:
        - humidity: Humidity in Percent.
        - temperature: Surface temperature in Celsius.
        - cloud_cover: Cloud cover in Percent.
        - wind_speed: Wind speed in meters per second.
        - altitude: Altitude in meters.
        - dew_point_temperature: Dew point temperature in Celsius.
        - air_pressure_at_sea_level: Air pressure at sea level.
        - lifted_index: Lifted index in Celsius.
        - seeing: Seeing in Arcsecs.
        - w: Mixing ratio

        Returns:
        - transparency: In the range of 0 to 1
        """

        # Coefficients for the linear model (you can adjust these based on your requirements)
        temp_weight = 0.10
        humidity_weight = 0.10
        wind_weight = 0.10
        dew_point_weight = 0.10
        lifted_index_weight = 0.15
        seeing_weight = 0.15
        pressure_weight = 0.10
        cloud_cover_weight = 0.10
        altitude_weight = 0.10

        # Normalize values (optional)
        # Assuming typical temperature range from -10°C to 40°C
        temp_normalized = (temperature - (-10)) / (40 - (-10))
        humidity_normalized = humidity / 100.0
        # Assuming maximum typical wind speed as 20 m/s
        wind_normalized = wind_speed / 20.0
        # Assuming typical dew point range from -10°C to 30°C
        dew_point_normalized = (dew_point_temperature - (-10)) / (30 - (-10))
        # Assuming lifted index range from -8 to 8
        lifted_index_normalized = (lifted_index + 8) / 16.0
        # Assuming typical seeing conditions from 0 to 10 arcseconds
        seeing_normalized = (10 - seeing) / 10.0
        # Assuming typical pressure range from 900 to 1100 mb
        pressure_normalized = (air_pressure_at_sea_level - 900) / (1100 - 900)
        cloud_cover_normalized = cloud_cover / 100.0
        # Assuming typical altitude range from 0 to 5000 meters
        altitude_normalized = altitude / 5000.0

        transparency = 1 - (
            temp_weight * temp_normalized
            + humidity_weight * humidity_normalized
            + wind_weight * wind_normalized
            + dew_point_weight * dew_point_normalized
            + lifted_index_weight * lifted_index_normalized
            + seeing_weight * seeing_normalized
            + pressure_weight * pressure_normalized
            + cloud_cover_weight * cloud_cover_normalized
            + altitude_weight * altitude_normalized
        )

        # Ensure transparency is within the valid range [0, 1]
        transparency = max(0, min(1, transparency))

        return transparency

    @typechecked
    def _transparency_to_magnitude_degradation(self, transparency) -> float:
        """
        The magnitude degradation based on the atmospheric transparency.

        Used by: magnitude degradation

        Args:
        - transparency: In the range of 0 to 1.

        Returns:
        - magniture_degradation: In magnitude.
        """

        if transparency == 0:
            return float(MAG_DEGRATION_MAX)
        magnitude_degradation = -MAG_DEGRATION_MAX * math.log(transparency)
        magnitude_degradation = max(0, min(MAG_DEGRATION_MAX, magnitude_degradation))

        return magnitude_degradation


class AstronomicalRoutines:
    """Calculate different astronomical objects."""

    def __init__(
        self,
        location_data,
        forecast_time=None,
    ) -> None:
        self._location_data = location_data
        self._test_mode = False

        _LOGGER.debug("Timezone: %s", self._location_data.timezone_info)
        if forecast_time is None:
            self._forecast_time = datetime.now(UTC).replace(tzinfo=UTC)
        else:
            self._forecast_time = forecast_time.replace(tzinfo=UTC)
            self._test_mode = True

        self._sun_observer = None
        self._sun_observer_nautical = None
        self._sun_observer_astro = None
        self._moon_observer = None
        self._sun = None
        self._moon = None
        self._sun_data = {}
        self._moon_data = {}
        self._darkness_data = {}

        # Internal only
        self._sun_previous_rising_astro = None
        self._sun_previous_setting_astro = None

    def _test_data(self, data, keys) -> bool:
        """Test that specific values in a dictionary are not None"""

        if not all(data[key] is not None for key in keys):
            return False
        return True

    def utc_to_local_diff(self) -> float:
        """Returns the UTC Offset."""

        # Get the current time in the specified timezone
        now = datetime.now(ZoneInfo(self._location_data.timezone_info))

        # Get the offset in seconds
        offset_seconds = now.utcoffset().total_seconds()

        # Convert the offset to hours
        return offset_seconds / 3600

    async def time_shift(self) -> float:
        """Returns the time_shift to UTC in hours."""

        return int(self.utc_to_local_diff() * 3600)

    async def need_update(self, forecast_time=None) -> None:
        """Update Sun and Moon."""

        if forecast_time is not None:
            self._forecast_time = forecast_time.replace(tzinfo=UTC)

        _LOGGER.debug("Astronomical calculations updating")
        self._calculate_sun()
        self._calculate_moon()

    #
    # Observers
    #
    @typechecked
    def _get_sun_observer(self, below_horizon=ASTRONOMICAL_DUSK_DAWN) -> ephem.Observer:
        """Retrieves the ephem sun observer for the current location."""

        observer = ephem.Observer()
        observer.lon = str(self._location_data.longitude)  # * degree
        observer.lat = str(self._location_data.latitude)  # * degree
        observer.elevation = self._location_data.elevation
        observer.horizon = below_horizon * degree
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")

        return observer

    @typechecked
    def _get_moon_observer(self) -> ephem.Observer:
        """Retrieves the ephem mon observer for the current location."""

        observer = ephem.Observer()
        observer.lon = str(self._location_data.longitude)  # * degree
        observer.lat = str(self._location_data.latitude)  # * degree
        observer.elevation = self._location_data.elevation
        # Naval Observatory Risings and Settings
        # Set horizon to minus 34 arcminutes
        # https://aa.usno.navy.mil/data/RS_OneDay
        observer.horizon = "-0:34"
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")

        return observer

    def _ephem_find_event(
        self,
        observer: ephem.Observer,
        make_call,
        forward: bool,
        label: str,
    ) -> datetime | None:
        """Compute a rise/set event, searching ±365 days if the body is circumpolar."""
        try:
            return make_call().datetime().replace(tzinfo=UTC)
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            start = observer.date.datetime()
            step = timedelta(minutes=1440) if forward else timedelta(minutes=-1440)
            limit = start + timedelta(days=365) if forward else start - timedelta(days=365)
            timestamp = start
            cnt = 1
            while (timestamp < limit) if forward else (timestamp > limit):
                timestamp += step
                observer.date = timestamp
                try:
                    result = make_call().datetime().replace(tzinfo=UTC)
                    _LOGGER.debug(f"{label} in {cnt} days.")
                    return result
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    cnt += 1
            return None

    # #########################################################################
    # Sun
    # #########################################################################
    @typechecked
    async def sun_data(self) -> SunData:
        """Returns sun data."""

        sd = SunDataModel(self._sun_data)
        try:
            return SunData(data=sd)
        except TypeError as ve:
            _LOGGER.error(f"Failed to parse Sun data: {self._sun_data}")
            _LOGGER.error(ve)
            return None

    async def sun_next_rising(self) -> datetime:
        """Returns sun next rising."""

        if (
            not self._test_data(
                self._sun_data,
                ["next_rising_astro", "next_rising_nautical", "next_rising_civil"],
            )
            or self._forecast_time > self._sun_data["next_rising_astro"]
            or self._forecast_time > self._sun_data["next_rising_nautical"]
            or self._forecast_time > self._sun_data["next_rising_civil"]
        ):
            _LOGGER.debug("Astronomical calculations updating sun_next_rising")
            self._calculate_sun()

        if self._sun_data.get("next_rising_astro", None) is not None:
            return self._sun_data["next_rising_astro"]
        if self._sun_data.get("next_rising_nautical", None) is not None:
            return self._sun_data["next_rising_nautical"]
        if self._sun_data.get("next_rising_civil", None) is not None:
            return self._sun_data["next_rising_civil"]

    async def sun_next_setting(self) -> datetime:
        """Returns sun next setting."""

        if (
            not self._test_data(
                self._sun_data,
                ["next_setting_astro", "next_setting_nautical", "next_setting_civil"],
            )
            or self._forecast_time > self._sun_data["next_setting_astro"]
            or self._forecast_time > self._sun_data["next_setting_nautical"]
            or self._forecast_time > self._sun_data["next_setting_civil"]
        ):
            _LOGGER.debug("Astronomical calculations updating sun_next_setting")
            self._calculate_sun()

        if self._sun_data.get("next_setting_astro", None) is not None:
            return self._sun_data["next_setting_astro"]
        if self._sun_data.get("next_setting_nautical", None) is not None:
            return self._sun_data["next_setting_nautical"]
        if self._sun_data.get("next_setting_civil", None) is not None:
            return self._sun_data["next_setting_civil"]

    def _calculate_sun(self) -> None:
        """Calculates sun risings and settings."""

        if self._sun_observer is None:
            self._sun_observer = self._get_sun_observer(CIVIL_DUSK_DAWN)
        if self._sun_observer_nautical is None:
            self._sun_observer_nautical = self._get_sun_observer(NAUTICAL_DUSK_DAWN)
        if self._sun_observer_astro is None:
            self._sun_observer_astro = self._get_sun_observer(ASTRONOMICAL_DUSK_DAWN)
        if self._sun is None:
            self._sun = ephem.Sun()

        obs_c = self._sun_observer
        obs_c.date = self._forecast_time
        self._sun.compute(obs_c)
        self._sun_data["next_rising_civil"] = self._ephem_find_event(
            obs_c, lambda: obs_c.next_rising(ephem.Sun(), use_center=True), True, "Sun next rising civil"
        )
        self._sun_data["next_setting_civil"] = self._ephem_find_event(
            obs_c, lambda: obs_c.next_setting(ephem.Sun(), use_center=True), True, "Sun next setting civil"
        )

        obs_n = self._sun_observer_nautical
        obs_n.date = self._forecast_time
        self._sun.compute(obs_n)
        self._sun_data["next_rising_nautical"] = self._ephem_find_event(
            obs_n, lambda: obs_n.next_rising(ephem.Sun(), use_center=True), True, "Sun next rising nautical"
        )
        self._sun_data["next_setting_nautical"] = self._ephem_find_event(
            obs_n, lambda: obs_n.next_setting(ephem.Sun(), use_center=True), True, "Sun next setting nautical"
        )

        obs_a = self._sun_observer_astro
        obs_a.date = self._forecast_time
        self._sun.compute(obs_a)
        self._sun_data["next_rising_astro"] = self._ephem_find_event(
            obs_a, lambda: obs_a.next_rising(ephem.Sun(), use_center=True), True, "Sun next rising astro"
        )
        self._sun_data["previous_rising_astro"] = self._ephem_find_event(
            obs_a, lambda: obs_a.previous_rising(ephem.Sun(), use_center=True), False, "Sun previous rising astro"
        )
        self._sun_data["next_setting_astro"] = self._ephem_find_event(
            obs_a, lambda: obs_a.next_setting(ephem.Sun(), use_center=True), True, "Sun next setting astro"
        )
        self._sun_data["previous_setting_astro"] = self._ephem_find_event(
            obs_a, lambda: obs_a.previous_setting(ephem.Sun(), use_center=True), False, "Sun previous setting astro"
        )

        self._calculate_sun_altaz()
        self._calculate_sun_constellation()

    def _calculate_sun_altaz(self) -> None:
        """Calculates sun altitude and azimuth."""

        if self._sun_observer is None:
            self._sun_observer = self._get_sun_observer(CIVIL_DUSK_DAWN)
        if self._sun is None:
            self._sun = ephem.Sun()

        self._sun_observer.date = self._forecast_time
        self._sun.compute(self._sun_observer)

        # Sun Altitude
        self._sun_data["altitude"] = deg(float(self._sun.alt))

        # Sun Azimuth
        self._sun_data["azimuth"] = deg(float(self._sun.az))

    def _calculate_sun_constellation(self) -> None:
        """Calculates sun altitude and azimuth."""

        if self._sun_observer is None:
            self._sun_observer = self._get_sun_observer(CIVIL_DUSK_DAWN)
        if self._sun is None:
            self._sun = ephem.Sun()

        self._sun_observer.date = self._forecast_time
        self._sun.compute(self._sun_observer)

        # Sun Constellation
        constellation = ephem.constellation(self._sun)[1]
        self._sun_data["constellation"] = constellation

    # #########################################################################
    # Moon
    # #########################################################################
    @typechecked
    async def moon_data(self) -> MoonData:
        """Returns moon data."""

        md = MoonDataModel(self._moon_data)
        try:
            return MoonData(data=md)
        except TypeError as ve:
            _LOGGER.error(f"Failed to parse Moon data: {self._moon_data}")
            _LOGGER.error(ve)
            return None

    def _calculate_moon(self) -> None:
        """Calculates moon rising and setting."""

        if self._moon_observer is None:
            self._moon_observer = self._get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()

        # Rise and Setting
        self._moon_observer.date = self._forecast_time
        self._moon.compute(self._moon_observer)

        obs = self._moon_observer
        self._moon_data["next_rising"] = self._ephem_find_event(
            obs, lambda: obs.next_rising(ephem.Moon()), True, "Moon next rising"
        )
        self._moon_data["next_setting"] = self._ephem_find_event(
            obs, lambda: obs.next_setting(ephem.Moon()), True, "Moon next setting"
        )
        self._moon_data["previous_rising"] = self._ephem_find_event(
            obs, lambda: obs.previous_rising(ephem.Moon()), False, "Moon previous rising"
        )
        self._moon_data["previous_setting"] = self._ephem_find_event(
            obs, lambda: obs.previous_setting(ephem.Moon()), False, "Moon previous setting"
        )

        # Next new Moon
        self._moon_data["next_new_moon"] = ephem.next_new_moon(self._forecast_time).datetime().replace(tzinfo=UTC)

        # Pervious new Moon
        self._moon_data["previous_new_moon"] = (
            ephem.previous_new_moon(self._forecast_time).datetime().replace(tzinfo=UTC)
        )

        # Next full Moon
        self._moon_data["next_full_moon"] = ephem.next_full_moon(self._forecast_time).datetime().replace(tzinfo=UTC)

        # Moon phase
        self._moon_data["phase"] = self._moon.phase

        self._calculate_moon_altaz()
        self._calculate_moon_distance_size()
        self._calculate_moon_constellation()
        self._calculate_moon_phase_on_day()
        self._next_dark_night()

    def _calculate_moon_altaz(self) -> None:
        """Calculates moon altitude and azimuth."""

        if self._moon_observer is None:
            self._moon_observer = self._get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()

        self._moon_observer.date = self._forecast_time
        self._moon.compute(self._moon_observer)

        # Moon Altitude
        self._moon_data["altitude"] = deg(float(self._moon.alt))

        # Moon Azimuth
        self._moon_data["azimuth"] = deg(float(self._moon.az))

    def _calculate_moon_distance_size(self) -> None:
        """Calculate moon distance and relative size"""

        if self._moon_observer is None:
            self._moon_observer = self._get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()

        # Get the distance in Earth radii
        self._moon_data["distance"] = self._moon.earth_distance  # in AU (Astronomical Units)

        # Convert to kilometers
        self._moon_data["distance_km"] = self._moon_data["distance"] * AU_TO_KM

        # Get the Moon's angular diameter (radius is in radians in ephem)
        self._moon_data["angular_size"] = math.degrees(self._moon.radius * 2)

        # Average distance and angular size for comparison
        self._moon_data["avg_distance_km"] = MOON_MEAN_DISTANCE_KM
        self._moon_data["avg_angular_size"] = MOON_MEAN_ANGULAR_SIZE_DEG

        # Relative distance and size compared to average
        self._moon_data["relative_distance"] = self._moon_data["distance_km"] / self._moon_data["avg_distance_km"]
        self._moon_data["relative_size"] = self._moon_data["angular_size"] / self._moon_data["avg_angular_size"]

    def _calculate_moon_constellation(self) -> None:
        """Calculates moon constellation."""

        if self._moon_observer is None:
            self._moon_observer = self._get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()

        self._moon_observer.date = self._forecast_time
        self._moon.compute(self._moon_observer)

        # Moon Constellation
        constellation = ephem.constellation(self._moon)[1]
        self._moon_data["constellation"] = constellation

    def _calculate_moon_phase_on_day(self) -> None:
        """
        Calculates the Moon Phase on day

        The following extract the percent time between one new moon and the next
        This corresponds (somewhat roughly) to the phase of the moon.
        Note that there is a ephem.Moon().phase(), but this returns the
        percentage of the moon which is illuminated. This is not really what we
        want.
        """

        day = 1.0 / LUNAR_MONTH_DAYS
        moonphase = [
            (0.0 / 4.0 + day, "🌑", "New moon", "moon-new"),
            (1.0 / 4.0 - day, "🌒", "Waxing crescent moon", "moon-waxing-crescent"),
            (1.0 / 4.0 + day, "🌓", "First quarter moon", "first-quarter-moon"),
            (2.0 / 4.0 - day, "🌔", "Waxing gibbous moon", "moon-waxing-gibbous"),
            (2.0 / 4.0 + day, "🌕", "Full moon", "moon-full"),
            (3.0 / 4.0 - day, "🌖", "Waning gibbous moon", "moon-waning-gibbous"),
            (3.0 / 4.0 + day, "🌗", "Last quarter moon", "moon-last-quarter"),
            (4.0 / 4.0 - day, "🌘", "Waning crescent moon", "moon-waning-crescent"),
            (4.0 / 4.0, "🌑", "New moon", "moon-new"),
        ]
        ranges = [x[0] for x in moonphase]

        nnm = self._moon_data["next_new_moon"]
        pnm = self._moon_data["previous_new_moon"]

        # Number from 0-1. where 0=new, 0.5=full, 1=new
        lunation = (self._forecast_time - pnm) / (nnm - pnm)

        phase = bisect.bisect_right(ranges, lunation)

        self._moon_data["icon"] = moonphase[phase][3]

        # _LOGGER.debug(f"{round(lunation * 100.0, 1)} {moonphase[phase][1]} {moonphase[phase][2]} {moonphase[phase][3]}")

    def _get_astronomical_darkness(self, date) -> tuple | tuple[None, None]:
        """
        Get astronimical darkness for a given date.

        Args:
        - date: Date for calculation

        Returns:
        - astro_twilight_start,
          astro_twilight_end: Datetime for astronomical sun set and rise.
                              If the sun does not rise or set [None, None] is returned.
        """
        self._sun_observer_astro.date = date

        # Compute the next sunset and sunrise
        try:
            astro_twilight_start = self._sun_observer_astro.next_setting(ephem.Sun(), use_center=True)
            self._sun_observer_astro.date = astro_twilight_start
            astro_twilight_end = self._sun_observer_astro.next_rising(ephem.Sun(), use_center=True)
            return astro_twilight_start.datetime(), astro_twilight_end.datetime()
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            return None, None

    @staticmethod
    def _moon_illuminance(alt_rad: float, phase_pct: float) -> float:
        """Return lunar illuminance proxy: phase_fraction × max(0, sin(altitude)).

        Combines phase and altitude into a single value on [0, 1]:
        - 0   → moon invisible (below horizon or new moon)
        - 1   → full moon directly overhead
        A value below DARK_NIGHT_MAX_ILLUMINANCE indicates negligible sky glow.
        """
        return (phase_pct / 100.0) * max(0.0, math.sin(alt_rad))

    def moon_illuminance_at(self, dt: datetime) -> float:
        """Return the lunar illuminance proxy at an arbitrary UTC datetime.

        Intended for per-hour forecast calculations so that the moon's actual
        position at each forecast timestamp drives the score, not its position
        at the time the coordinator last ran.
        """
        if self._moon_observer is None:
            self._moon_observer = self._get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()
        self._moon_observer.date = dt.replace(tzinfo=None)
        self._moon.compute(self._moon_observer)
        return self._moon_illuminance(float(self._moon.alt), self._moon.phase)

    def moon_altitude_at(self, dt: datetime) -> float:
        """Return moon altitude in degrees at an arbitrary UTC datetime."""
        if self._moon_observer is None:
            self._moon_observer = self._get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()
        self._moon_observer.date = dt.replace(tzinfo=None)
        self._moon.compute(self._moon_observer)
        return deg(float(self._moon.alt))

    # Function to check Moon conditions for the whole night
    def _is_moon_dark_whole_night(self, night_start, night_end) -> bool:
        """Return True if the night qualifies as a dark night.

        Uses an integrated lunar illuminance proxy instead of independent
        phase / altitude thresholds. The proxy is:
            illuminance = (phase / 100) × max(0, sin(altitude_radians))
        A night is dark when the peak illuminance over the whole night stays
        below DARK_NIGHT_MAX_ILLUMINANCE, which avoids the edge cases of the
        previous approach (e.g. a full moon 3° above the horizon being accepted
        because its altitude was below the 5° threshold).
        """
        current_time = night_start
        peak_illuminance = 0.0

        while current_time <= night_end:
            self._moon_observer.date = current_time
            moon = ephem.Moon(self._moon_observer)
            illuminance = self._moon_illuminance(float(moon.alt), moon.phase)
            if illuminance > peak_illuminance:
                peak_illuminance = illuminance
            current_time += timedelta(minutes=5)

        dark_night = peak_illuminance <= DARK_NIGHT_MAX_ILLUMINANCE
        _LOGGER.debug(
            f"Night {night_start.strftime('%Y-%m-%d')}: peak illuminance {peak_illuminance:.4f} → dark_night={dark_night}"
        )
        return dark_night

    def _next_dark_night(self) -> None:
        """Calculate the next dark night"""

        if self._moon_observer is None:
            self._moon_observer = self._get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()

        self._moon_data["next_dark_night"] = None

        start_date = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0) - timedelta(
            seconds=self.utc_to_local_diff()
        )

        for i in range(365):
            date = start_date + timedelta(days=i)
            night_start, night_end = self._get_astronomical_darkness(date)

            # Skip nights where twilight is undefined (polar regions)
            if night_start is None or night_end is None:
                continue

            if self._is_moon_dark_whole_night(night_start, night_end):
                self._moon_data["next_dark_night"] = night_start.replace(tzinfo=UTC)
                break

    # #########################################################################
    # Darkness
    # #########################################################################
    @typechecked
    async def darkness_data(self) -> DarknessData:
        """Returns darkness data."""

        self._darkness_data["deep_sky_darkness_moon_rises"] = self._deep_sky_darkness_moon_rises()
        self._darkness_data["deep_sky_darkness_moon_sets"] = self._deep_sky_darkness_moon_sets()
        self._darkness_data["deep_sky_darkness_moon_always_up"] = self._deep_sky_darkness_moon_always_up()
        self._darkness_data["deep_sky_darkness_moon_always_down"] = self._deep_sky_darkness_moon_always_down()
        self._darkness_data["deep_sky_darkness"] = self._deep_sky_darkness()

        dd = DarknessDataModel(self._darkness_data)
        try:
            return DarknessData(data=dd)
        except TypeError as ve:
            _LOGGER.error(f"Failed to parse darkness data: {self._darkness_data}")
            _LOGGER.error(ve)
            return None

    async def night_duration_astronomical(self) -> float:
        """Returns the remaining timespan of astronomical darkness."""

        return (self._sun_data["next_rising_astro"] - self._night_start_timestamp()).total_seconds()

    def _deep_sky_darkness(self) -> float:
        """Returns the remaining timespan of deep sky darkness."""

        dsd = timedelta(0)

        if self._astronomical_darkness():
            _LOGGER.debug("DSD: In astronomical darkness")
            if self._deep_sky_darkness_moon_rises():
                dsd = self._moon_data["next_rising"] - self._forecast_time
                _LOGGER.debug(f"DSD: Sun down, Moon rises {dsd}")

            if self._deep_sky_darkness_moon_sets():
                if self._moon_down():
                    dsd = self._sun_data["next_rising_astro"] - self._forecast_time
                    _LOGGER.debug(f"DSD: Sun down, Moon is down {dsd}")
                else:
                    dsd = self._sun_data["next_rising_astro"] - self._moon_data["next_setting"]
                    _LOGGER.debug(f"DSD: Sun down, Moon sets {dsd}")

            if self._deep_sky_darkness_moon_always_down():
                dsd = self._sun_data["next_rising_astro"] - self._forecast_time
                _LOGGER.debug(f"DSD: Moon always down {dsd}")
            else:
                _LOGGER.debug(f"DSD: Moon NOT always down {dsd}")

        if not self._astronomical_darkness():
            _LOGGER.debug("DSD: At sunlight")
            if self._deep_sky_darkness_moon_rises():
                dsd = self._moon_data["next_rising"] - self._sun_data["next_setting_astro"]
                _LOGGER.debug(f"DSD: Sun up, Moon rises {dsd}")

            if self._deep_sky_darkness_moon_sets():
                dsd = self._sun_data["next_rising_astro"] - self._moon_data["next_setting"]
                _LOGGER.debug(f"DSD: Sun up, Moon sets {dsd}")

            if self._deep_sky_darkness_moon_always_down():
                dsd = self._sun_data["next_rising_astro"] - self._sun_data["next_setting_astro"]
                _LOGGER.debug(f"DSD: Sun up, Moon down {dsd}")

        if self._deep_sky_darkness_moon_always_up():
            dsd = timedelta(0)
            _LOGGER.debug(f"DSD: Moon always up {dsd}")
        else:
            _LOGGER.debug(f"DSD: Moon NOT always up {dsd}")

        return dsd.total_seconds()

    def _astronomical_darkness(self) -> bool:
        """Returns true during astronomical night."""

        if self._sun_data["next_setting_astro"] > self._sun_data["next_rising_astro"]:
            return True
        return False

    def _night_start_timestamp(self):
        """Returns the start of the current (or next) astronomical night."""
        if self._astronomical_darkness():
            return self._sun_data["previous_setting_astro"]
        return self._sun_data["next_setting_astro"]

    def _moon_down(self) -> bool:
        """Returns true while moon is set-"""

        if self._moon_data["next_setting"] > self._moon_data["next_rising"]:
            return True
        return False

    def _deep_sky_darkness_moon_rises(self) -> bool:
        """Returns true if moon rises during astronomical night."""

        start_timestamp = self._night_start_timestamp()

        if (
            self._moon_data["next_rising"] > start_timestamp
            and self._moon_data["next_rising"] < self._sun_data["next_rising_astro"]
        ):
            _LOGGER.debug("DSD: Moon rises during astronomical night")
            return True
        return False

    def _deep_sky_darkness_moon_sets(self) -> bool:
        """Returns true if moon sets during astronomical night."""

        start_timestamp = self._night_start_timestamp()

        # Did Moon already set in darkness?
        if self._moon_down() and self._astronomical_darkness():
            start_timestamp_moon = self._moon_data["previous_setting"]
        else:
            start_timestamp_moon = self._moon_data["next_setting"]

        if start_timestamp_moon > start_timestamp and start_timestamp_moon < self._sun_data["next_rising_astro"]:
            _LOGGER.debug("DSD: Moon sets during astronomical night")
            return True
        return False

    def _deep_sky_darkness_moon_always_up(self) -> bool:
        """Returns true if moon is up during astronomical night."""

        start_timestamp = self._night_start_timestamp()

        if (
            self._moon_data["next_rising"] < start_timestamp
            and self._moon_data["next_setting"] > self._sun_data["next_rising_astro"]
        ):
            _LOGGER.debug("DSD: Moon is up during astronomical night")
            return True
        return False

    def _deep_sky_darkness_moon_always_down(self) -> bool:
        """Returns true if moon is down during astronomical night."""

        start_timestamp = self._night_start_timestamp()

        if (
            self._moon_data["previous_setting"] < start_timestamp
            and self._moon_data["next_rising"] > self._sun_data["next_rising_astro"]
        ):
            _LOGGER.debug("DSD: Moon is down during astronomical night")
            return True
        return False
