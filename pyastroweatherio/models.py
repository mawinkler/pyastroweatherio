from datetime import datetime

from pydantic import BaseModel, Field

from pyastroweatherio.const import (
    DEFAULT_ELEVATION,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_TIMEZONE,
)


class LocationModel(BaseModel):
    latitude: float = Field(default=DEFAULT_LATITUDE)
    longitude: float = Field(default=DEFAULT_LONGITUDE)
    elevation: float = Field(default=DEFAULT_ELEVATION)
    timezone_info: str = Field(default=DEFAULT_TIMEZONE)


class ConditionModel(BaseModel):
    cloudcover: float
    cloud_area_fraction: float
    cloud_area_fraction_high: float
    cloud_area_fraction_low: float
    cloud_area_fraction_medium: float
    fog_area_fraction: float
    seeing: float
    transparency: float
    lifted_index: float
    condition_percentage: int
    rh2m: float
    wind_speed: float
    wind_from_direction: float
    temp2m: float
    dewpoint2m: float
    weather: str
    weather6: str
    precipitation_amount: float
    precipitation_amount6: float


class AtmosphereModel(BaseModel):
    seeing: float
    transparency: float
    lifted_index: float


class SunModel(BaseModel):
    altitude: float
    azimuth: float
    next_rising_astro: datetime
    next_rising_civil: datetime
    next_rising_nautical: datetime
    next_setting_astro: datetime
    next_setting_civil: datetime
    next_setting_nautical: datetime
    previous_rising_astro: datetime
    previous_setting_astro: datetime


class MoonModel(BaseModel):
    altitude: float
    angular_size: float
    avg_angular_size: float
    avg_distance_km: float
    azimuth: float
    distance: float
    distance_km: float
    next_full_moon: datetime
    next_new_moon: datetime
    next_rising: datetime
    next_setting: datetime
    phase: float
    previous_rising: datetime
    previous_setting: datetime
    relative_distance: float
    relative_size: float


class DarknessModel(BaseModel):
    deep_sky_darkness_moon_rises: bool
    deep_sky_darkness_moon_sets: bool
    deep_sky_darkness_moon_always_up: bool
    deep_sky_darkness_moon_always_down: bool
    deep_sky_darkness: float
