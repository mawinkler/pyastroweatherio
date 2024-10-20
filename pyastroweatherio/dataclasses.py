"""Defines the Data Classes used."""

import math
from datetime import datetime, timezone

# from pprint import pprint as pp

from pyastroweatherio.const import (
    CONDITION,
    CONDITION_PLAIN,
    DEEP_SKY_THRESHOLD,
    LIFTED_INDEX_PLAIN,
    LIFTED_INDEX_RANGE,
    LIFTED_INDEX_VALUE,
    MAG_DEGRATION_MAX,
    SEEING_MAX,
    WIND10M_DIRECTON,
    WIND10M_MAX,
    WIND10M_PLAIN,
    WIND10M_RANGE,
    WIND10M_VALUE,
)


class ConditionData:
    """A representation of the base class for AstroWeather Data."""

    def __init__(self, data):
        self._seventimer_init = data["seventimer_init"]
        self._seventimer_timepoint = data["seventimer_timepoint"]
        self._forecast_time = data["forecast_time"]

        self._condition_data = data["condition_data"]

    @property
    def seventimer_init(self) -> datetime:
        """Return Forecast Anchor."""

        if self._seventimer_init is not None:
            return self._seventimer_init.replace(microsecond=0, tzinfo=timezone.utc)
        return None

    @property
    def seventimer_timepoint(self) -> int:
        """Return Forecast Hour."""

        if self._seventimer_timepoint is not None:
            return self._seventimer_timepoint
        return None

    @property
    def forecast_time(self) -> datetime:
        """Return Forecast Timestamp."""

        if self._forecast_time is not None:
            return self._forecast_time.replace(microsecond=0, tzinfo=timezone.utc)
        return None

    # #########################################################################
    # Condition
    # #########################################################################
    @property
    def condition_percentage(self) -> int:
        """Return condition based on cloud cover, seeing and transparency."""

        value = self._condition_data.condition_percentage
        if value is not None:
            return int(value)
        return None

    @property
    def cloudcover(self) -> int:
        """Return Cloud Coverage."""

        value = self._condition_data.cloudcover
        if value is not None:
            return int(value)
        return None

    @property
    def cloudcover_percentage(self) -> int:
        """Return Cloud Cover Percentage."""

        value = self._condition_data.cloudcover
        if value is not None:
            return int(value)
        return None

    @property
    def cloudless_percentage(self) -> int:
        """Return Cloudless Percentage."""

        value = self._condition_data.cloudcover
        if value is not None:
            return 100 - int(value)
        return None

    @property
    def cloud_area_fraction_percentage(self) -> int:
        """Return Cloud Cover Percentage."""

        value = self._condition_data.cloud_area_fraction
        if value is not None:
            return int(value)
        return None

    @property
    def cloud_area_fraction_high_percentage(self) -> int:
        """Return Cloud Cover Percentage."""

        value = self._condition_data.cloud_area_fraction_high
        if value is not None:
            return int(value)
        return None

    @property
    def cloud_area_fraction_medium_percentage(self) -> int:
        """Return Cloud Cover Percentage."""

        value = self._condition_data.cloud_area_fraction_medium
        if value is not None:
            return int(value)
        return None

    @property
    def cloud_area_fraction_low_percentage(self) -> int:
        """Return Cloud Cover Percentage."""

        value = self._condition_data.cloud_area_fraction_low
        if value is not None:
            return int(value)
        return None

    @property
    def fog_area_fraction_percentage(self) -> int:
        """Return Fog Area Percentage."""

        value = self._condition_data.fog_area_fraction
        if value is not None:
            return int(value)
        return None

    @property
    def seeing(self) -> float:
        """Return Seeing."""

        value = self._condition_data.seeing
        if value is not None:
            return round(value, 2)
        return None

    @property
    def seeing_percentage(self) -> int:
        """Return Seeing."""

        value = self._condition_data.seeing
        if value is not None:
            return int(100 - value * 100 / SEEING_MAX)
        return None

    @property
    def transparency(self) -> float:
        """Return Transparency."""

        value = self._condition_data.transparency
        if value is not None:
            return round(value, 2)
        return None

    @property
    def transparency_percentage(self) -> int:
        """Return Transparency."""

        value = self._condition_data.transparency
        if value is not None:
            return int(100 - value * 100 / MAG_DEGRATION_MAX)
        return None

    @property
    def lifted_index(self) -> float:
        """Return Lifted Index."""

        value = self._condition_data.lifted_index
        if value is not None:
            return round(value, 2)
        return None

    @property
    def rh2m(self) -> int:
        """Return 2m Relative Humidity."""

        value = self._condition_data.rh2m
        if value is not None:
            return value
        return None

    @property
    def wind10m_speed(self) -> float:
        """Return 10m Wind Speed."""

        value = self._condition_data.wind_speed
        if value is not None:
            return value
        return None

    @property
    def calm_percentage(self) -> int:
        """Return 10m Wind Speed."""

        value = self._condition_data.wind_speed
        if value is not None:
            return int(100 - value * (100 / WIND10M_MAX))
        return None

    @property
    def wind10m_direction(self) -> str:
        """Return 10m Wind Direction."""

        value = self._condition_data.wind_from_direction
        if value is not None:
            direction = value
            direction += 22.5
            direction = direction % 360
            direction = int(direction / 45)  # values 0 to 7
            return WIND10M_DIRECTON[max(0, min(7, direction))]
        return None

    @property
    def temp2m(self) -> int:
        """Return 2m Temperature."""

        value = self._condition_data.temp2m
        if value is not None:
            return value
        return None

    @property
    def dewpoint2m(self) -> float:
        """Return 2m Dew Point."""

        value = self._condition_data.dewpoint2m
        if value is not None:
            return round(value, 1)
        return None

    @property
    def weather(self) -> str:
        """Return Current Weather."""

        value = self._condition_data.weather
        if value is not None:
            return value.replace("_", " ").capitalize()
        return None

    @property
    def weather6(self) -> str:
        """Return Current Weather."""

        value = self._condition_data.weather6
        if value is not None:
            return value.replace("_", " ").capitalize()
        return None

    @property
    def precipitation_amount(self) -> float:
        """Return Current Precipitation Amount."""

        value = self._condition_data.precipitation_amount
        if value is not None:
            return value
        return None

    @property
    def precipitation_amount6(self) -> float:
        """Return Precipitation Amount in next 6 hours."""

        value = self._condition_data.precipitation_amount6
        if value is not None:
            return value
        return None


class LocationData(ConditionData):
    """A representation of the Location AstroWeather Data."""

    def __init__(self, data):
        super().__init__(data)
        self._time_shift = data["time_shift"]
        self._forecast_length = data["forecast_length"]

        self._location_data = data["location_data"]
        self._sun_data = data["sun_data"]
        self._moon_data = data["moon_data"]
        self._darkness_data = data["darkness_data"]
        self._night_duration_astronomical = data["night_duration_astronomical"]
        self._deepsky_forecast = data["deepsky_forecast"]
        self._uptonight = data["uptonight"]
        self._uptonight_bodies = data["uptonight_bodies"]
        self._uptonight_comets = data["uptonight_comets"]

    # #########################################################################
    # Location
    # #########################################################################
    @property
    def time_shift(self) -> int:
        """Return Forecast Timestamp."""

        if self._time_shift is not None:
            return self._time_shift
        return None

    @property
    def forecast_length(self) -> int:
        """Return Forecast Length in Hours."""

        if self._forecast_length is not None:
            return self._forecast_length
        return None

    @property
    def latitude(self) -> float:
        """Return Latitude."""

        if self._location_data.latitude is not None:
            return self._location_data.latitude
        return None

    @property
    def longitude(self) -> float:
        """Return Longitude."""

        if self._location_data.longitude is not None:
            return self._location_data.longitude
        return None

    @property
    def elevation(self) -> float:
        """Return Elevation."""

        if self._location_data.elevation is not None:
            return self._location_data.elevation
        return None

    # #########################################################################
    # Condition
    # #########################################################################
    @property
    def seeing_plain(self) -> str:
        """Return Seeing."""

        return "Deprecated. Use seeing instead."

    @property
    def wind10m_speed_plain(self) -> str:
        """Return wind speed plain."""

        value = self._condition_data.wind_speed
        if value is not None:
            wind_speed_value = 0
            for (start, end), derate in zip(WIND10M_RANGE, WIND10M_VALUE):
                if start <= value <= end:
                    wind_speed_value = derate

            return WIND10M_PLAIN[max(0, min(7, wind_speed_value - 1))]
        return None

    @property
    def lifted_index_plain(self) -> str:
        """Return Lifted Index plain."""

        value = self._condition_data.lifted_index
        if value is not None:
            lifted_index_value = 0
            for (start, end), derate in zip(LIFTED_INDEX_RANGE, LIFTED_INDEX_VALUE):
                if start <= value <= end:
                    lifted_index_value = derate

            return LIFTED_INDEX_PLAIN[max(0, min(7, lifted_index_value - 1))]
        return None

    @property
    def deep_sky_view(self) -> bool:
        """Return True if Deep Sky should be possible."""

        if self.condition_percentage is not None:
            if self.condition_percentage >= DEEP_SKY_THRESHOLD:
                return True
            return False
        return None

    @property
    def condition_plain(self) -> str:
        """Return Current View Conditions."""

        if self.condition_percentage is not None:
            if self.condition_percentage > 80:
                return CONDITION_PLAIN[0].capitalize()
            if self.condition_percentage > 60:
                return CONDITION_PLAIN[1].capitalize()
            if self.condition_percentage > 40:
                return CONDITION_PLAIN[2].capitalize()
            if self.condition_percentage > 20:
                return CONDITION_PLAIN[3].capitalize()
            return CONDITION_PLAIN[4].capitalize()
        return None

    # #########################################################################
    # Sun
    # #########################################################################
    @property
    def sun_altitude(self) -> float:
        """Return Sun Altitude."""

        value = self._sun_data.altitude
        if value is not None:
            return round(value, 3)
        return None

    @property
    def sun_azimuth(self) -> float:
        """Return sun Azimuth."""

        value = self._sun_data.azimuth
        if value is not None:
            return round(value, 3)
        return None

    @property
    def sun_next_rising_astro(self) -> datetime:
        """Return Sun Next Rising Astronomical."""

        value = self._sun_data.next_rising_astro
        if value is not None:
            return value
        return None

    @property
    def sun_next_rising(self) -> datetime:
        """Return Sun Next Rising Civil."""

        value = self._sun_data.next_rising_civil
        if value is not None:
            return value
        return None

    @property
    def sun_next_rising_nautical(self) -> datetime:
        """Return Sun Next Rising Nautical."""

        value = self._sun_data.next_rising_nautical
        if value is not None:
            return value
        return None

    @property
    def sun_next_setting_astro(self) -> datetime:
        """Return Sun Next Setting Astronomical."""

        value = self._sun_data.next_setting_astro
        if value is not None:
            return value
        return None

    @property
    def sun_next_setting(self) -> datetime:
        """Return Next Setting Civil."""

        value = self._sun_data.next_setting_civil
        if value is not None:
            return value
        return None

    @property
    def sun_next_setting_nautical(self) -> datetime:
        """Return Sun Next Setting Nautical."""

        value = self._sun_data.next_setting_nautical
        if value is not None:
            return value
        return None

    # #########################################################################
    # Moon
    # #########################################################################
    @property
    def moon_altitude(self) -> float:
        """Return Moon Altitude."""

        value = self._moon_data.altitude
        if value is not None:
            return round(value, 3)
        return None

    @property
    def moon_angular_size(self) -> float:
        """Return Moon Angular Size in Minutes."""

        value = self._moon_data.angular_size
        if value is not None:
            return round(value, 3)
        return None

    @property
    def moon_azimuth(self) -> float:
        """Return Moon Azimuth."""

        value = self._moon_data.azimuth
        if value is not None:
            return round(value, 3)
        return None

    @property
    def moon_distance_km(self) -> float:
        """Return Moon Distance in km."""

        value = self._moon_data.distance_km
        if value is not None:
            return round(value, 0)
        return None

    @property
    def moon_next_full_moon(self) -> datetime:
        """Return Moon Next Full Moon."""

        value = self._moon_data.next_full_moon
        if value is not None:
            return value
        return None

    @property
    def moon_next_new_moon(self) -> datetime:
        """Return Moon Next New Moon."""

        value = self._moon_data.next_new_moon
        if value is not None:
            return value
        return None

    @property
    def moon_next_rising(self) -> datetime:
        """Return Moon Next Rising."""

        value = self._moon_data.next_rising
        if value is not None:
            return value
        return None

    @property
    def moon_next_setting(self) -> datetime:
        """Return Moon Next Setting."""

        value = self._moon_data.next_setting
        if value is not None:
            return value
        return None

    @property
    def moon_phase(self) -> float:
        """Return Moon Phase."""

        value = self._moon_data.phase
        if value is not None:
            return round(value, 1)
        return None

    @property
    def moon_relative_size(self) -> float:
        """Return Moon Relative Size in %."""

        value = self._moon_data.relative_size
        if value is not None:
            return round(value * 100 - 100, 3)
        return None

    # #########################################################################
    # Darkness
    # #########################################################################
    @property
    def night_duration_astronomical(self) -> float:
        """Returns the remaining timespan of astronomical darkness."""

        if self._night_duration_astronomical is not None:
            return self._night_duration_astronomical
        return None

    @property
    def deep_sky_darkness_moon_rises(self) -> bool:
        """Returns true if moon rises during astronomical night."""

        return self._darkness_data.deep_sky_darkness_moon_rises

    @property
    def deep_sky_darkness_moon_sets(self) -> bool:
        """Returns true if moon sets during astronomical night."""

        return self._darkness_data.deep_sky_darkness_moon_sets

    @property
    def deep_sky_darkness_moon_always_up(self) -> bool:
        """Returns true if moon is up during astronomical night."""

        return self._darkness_data.deep_sky_darkness_moon_always_up

    @property
    def deep_sky_darkness_moon_always_down(self) -> bool:
        """Returns true if moon is down during astronomical night."""

        return self._darkness_data.deep_sky_darkness_moon_always_down

    @property
    def deep_sky_darkness(self) -> float:
        """Returns the remaining timespan of deep sky darkness."""

        return self._darkness_data.deep_sky_darkness

    # #########################################################################
    # Deep Sky Forecast
    # #########################################################################
    @property
    def deepsky_forecast_today(self) -> int:
        """Return Forecas Today in Percent."""

        if self._deepsky_forecast is not None:
            nightly_condition_sum = 0
            if len(self._deepsky_forecast) > 0:
                for nightly_condition in self._deepsky_forecast[0].nightly_conditions:
                    nightly_condition_sum += nightly_condition
                return int(round(nightly_condition_sum / len(self._deepsky_forecast[0].nightly_conditions)))
        return None

    @property
    def deepsky_forecast_today_dayname(self):
        """Return Forecast Todays Dayname."""

        if self._deepsky_forecast is not None:
            if len(self._deepsky_forecast) > 0:
                nightly_conditions = self._deepsky_forecast[0]
                return nightly_conditions.dayname
        return None

    @property
    def deepsky_forecast_today_plain(self):
        """Return Forecast Today."""

        if self._deepsky_forecast is not None:
            out = ""
            if len(self._deepsky_forecast) > 0:
                for nightly_condition in self._deepsky_forecast[0].nightly_conditions:
                    out += CONDITION[4 - math.floor(nightly_condition / 20)].capitalize()
            return out
        return None

    @property
    def deepsky_forecast_today_desc(self):
        """Return Forecast Today Description."""

        if self._deepsky_forecast is not None:
            if len(self._deepsky_forecast) > 0:
                nightly_conditions = self._deepsky_forecast[0]
                return nightly_conditions.weather.replace("_", " ").capitalize()
        return None

    @property
    def deepsky_forecast_today_precipitation_amount6(self) -> float:
        """Return Forecast Today Precipitation Amount6."""

        if self._deepsky_forecast is not None:
            if len(self._deepsky_forecast) > 0:
                nightly_conditions = self._deepsky_forecast[0]
                return nightly_conditions.precipitation_amount6
        return None

    @property
    def deepsky_forecast_tomorrow(self) -> int:
        """Return Forecas Tomorrow in Percentt."""

        if self._deepsky_forecast is not None:
            nightly_condition_sum = 0
            if len(self._deepsky_forecast) > 1:
                for nightly_condition in self._deepsky_forecast[1].nightly_conditions:
                    nightly_condition_sum += nightly_condition
                return int(round(nightly_condition_sum / len(self._deepsky_forecast[1].nightly_conditions)))
        return None

    @property
    def deepsky_forecast_tomorrow_dayname(self):
        """Return Forecast Todays Dayname."""

        if self._deepsky_forecast is not None:
            if len(self._deepsky_forecast) > 1:
                nightly_conditions = self._deepsky_forecast[1]
                return nightly_conditions.dayname
        return None

    @property
    def deepsky_forecast_tomorrow_plain(self):
        """Return Forecast Tomorrow."""

        if self._deepsky_forecast is not None:
            out = ""
            if len(self._deepsky_forecast) > 1:
                for nightly_condition in self._deepsky_forecast[1].nightly_conditions:
                    out += CONDITION[4 - math.floor(nightly_condition / 20)].capitalize()
            return out
        return None

    @property
    def deepsky_forecast_tomorrow_desc(self):
        """Return Forecast Tomorrow Description."""

        if self._deepsky_forecast is not None:
            if len(self._deepsky_forecast) > 1:
                nightly_conditions = self._deepsky_forecast[1]
                return nightly_conditions.weather.replace("_", " ").capitalize()
        return None

    @property
    def deepsky_forecast_tomorrow_precipitation_amount6(self) -> float:
        """Return Forecast Today Precipitation Amount6."""

        if self._deepsky_forecast is not None:
            if len(self._deepsky_forecast) > 0:
                nightly_conditions = self._deepsky_forecast[1]
                return nightly_conditions.precipitation_amount6
        return None

    @property
    def deepsky_forecast(self):
        """Return Deepsky Forecast."""

        if self._deepsky_forecast is not None:
            return self._deepsky_forecast
        return None

    # #########################################################################
    # UpTonight
    # #########################################################################
    @property
    def uptonight(self) -> int:
        """Return the number of best DSOs for tonight."""

        if self._uptonight is not None:
            return len(self._uptonight)
        return None

    @property
    def uptonight_list(self) -> []:
        """Return the list of UpTonight targets."""

        if self._uptonight is not None:
            return self._uptonight
        return None

    # #########################################################################
    # UpTonight Bodies
    # #########################################################################
    @property
    def uptonight_bodies(self) -> int:
        """Return the number of best BODIEs for tonight."""

        if self._uptonight_bodies is not None:
            return len(self._uptonight_bodies)
        return None

    @property
    def uptonight_bodies_list(self) -> []:
        """Return the list of UpTonight bodies."""

        if self._uptonight_bodies is not None:
            return self._uptonight_bodies
        return None

    # #########################################################################
    # UpTonight Comets
    # #########################################################################
    @property
    def uptonight_comets(self) -> int:
        """Return the number of best comets for tonight."""

        if self._uptonight_comets is not None:
            return len(self._uptonight_comets)
        return None

    @property
    def uptonight_comets_list(self) -> []:
        """Return the list of UpTonight comets."""

        if self._uptonight_comets is not None:
            return self._uptonight_comets
        return None


class ForecastData(ConditionData):
    """A representation of 3-Hour Based Forecast AstroWeather Data."""

    def __init__(self, data):
        super().__init__(data)
        self._hour = data["hour"]

    @property
    def hour(self) -> int:
        """Return Forecast Hour of the day."""

        if self._hour is not None:
            return self._hour
        return None

    @property
    def deep_sky_view(self) -> bool:
        """Return True if Deep Sky should be possible."""

        if self.condition_percentage is not None:
            if self.condition_percentage <= DEEP_SKY_THRESHOLD:
                return True
            return False
        return None


class NightlyConditionsData:
    """A representation of nights Sky Quality Data."""

    def __init__(self, data) -> None:
        self._seventimer_init = data["seventimer_init"]
        self._dayname = data["dayname"]
        self._hour = data["hour"]
        self._nightly_conditions = data["nightly_conditions"]
        self._weather = data["weather"]
        self._precipitation_amount6 = data["precipitation_amount6"]

    @property
    def seventimer_init(self) -> datetime:
        """Return Forecast Anchor."""

        if self._seventimer_init is not None:
            return self._seventimer_init
        return None

    @property
    def dayname(self) -> str:
        """Return Forecast Name of the Day."""

        if self._dayname is not None:
            return self._dayname
        return None

    @property
    def hour(self) -> int:
        """Return Forecast Hour."""

        if self._hour is not None:
            return self._hour
        return None

    @property
    def nightly_conditions(self) -> int:
        """Return Forecast Hour."""

        if self._nightly_conditions is not None:
            return self._nightly_conditions
        return None

    @property
    def weather(self) -> str:
        """Return Current Weather."""

        if self._weather is not None:
            return self._weather.replace("_", " ").capitalize()
        return None

    @property
    def precipitation_amount6(self) -> float:
        """Return Current Precipitation Amount 6hrs."""

        if self._precipitation_amount6 is not None:
            return self._precipitation_amount6
        return None


class DSOUpTonight:
    """A representation of uptonight DSO."""

    def __init__(self, data):
        self._id = data["id"]
        self._target_name = data["target_name"]
        self._type = data["type"]
        self._constellation = data["constellation"]
        self._size = data["size"]
        self._visual_magnitude = data["visual_magnitude"]
        self._meridian_transit = data["meridian_transit"]
        self._meridian_antitransit = data["meridian_antitransit"]
        self._foto = data["foto"]

    @property
    def id(self) -> str:
        """Return object catalogue id."""

        if self._id is not None:
            return self._id
        return None

    @property
    def target_name(self) -> str:
        """Return object name."""

        if self._target_name is not None:
            return self._target_name
        return None

    @property
    def type(self) -> str:
        """Return the type of the object."""

        if self._type is not None:
            return self._type
        return None

    @property
    def constellation(self) -> str:
        """Return the constellation of the object."""

        if self._constellation is not None:
            return self._constellation
        return None

    @property
    def size(self) -> float:
        """Return size of the object."""

        if self._size is not None:
            return self._size
        return None

    @property
    def visual_magnitude(self) -> float:
        """Return visual magnitude of the object."""

        if self._visual_magnitude is not None:
            return self._visual_magnitude
        return None

    @property
    def meridian_transit(self) -> datetime:
        """Return the meridian transit time of the object."""

        if self._meridian_transit is not None:
            return self._meridian_transit
        return None

    @property
    def meridian_antitransit(self) -> datetime:
        """Return the meridian anti-transit time of the object."""

        if self._meridian_antitransit is not None:
            return self._meridian_antitransit
        return None

    @property
    def foto(self) -> float:
        """Return fraction of time observable of the object."""

        if self._foto is not None:
            return self._foto
        return None


class BODIESUpTonight:
    """A representation of uptonight bodies."""

    def __init__(self, data):
        self._target_name = data["target_name"]
        self._max_altitude = data["max_altitude"]
        self._azimuth = data["azimuth"]
        self._max_altitude_time = data["max_altitude_time"]
        self._visual_magnitude = data["visual_magnitude"]
        self._meridian_transit = data["meridian_transit"]
        self._foto = data["foto"]

    @property
    def target_name(self) -> str:
        """Return body name."""

        if self._target_name is not None:
            return self._target_name
        return None

    @property
    def max_altitude(self) -> float:
        """Return maximum altitude of the body."""

        if self._max_altitude is not None:
            return self._max_altitude
        return None

    @property
    def azimuth(self) -> float:
        """Return the azimuth of maximum altitude."""

        if self._azimuth is not None:
            return self._azimuth
        return None

    @property
    def max_altitude_time(self) -> datetime:
        """Return date and time of maximum altitude."""

        if self._max_altitude_time is not None:
            return self._max_altitude_time
        return None

    @property
    def visual_magnitude(self) -> float:
        """Return visual magnitude of the body."""

        if self._visual_magnitude is not None:
            return self._visual_magnitude
        return None

    @property
    def meridian_transit(self) -> datetime:
        """Return the meridian transit time of the body."""

        if self._meridian_transit is not None:
            return self._meridian_transit
        return None

    @property
    def foto(self) -> float:
        """Return fraction of time observable of the body."""

        if self._foto is not None:
            return self._foto
        return None


class COMETSUpTonight:
    """A representation of uptonight comets."""

    def __init__(self, data):
        self._designation = data["designation"]
        self._distance_au_earth = data["distance_au_earth"]
        self._distance_au_sun = data["distance_au_sun"]
        self._absolute_magnitude = data["absolute_magnitude"]
        self._visual_magnitude = data["visual_magnitude"]
        self._altitude = data["altitude"]
        self._azimuth = data["azimuth"]
        self._rise_time = data["rise_time"]
        self._set_time = data["set_time"]

    @property
    def designation(self) -> str:
        """Return comet name."""

        if self._designation is not None:
            return self._designation
        return None

    @property
    def distance_au_earth(self) -> float:
        """Return distance to earth in au."""

        if self._distance_au_earth is not None:
            return self._distance_au_earth
        return None

    @property
    def distance_au_sun(self) -> float:
        """Return distance to sun in au."""

        if self._distance_au_sun is not None:
            return self._distance_au_sun
        return None

    @property
    def absolute_magnitude(self) -> float:
        """Return absolute magnitude."""

        if self._absolute_magnitude is not None:
            return self._absolute_magnitude
        return None

    @property
    def visual_magnitude(self) -> float:
        """Return visual magnitude."""

        if self._visual_magnitude is not None:
            return self._visual_magnitude
        return None

    @property
    def altitude(self) -> float:
        """Return altitude."""

        if self._altitude is not None:
            return self._altitude
        return None

    @property
    def azimuth(self) -> float:
        """Return the azimuth of maximum altitude."""

        if self._azimuth is not None:
            return self._azimuth
        return None

    @property
    def rise_time(self) -> datetime:
        """Return rise time."""

        if self._rise_time is not None:
            return self._rise_time
        return None

    @property
    def set_time(self) -> datetime:
        """Return rise time."""

        if self._set_time is not None:
            return self._set_time
        return None
