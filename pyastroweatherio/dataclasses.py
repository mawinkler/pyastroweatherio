"""Defines the Data Classes used."""
from datetime import datetime, timezone
import math

from pyastroweatherio.const import (
    CLOUDCOVER_PLAIN,
    CONDITION,
    DEEP_SKY_THRESHOLD,
    LIFTED_INDEX_PLAIN,
    # RH2M_PLAIN,
    SEEING_PLAIN,
    TRANSPARENCY_PLAIN,
    WIND10M_SPEED_PLAIN,
    WIND10M_SPEED,
    MAP_WEATHER_TYPE,
)


class BaseData:
    """A representation of the base class for AstroWeather Data."""

    def __init__(self, data):
        self._init = data["init"]
        self._timepoint = data["timepoint"]
        self._timestamp = data["timestamp"]
        self._cloudcover = data["cloudcover"]
        self._seeing = data["seeing"]
        self._transparency = data["transparency"]
        self._condition_percentage = data["condition_percentage"]
        self._lifted_index = data["lifted_index"]
        self._rh2m = data["rh2m"]
        self._wind10m = data["wind10m"]
        self._temp2m = data["temp2m"]
        self._dewpoint2m = data["dewpoint2m"]
        self._prec_type = data["prec_type"]
        self._weather = data["weather"]

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
        return float(WIND10M_SPEED[self._wind10m.get("speed", 0)])

    @property
    def temp2m(self) -> int:
        """Return 2m Temperature."""
        return self._temp2m

    @property
    def dewpoint2m(self) -> float:
        """Return 2m Dew Point."""
        return round(self._dewpoint2m, 1)

    @property
    def prec_type(self) -> str:
        """Return Precipitation Type."""
        return self._prec_type.capitalize()

    @property
    def weather(self) -> str:
        """Return Current Weather."""
        return self._weather


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
        self._moon_altitude = data["moon_altitude"]
        self._moon_azimuth = data["moon_azimuth"]
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
        return CLOUDCOVER_PLAIN[self._cloudcover - 1]

    @property
    def seeing_plain(self) -> str:
        """Return Seeing."""
        return SEEING_PLAIN[self._seeing - 1]

    @property
    def transparency_plain(self) -> str:
        """Return Transparency."""
        return TRANSPARENCY_PLAIN[self._transparency - 1]

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
        return trans.get(self._lifted_index, "")

    @property
    def wind10m_direction(self) -> str:
        """Return 10m Wind Direction."""
        return self._wind10m.get("direction", "O").upper()

    @property
    def wind10m_speed_plain(self) -> str:
        """Return 10m Wind Speed."""
        speed = self._wind10m.get("speed", -1)
        if speed < 8:
            return WIND10M_SPEED_PLAIN[self._wind10m.get("speed", 0)].capitalize()
        else:
            return WIND10M_SPEED_PLAIN[8].capitalize()

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
        # return self._sun_next_rising

    @property
    def sun_next_rising_nautical(self) -> datetime:
        """Return Sun Next Rising Nautical."""
        if isinstance(self._sun_next_rising_nautical, datetime):
            return self._sun_next_rising_nautical
        # return self._sun_next_rising_nautical

    @property
    def sun_next_rising_astro(self) -> datetime:
        """Return Sun Next Rising Astronomical."""
        if isinstance(self._sun_next_rising_astro, datetime):
            return self._sun_next_rising_astro
        # return self._sun_next_rising_astro

    @property
    def sun_next_setting(self) -> datetime:
        """Return Next Setting Civil."""
        if isinstance(self._sun_next_setting, datetime):
            return self._sun_next_setting
        # return self._sun_next_setting

    @property
    def sun_next_setting_nautical(self) -> datetime:
        """Return Sun Next Setting Nautical."""
        if isinstance(self._sun_next_setting_nautical, datetime):
            return self._sun_next_setting_nautical
        # return self._sun_next_setting_nautical

    @property
    def sun_next_setting_astro(self) -> datetime:
        """Return Sun Next Setting Astronomical."""
        if isinstance(self._sun_next_setting_astro, datetime):
            return self._sun_next_setting_astro
        # return self._sun_next_setting_astro

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
        # return self._moon_next_rising

    @property
    def moon_next_setting(self) -> datetime:
        """Return Moon Next Setting."""
        if isinstance(self._moon_next_setting, datetime):
            return self._moon_next_setting
        # return self._moon_next_setting

    @property
    def moon_phase(self) -> float:
        """Return Moon Phase."""
        return round(self._moon_phase, 1)

    @property
    def moon_altitude(self) -> float:
        """Return Moon Altitude."""
        return round(self._moon_altitude, 3)

    @property
    def moon_azimuth(self) -> float:
        """Return Moon Azimuth."""
        return round(self._moon_azimuth, 3)

    @property
    def deepsky_forecast(self):
        """Return Deepsky Forecast."""
        return self._deepsky_forecast

    @property
    def deepsky_forecast_today(self) -> int:
        """Return Forecas Today in Percentt."""
        if len(self._deepsky_forecast) > 0:
            nightly_conditions = self._deepsky_forecast[0]
            return int(
                round(
                    (
                        nightly_conditions.nightly_conditions[0]
                        + nightly_conditions.nightly_conditions[1]
                        + nightly_conditions.nightly_conditions[2]
                    )
                    / 3,
                    1,
                )
            )
        return None

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
        if len(self._deepsky_forecast) > 0:
            nightly_conditions = self._deepsky_forecast[0]
            out = ""
            out += (
                CONDITION[
                    4 - math.floor(nightly_conditions.nightly_conditions[0] / 20)
                ].capitalize()
                + "-"
            )
            out += (
                CONDITION[
                    4 - math.floor(nightly_conditions.nightly_conditions[1] / 20)
                ].capitalize()
                + "-"
            )
            out += CONDITION[
                4 - math.floor(nightly_conditions.nightly_conditions[2] / 20)
            ].capitalize()
            return out
        return None

    @property
    def deepsky_forecast_today_desc(self):
        """Return Forecast Today Description."""
        if len(self._deepsky_forecast) > 0:
            nightly_conditions = self._deepsky_forecast[0]
            return MAP_WEATHER_TYPE[nightly_conditions.weather]
        return None

    @property
    def deepsky_forecast_tomorrow(self) -> int:
        """Return Forecas Tomorrow in Percentt."""
        if len(self._deepsky_forecast) > 1:
            nightly_conditions = self._deepsky_forecast[1]
            return int(
                round(
                    (
                        nightly_conditions.nightly_conditions[0]
                        + nightly_conditions.nightly_conditions[1]
                        + nightly_conditions.nightly_conditions[2]
                    )
                    / 3,
                    1,
                )
            )
        return None

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
        if len(self._deepsky_forecast) > 1:
            nightly_conditions = self._deepsky_forecast[1]
            out = ""
            out += (
                CONDITION[
                    4 - math.floor(nightly_conditions.nightly_conditions[0] / 20)
                ].capitalize()
                + "-"
            )
            out += (
                CONDITION[
                    4 - math.floor(nightly_conditions.nightly_conditions[1] / 20)
                ].capitalize()
                + "-"
            )
            out += CONDITION[
                4 - math.floor(nightly_conditions.nightly_conditions[2] / 20)
            ].capitalize()
            return out
        return None

    @property
    def deepsky_forecast_tomorrow_desc(self):
        """Return Forecast Tomorrow Description."""
        if len(self._deepsky_forecast) > 1:
            nightly_conditions = self._deepsky_forecast[1]
            return MAP_WEATHER_TYPE[nightly_conditions.weather]
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
    def wind10m_direction(self) -> str:
        """Return 10m Wind Direction."""
        return self._wind10m.get("direction", "O").upper()

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
        return self._weather
