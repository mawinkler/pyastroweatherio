"""Defines the Data Classes used."""

from datetime import datetime, timezone
import math

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


class BaseData:
    """A representation of the base class for AstroWeather Data."""

    def __init__(self, data):
        self._seventimer_init = data["seventimer_init"]
        self._seventimer_timepoint = data["seventimer_timepoint"]
        self._forecast_time = data["forecast_time"]

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
        self._precipitation_amount6 = data["precipitation_amount6"]

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

    @property
    def condition_percentage(self) -> int:
        """Return condition based on cloud cover, seeing and transparency."""

        if self._condition_percentage is not None:
            return int(self._condition_percentage)
        return None

    @property
    def cloudcover(self) -> int:
        """Return Cloud Coverage."""

        if self._cloudcover is not None:
            return int(self._cloudcover)
        return None

    @property
    def cloudcover_percentage(self) -> int:
        """Return Cloud Cover Percentage."""

        if self._cloudcover is not None:
            return int(self._cloudcover)
        return None

    @property
    def cloudless_percentage(self) -> int:
        """Return Cloudless Percentage."""

        if self._cloudcover is not None:
            return 100 - int(self._cloudcover)
        return None

    @property
    def cloud_area_fraction_percentage(self) -> int:
        """Return Cloud Cover Percentage."""

        if self._cloud_area_fraction is not None:
            return int(self._cloud_area_fraction)
        return None

    @property
    def cloud_area_fraction_high_percentage(self) -> int:
        """Return Cloud Cover Percentage."""

        if self._cloud_area_fraction_high is not None:
            return int(self._cloud_area_fraction_high)
        return None

    @property
    def cloud_area_fraction_medium_percentage(self) -> int:
        """Return Cloud Cover Percentage."""

        if self._cloud_area_fraction_medium is not None:
            return int(self._cloud_area_fraction_medium)
        return None

    @property
    def cloud_area_fraction_low_percentage(self) -> int:
        """Return Cloud Cover Percentage."""

        if self._cloud_area_fraction_low is not None:
            return int(self._cloud_area_fraction_low)
        return None

    @property
    def fog_area_fraction_percentage(self) -> int:
        """Return Fog Area Percentage."""

        if self._fog_area_fraction is not None:
            return int(self._fog_area_fraction)
        return None

    @property
    def seeing(self) -> float:
        """Return Seeing."""

        if self._seeing is not None:
            return round(self._seeing, 2)
        return None

    @property
    def seeing_percentage(self) -> int:
        """Return Seeing."""

        if self._seeing is not None:
            return int(100 - self._seeing * 100 / SEEING_MAX)
        return None

    @property
    def transparency(self) -> float:
        """Return Transparency."""

        if self._transparency is not None:
            return round(self._transparency, 2)
        return None

    @property
    def transparency_percentage(self) -> int:
        """Return Transparency."""

        if self._transparency is not None:
            return int(100 - self._transparency * 100 / MAG_DEGRATION_MAX)
        return None

    @property
    def lifted_index(self) -> float:
        """Return Lifted Index."""

        if self._lifted_index is not None:
            return round(self._lifted_index, 2)
        return None

    @property
    def rh2m(self) -> int:
        """Return 2m Relative Humidity."""

        if self._rh2m is not None:
            return self._rh2m
        return None

    @property
    def wind10m_speed(self) -> float:
        """Return 10m Wind Speed."""

        if self._wind_speed is not None:
            return self._wind_speed
        return None

    @property
    def calm_percentage(self) -> int:
        """Return 10m Wind Speed."""

        if self._wind_speed is not None:
            return int(100 - self._wind_speed * (100 / WIND10M_MAX))
        return None

    @property
    def wind10m_direction(self) -> str:
        """Return 10m Wind Direction."""

        if self._wind_from_direction is not None:
            direction = self._wind_from_direction
            direction += 22.5
            direction = direction % 360
            direction = int(direction / 45)  # values 0 to 7
            return WIND10M_DIRECTON[max(0, min(7, direction))]
        return None

    @property
    def temp2m(self) -> int:
        """Return 2m Temperature."""

        if self._temp2m is not None:
            return self._temp2m
        return None

    @property
    def dewpoint2m(self) -> float:
        """Return 2m Dew Point."""

        if self._dewpoint2m is not None:
            return round(self._dewpoint2m, 1)
        return None

    @property
    def weather(self) -> str:
        """Return Current Weather."""

        if self._weather is not None:
            return self._weather.replace("_", " ").capitalize()
        return None

    @property
    def weather6(self) -> str:
        """Return Current Weather."""

        if self._weather6 is not None:
            return self._weather6.replace("_", " ").capitalize()
        return None

    @property
    def precipitation_amount(self) -> float:
        """Return Current Precipitation Amount."""

        if self._precipitation_amount is not None:
            return self._precipitation_amount
        return None

    @property
    def precipitation_amount6(self) -> float:
        """Return Precipitation Amount in next 6 hours."""

        if self._precipitation_amount6 is not None:
            return self._precipitation_amount6
        return None


class LocationData(BaseData):
    """A representation of the Location AstroWeather Data."""

    def __init__(self, data):
        super().__init__(data)
        self._time_shift = data["time_shift"]
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
        self._moon_next_full_moon = data["moon_next_full_moon"]
        self._moon_altitude = data["moon_altitude"]
        self._moon_azimuth = data["moon_azimuth"]
        self._night_duration_astronomical = data["night_duration_astronomical"]
        self._deep_sky_darkness_moon_rises = data["deep_sky_darkness_moon_rises"]
        self._deep_sky_darkness_moon_sets = data["deep_sky_darkness_moon_sets"]
        self._deep_sky_darkness_moon_always_up = data[
            "deep_sky_darkness_moon_always_up"
        ]
        self._deep_sky_darkness_moon_always_down = data[
            "deep_sky_darkness_moon_always_down"
        ]
        self._deep_sky_darkness = data["deep_sky_darkness"]
        self._deepsky_forecast = data["deepsky_forecast"]
        self._uptonight = data["uptonight"]
        self._uptonight_bodies = data["uptonight_bodies"]
        self._uptonight_comets = data["uptonight_comets"]

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

        if self._latitude is not None:
            return self._latitude
        return None

    @property
    def longitude(self) -> float:
        """Return Longitude."""

        if self._longitude is not None:
            return self._longitude
        return None

    @property
    def elevation(self) -> float:
        """Return Elevation."""

        if self._elevation is not None:
            return self._elevation
        return None

    @property
    def seeing_plain(self) -> str:
        """Return Seeing."""

        return "Deprecated. Use seeing instead."

    @property
    def wind10m_speed_plain(self) -> str:
        """Return wind speed plain."""

        if self._wind_speed is not None:
            wind_speed_value = 0
            for (start, end), derate in zip(WIND10M_RANGE, WIND10M_VALUE):
                if start <= self._wind_speed <= end:
                    wind_speed_value = derate

            return WIND10M_PLAIN[max(0, min(7, wind_speed_value - 1))]
        return None

    @property
    def lifted_index_plain(self) -> str:
        """Return Lifted Index plain."""

        if self._lifted_index is not None:
            lifted_index_value = 0
            for (start, end), derate in zip(LIFTED_INDEX_RANGE, LIFTED_INDEX_VALUE):
                if start <= self._lifted_index <= end:
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

    @property
    def sun_next_rising(self) -> datetime:
        """Return Sun Next Rising Civil."""

        if isinstance(self._sun_next_rising, datetime):
            return self._sun_next_rising
        return None

    @property
    def sun_next_rising_nautical(self) -> datetime:
        """Return Sun Next Rising Nautical."""

        if isinstance(self._sun_next_rising_nautical, datetime):
            return self._sun_next_rising_nautical
        return None

    @property
    def sun_next_rising_astro(self) -> datetime:
        """Return Sun Next Rising Astronomical."""

        if isinstance(self._sun_next_rising_astro, datetime):
            return self._sun_next_rising_astro
        return None

    @property
    def sun_next_setting(self) -> datetime:
        """Return Next Setting Civil."""

        if isinstance(self._sun_next_setting, datetime):
            return self._sun_next_setting
        return None

    @property
    def sun_next_setting_nautical(self) -> datetime:
        """Return Sun Next Setting Nautical."""

        if isinstance(self._sun_next_setting_nautical, datetime):
            return self._sun_next_setting_nautical
        return None

    @property
    def sun_next_setting_astro(self) -> datetime:
        """Return Sun Next Setting Astronomical."""

        if isinstance(self._sun_next_setting_astro, datetime):
            return self._sun_next_setting_astro
        return None

    @property
    def sun_altitude(self) -> float:
        """Return Sun Altitude."""

        if self._sun_altitude is not None:
            return round(self._sun_altitude, 3)
        return None

    @property
    def sun_azimuth(self) -> float:
        """Return sun Azimuth."""

        if self._sun_azimuth is not None:
            return round(self._sun_azimuth, 3)
        return None

    @property
    def moon_next_rising(self) -> datetime:
        """Return Moon Next Rising."""

        if isinstance(self._moon_next_rising, datetime):
            return self._moon_next_rising
        return None

    @property
    def moon_next_setting(self) -> datetime:
        """Return Moon Next Setting."""

        if isinstance(self._moon_next_setting, datetime):
            return self._moon_next_setting
        return None

    @property
    def moon_phase(self) -> float:
        """Return Moon Phase."""

        if self._moon_phase is not None:
            return round(self._moon_phase, 1)
        return None

    @property
    def moon_next_new_moon(self) -> datetime:
        """Return Moon Next New Moon."""

        if isinstance(self._moon_next_new_moon, datetime):
            return self._moon_next_new_moon
        return None

    @property
    def moon_next_full_moon(self) -> datetime:
        """Return Moon Next Full Moon."""

        if isinstance(self._moon_next_full_moon, datetime):
            return self._moon_next_full_moon
        return None

    @property
    def moon_altitude(self) -> float:
        """Return Moon Altitude."""

        if self._moon_altitude is not None:
            return round(self._moon_altitude, 3)
        return None

    @property
    def moon_azimuth(self) -> float:
        """Return Moon Azimuth."""

        if self._moon_azimuth is not None:
            return round(self._moon_azimuth, 3)
        return None

    @property
    def night_duration_astronomical(self) -> float:
        """Returns the remaining timespan of astronomical darkness."""

        if self._night_duration_astronomical is not None:
            return self._night_duration_astronomical
        return None

    @property
    def deep_sky_darkness_moon_rises(self) -> bool:
        """Returns true if moon rises during astronomical night."""

        if self._deep_sky_darkness_moon_rises is not None:
            return self._deep_sky_darkness_moon_rises
        return None

    @property
    def deep_sky_darkness_moon_sets(self) -> bool:
        """Returns true if moon sets during astronomical night."""

        if self._deep_sky_darkness_moon_sets is not None:
            return self._deep_sky_darkness_moon_sets
        return None

    @property
    def deep_sky_darkness_moon_always_up(self) -> bool:
        """Returns true if moon is up during astronomical night."""

        if self._deep_sky_darkness_moon_always_up is not None:
            return self._deep_sky_darkness_moon_always_up
        return None

    @property
    def deep_sky_darkness_moon_always_down(self) -> bool:
        """Returns true if moon is down during astronomical night."""

        if self._deep_sky_darkness_moon_always_down is not None:
            return self._deep_sky_darkness_moon_always_down
        return None

    @property
    def deep_sky_darkness(self) -> float:
        """Returns the remaining timespan of deep sky darkness."""

        if self._deep_sky_darkness is not None:
            return self._deep_sky_darkness
        return None

    @property
    def deepsky_forecast_today(self) -> int:
        """Return Forecas Today in Percent."""

        if self._deepsky_forecast is not None:
            nightly_condition_sum = 0
            if len(self._deepsky_forecast) > 0:
                for nightly_condition in self._deepsky_forecast[0].nightly_conditions:
                    nightly_condition_sum += nightly_condition
                return int(
                    round(
                        nightly_condition_sum
                        / len(self._deepsky_forecast[0].nightly_conditions)
                    )
                )
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
                    out += CONDITION[
                        4 - math.floor(nightly_condition / 20)
                    ].capitalize()
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
                return int(
                    round(
                        nightly_condition_sum
                        / len(self._deepsky_forecast[1].nightly_conditions)
                    )
                )
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
                    out += CONDITION[
                        4 - math.floor(nightly_condition / 20)
                    ].capitalize()
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


class ForecastData(BaseData):
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
    def size(self) -> str:
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
    def foto(self) -> str:
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
    def foto(self) -> str:
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
        # self._ra = data["ra"]
        # self._dec = data["dec"]
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
