"""Defines the Data Classes used."""
from datetime import datetime, timezone
import math

from pyastroweatherio.const import (
    CLOUDCOVER_PLAIN,
    CONDITION,
    DEEP_SKY_THRESHOLD,
    LIFTED_INDEX_PLAIN,
    SEEING_PLAIN,
    TRANSPARENCY_PLAIN,
    # WIND10M_SPEED_PLAIN,
    # WIND10M_SPEED,
    WIND10M_DIRECTON,
    # MAP_WEATHER_TYPE,
)


class BaseData:
    """A representation of the base class for AstroWeather Data."""

    def __init__(self, data):
        self._init = data["init"]
        self._timepoint = data["timepoint"]
        self._timestamp = data["timestamp"]
        self._cloudcover = data["cloudcover"]
        self._cloud_area_fraction = data["cloud_area_fraction"]
        self._cloud_area_fraction_high = data["cloud_area_fraction_high"]
        self._cloud_area_fraction_low = data["cloud_area_fraction_low"]
        self._cloud_area_fraction_medium = data["cloud_area_fraction_medium"]
        self._fog_area_fraction = data["fog_area_fraction"]
        self._seeing = data["seeing"]
        self._transparency = data["transparency"]
        self._condition_percentage = data["condition_percentage"]
        self._lifted_index = data["lifted_index"]
        self._rh2m = data["rh2m"]
        self._wind_speed = data["wind_speed"]
        self._wind_from_direction = data["wind_from_direction"]
        self._temp2m = data["temp2m"]
        self._dewpoint2m = data["dewpoint2m"]
        self._weather = data["weather"]
        self._weather6 = data["weather6"]
        self._precipitation_amount = data["precipitation_amount"]

    @property
    def init(self) -> datetime:
        """Return Forecast Anchor."""
        return self._init.replace(microsecond=0, tzinfo=timezone.utc)

    @property
    def timepoint(self) -> int:
        """Return Forecast Hour."""
        return self._timepoint

    @property
    def timestamp(self) -> datetime:
        """Return Forecast Timestamp."""
        return self._timestamp.replace(microsecond=0, tzinfo=timezone.utc)

    @property
    def condition_percentage(self) -> int:
        """Return condition based on cloud cover, seeing and transparency"""
        return self._condition_percentage

    @property
    def cloudcover(self) -> int:
        """Return Cloud Coverage."""
        return self._cloudcover

    @property
    def cloudcover_percentage(self) -> int:
        """Return Cloud Cover Percentage."""
        return int(-(100 * (1 - self._cloudcover) / 8))

    @property
    def cloudless_percentage(self) -> int:
        """Return Cloudless Percentage."""
        return int(100 + 100 * (1 - self._cloudcover) / 8)

    @property
    def cloud_area_fraction_percentage(self) -> int:
        """Return Cloud Cover Percentage."""
        return self._cloud_area_fraction

    @property
    def cloud_area_fraction_high_percentage(self) -> int:
        """Return Cloud Cover Percentage."""
        return self._cloud_area_fraction_high

    @property
    def cloud_area_fraction_low_percentage(self) -> int:
        """Return Cloud Cover Percentage."""
        return self._cloud_area_fraction_low

    @property
    def cloud_area_fraction_medium_percentage(self) -> int:
        """Return Cloud Cover Percentage."""
        return self._cloud_area_fraction_medium

    @property
    def fog_area_fraction_percentage(self) -> int:
        """Return Fog Area Percentage."""
        return self._fog_area_fraction

    @property
    def seeing(self) -> int:
        """Return Seeing."""
        return self._seeing

    @property
    def seeing_percentage(self) -> int:
        """Return Seeing."""
        return int((100 + 100 / 7 - self._seeing * 100 / 7))

    @property
    def transparency(self) -> int:
        """Return Transparency."""
        return self._transparency

    @property
    def transparency_percentage(self) -> int:
        """Return Transparency."""
        return int((100 + 100 / 7 - self._transparency * 100 / 7))

    @property
    def lifted_index(self) -> int:
        """Return Lifted Index."""
        return self._lifted_index

    @property
    def rh2m(self) -> int:
        """Return 2m Relative Humidity."""
        return self._rh2m

    @property
    def wind10m_speed(self) -> float:
        """Return 10m Wind Speed."""
        return self._wind_speed

    @property
    def wind10m_direction(self) -> str:
        """Return 10m Wind Direction."""
        direction = self._wind_from_direction
        direction += 22.5
        direction = direction % 360
        direction = int(direction / 45)  # values 0 to 7
        return WIND10M_DIRECTON[direction]

    @property
    def temp2m(self) -> int:
        """Return 2m Temperature."""
        return self._temp2m

    @property
    def dewpoint2m(self) -> float:
        """Return 2m Dew Point."""
        return round(self._dewpoint2m, 1)

    @property
    def weather(self) -> str:
        """Return Current Weather."""
        return self._weather.replace("_", " ").capitalize()

    @property
    def weather6(self) -> str:
        """Return Current Weather."""
        return self._weather6.replace("_", " ").capitalize()

    @property
    def precipitation_amount(self) -> float:
        """Return Current Weather."""
        return self._precipitation_amount


class LocationData(BaseData):
    """A representation of the Location AstroWeather Data."""

    def __init__(self, data):
        super().__init__(data)
        self._forecast_length = data["forecast_length"]
        self._latitude = data["latitude"]
        self._longitude = data["longitude"]
        self._elevation = data["elevation"]
        self._sun_next_rising = data["sun_next_rising"]
        self._sun_next_rising_nautical = data["sun_next_rising_nautical"]
        self._sun_next_rising_astro = data["sun_next_rising_astro"]
        self._sun_next_setting = data["sun_next_setting"]
        self._sun_next_setting_nautical = data["sun_next_setting_nautical"]
        self._sun_next_setting_astro = data["sun_next_setting_astro"]
        self._sun_altitude = data["sun_altitude"]
        self._sun_azimuth = data["sun_azimuth"]
        self._moon_next_rising = data["moon_next_rising"]
        self._moon_next_setting = data["moon_next_setting"]
        self._moon_phase = data["moon_phase"]
        self._moon_next_new_moon = data["moon_next_new_moon"]
        self._moon_altitude = data["moon_altitude"]
        self._moon_azimuth = data["moon_azimuth"]
        self._night_duration_astronomical = data["night_duration_astronomical"]
        self._deep_sky_darkness_moon_rises = data["deep_sky_darkness_moon_rises"]
        self._deep_sky_darkness_moon_sets = data["deep_sky_darkness_moon_sets"]
        self._deep_sky_darkness_moon_always_up = data["deep_sky_darkness_moon_always_up"]
        self._deep_sky_darkness = data["deep_sky_darkness"]
        self._deepsky_forecast = data["deepsky_forecast"]

    @property
    def forecast_length(self) -> int:
        """Return Forecast Length in Hours"""
        return self._forecast_length

    @property
    def latitude(self) -> float:
        """Return Latitude."""
        return self._latitude

    @property
    def longitude(self) -> float:
        """Return Longitude."""
        return self._longitude

    @property
    def elevation(self) -> float:
        """Return Elevation."""
        return self._elevation

    @property
    def cloudcover_plain(self) -> str:
        """Return Cloud Coverage."""
        cover = self._cloudcover
        if cover >= 1 and cover <= 9:
            return CLOUDCOVER_PLAIN[cover - 1]
        return None

    @property
    def seeing_plain(self) -> str:
        """Return Seeing."""
        seeing = self._seeing
        if seeing >= 1 and seeing <= 8:
            return SEEING_PLAIN[seeing - 1]
        return None

    @property
    def transparency_plain(self) -> str:
        """Return Transparency."""
        transparency = self._transparency
        if transparency >= 1 and transparency <= 8:
            return TRANSPARENCY_PLAIN[self._transparency - 1]
        return None

    @property
    def lifted_index_plain(self) -> str:
        """Return Lifted Index."""

        trans = {
            -10: LIFTED_INDEX_PLAIN[0],
            -6: LIFTED_INDEX_PLAIN[1],
            -4: LIFTED_INDEX_PLAIN[2],
            -1: LIFTED_INDEX_PLAIN[3],
            2: LIFTED_INDEX_PLAIN[4],
            6: LIFTED_INDEX_PLAIN[5],
            10: LIFTED_INDEX_PLAIN[6],
            15: LIFTED_INDEX_PLAIN[7],
        }
        lifted_index = self._lifted_index
        if lifted_index in trans:
            return trans.get(self._lifted_index, "")
        return None

    @property
    def deep_sky_view(self) -> bool:
        """Return True if Deep Sky should be possible."""
        if self.condition_percentage >= DEEP_SKY_THRESHOLD:
            return True
        return False

    @property
    def condition_plain(self) -> str:
        """Return Current View Conditions."""
        if self.condition_percentage > 80:
            return CONDITION[0].capitalize()
        if self.condition_percentage > 60:
            return CONDITION[1].capitalize()
        if self.condition_percentage > 40:
            return CONDITION[2].capitalize()
        if self.condition_percentage > 20:
            return CONDITION[3].capitalize()
        return CONDITION[4].capitalize()

    @property
    def sun_next_rising(self) -> datetime:
        """Return Sun Next Rising Civil."""
        if isinstance(self._sun_next_rising, datetime):
            return self._sun_next_rising

    @property
    def sun_next_rising_nautical(self) -> datetime:
        """Return Sun Next Rising Nautical."""
        if isinstance(self._sun_next_rising_nautical, datetime):
            return self._sun_next_rising_nautical

    @property
    def sun_next_rising_astro(self) -> datetime:
        """Return Sun Next Rising Astronomical."""
        if isinstance(self._sun_next_rising_astro, datetime):
            return self._sun_next_rising_astro

    @property
    def sun_next_setting(self) -> datetime:
        """Return Next Setting Civil."""
        if isinstance(self._sun_next_setting, datetime):
            return self._sun_next_setting

    @property
    def sun_next_setting_nautical(self) -> datetime:
        """Return Sun Next Setting Nautical."""
        if isinstance(self._sun_next_setting_nautical, datetime):
            return self._sun_next_setting_nautical

    @property
    def sun_next_setting_astro(self) -> datetime:
        """Return Sun Next Setting Astronomical."""
        if isinstance(self._sun_next_setting_astro, datetime):
            return self._sun_next_setting_astro

    @property
    def sun_altitude(self) -> float:
        """Return Sun Altitude."""
        return round(self._sun_altitude, 3)

    @property
    def sun_azimuth(self) -> float:
        """Return sun Azimuth."""
        return round(self._sun_azimuth, 3)

    @property
    def moon_next_rising(self) -> datetime:
        """Return Moon Next Rising."""
        if isinstance(self._moon_next_rising, datetime):
            return self._moon_next_rising

    @property
    def moon_next_setting(self) -> datetime:
        """Return Moon Next Setting."""
        if isinstance(self._moon_next_setting, datetime):
            return self._moon_next_setting

    @property
    def moon_phase(self) -> float:
        """Return Moon Phase."""
        return round(self._moon_phase, 1)

    @property
    def moon_next_new_moon(self) -> datetime:
        """Return Moon Next New Moon."""
        if isinstance(self._moon_next_new_moon, datetime):
            return self._moon_next_new_moon

    @property
    def moon_altitude(self) -> float:
        """Return Moon Altitude."""
        return round(self._moon_altitude, 3)

    @property
    def moon_azimuth(self) -> float:
        """Return Moon Azimuth."""
        return round(self._moon_azimuth, 3)

    @property
    def night_duration_astronomical(self) -> float:
        """Returns the remaining timespan of astronomical darkness."""
        return self._night_duration_astronomical

    @property
    def deep_sky_darkness_moon_rises(self) -> bool:
        """Returns true if moon rises during astronomical night."""
        return self._deep_sky_darkness_moon_rises

    @property
    def deep_sky_darkness_moon_sets(self) -> bool:
        """Returns true if moon sets during astronomical night."""
        return self._deep_sky_darkness_moon_sets

    @property
    def deep_sky_darkness_moon_always_up(self) -> bool:
        """Returns true if moon is up during astronomical night."""
        return self._deep_sky_darkness_moon_always_up

    @property
    def deep_sky_darkness(self) -> float:
        """Returns the remaining timespan of deep sky darkness."""
        return self._deep_sky_darkness

    @property
    def deepsky_forecast(self):
        """Return Deepsky Forecast."""
        return self._deepsky_forecast

    @property
    def deepsky_forecast_today(self) -> int:
        """Return Forecas Today in Percent."""
        nightly_condition_sum = 0
        for nightly_condition in self._deepsky_forecast[0].nightly_conditions:
            nightly_condition_sum += nightly_condition
        return int(round(nightly_condition_sum / len(self._deepsky_forecast[0].nightly_conditions)))

    @property
    def deepsky_forecast_today_dayname(self):
        """Return Forecast Todays Dayname."""
        if len(self._deepsky_forecast) > 0:
            nightly_conditions = self._deepsky_forecast[0]
            return nightly_conditions.dayname
        return None

    @property
    def deepsky_forecast_today_plain(self):
        """Return Forecast Today."""
        out = ""
        for nightly_condition in self._deepsky_forecast[0].nightly_conditions:
            out += CONDITION[4 - math.floor(nightly_condition / 20)].capitalize()
        return out

    @property
    def deepsky_forecast_today_desc(self):
        """Return Forecast Today Description."""
        if len(self._deepsky_forecast) > 0:
            nightly_conditions = self._deepsky_forecast[0]
            return nightly_conditions.weather.replace("_", " ").capitalize()
        return None

    @property
    def deepsky_forecast_tomorrow(self) -> int:
        """Return Forecas Tomorrow in Percentt."""
        nightly_condition_sum = 0
        for nightly_condition in self._deepsky_forecast[1].nightly_conditions:
            nightly_condition_sum += nightly_condition
        return int(round(nightly_condition_sum / len(self._deepsky_forecast[0].nightly_conditions)))

    @property
    def deepsky_forecast_tomorrow_dayname(self):
        """Return Forecast Todays Dayname."""
        if len(self._deepsky_forecast) > 1:
            nightly_conditions = self._deepsky_forecast[1]
            return nightly_conditions.dayname
        return None

    @property
    def deepsky_forecast_tomorrow_plain(self):
        """Return Forecast Tomorrow."""
        out = ""
        for nightly_condition in self._deepsky_forecast[1].nightly_conditions:
            out += CONDITION[4 - math.floor(nightly_condition / 20)].capitalize()
        return out

    @property
    def deepsky_forecast_tomorrow_desc(self):
        """Return Forecast Tomorrow Description."""
        if len(self._deepsky_forecast) > 1:
            nightly_conditions = self._deepsky_forecast[1]
            return nightly_conditions.weather.replace("_", " ").capitalize()
        return None


class ForecastData(BaseData):
    """A representation of 3-Hour Based Forecast AstroWeather Data."""

    def __init__(self, data):
        super().__init__(data)
        self._hour = data["hour"]

    @property
    def hour(self) -> int:
        """Return Forecast Hour of the day."""
        return self._hour

    @property
    def deep_sky_view(self) -> bool:
        """Return True if Deep Sky should be possible."""
        if self.condition_percentage <= DEEP_SKY_THRESHOLD:
            return True
        return False


class NightlyConditionsData:
    """A representation of nights Sky Quality Data."""

    def __init__(self, data):
        self._init = data["init"]
        self._dayname = data["dayname"]
        self._hour = data["hour"]
        self._nightly_conditions = data["nightly_conditions"]
        self._weather = data["weather"]

    @property
    def init(self) -> datetime:
        """Return Forecast Anchor."""
        return self._init

    @property
    def dayname(self) -> str:
        """Return Forecast Name of the Day."""
        return self._dayname

    @property
    def hour(self) -> int:
        """Return Forecast Hour."""
        return self._hour

    @property
    def nightly_conditions(self) -> int:
        """Return Forecast Hour."""
        return self._nightly_conditions

    @property
    def weather(self) -> str:
        """Return Current Weather."""
        return self._weather.replace("_", " ").capitalize()
