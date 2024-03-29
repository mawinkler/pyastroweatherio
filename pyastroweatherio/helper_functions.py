""" Contains Helper functions for AstroWeather."""
from datetime import datetime, timedelta
import logging
import ephem
from ephem import degree
from math import degrees as deg
import pytz

# The introduction of the module [timezonefinder](https://github.com/jannikmi/timezonefinder)
# with it's nested dependency to [py-h3](https://github.com/uber/h3-py) failed while compiling
# the `c`-module h3 on some home assistant deployment variants (e.g. Home Assistant
# Operating System on RPi).
# from timezonefinder import TimezoneFinder
from pyastroweatherio.const import (
    DEFAULT_ELEVATION,
    DEFAULT_TIMEZONE,
    HOME_LATITUDE,
    HOME_LONGITUDE,
    CIVIL_TWILIGHT,
    CIVIL_DUSK_DAWN,
    NAUTICAL_TWILIGHT,
    NAUTICAL_DUSK_DAWN,
    ASTRONOMICAL_TWILIGHT,
    ASTRONOMICAL_DUSK_DAWN,
)

_LOGGER = logging.getLogger(__name__)


class ConversionFunctions:
    """Convert between different Weather Units."""

    async def epoch_to_datetime(self, value) -> str:
        """Converts EPOC time to Date Time String."""
        return datetime.datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d %H:%M:%S")

    async def anchor_timestamp(self, value) -> datetime:
        """Converts the datetime string from 7Timer to DateTime."""
        _LOGGER.debug("7timer anchor timestamp: %s", str(datetime.strptime(value, "%Y%m%d%H")))
        return datetime.strptime(value, "%Y%m%d%H")


class AstronomicalRoutines:
    """Calculate different astronomical objects"""

    def __init__(
        self,
        latitude=HOME_LATITUDE,
        longitude=HOME_LONGITUDE,
        elevation=DEFAULT_ELEVATION,
        timezone_info=DEFAULT_TIMEZONE,
        forecast_time=None,
    ):
        self._latitude = latitude
        self._longitude = longitude
        self._elevation = elevation
        self._timezone_info = timezone_info
        # tz_find = TimezoneFinder()
        # self._timezone_info = tz_find.timezone_at(lng=longitude, lat=latitude)
        self._test_mode = False
        _LOGGER.debug("Timezone: %s", self._timezone_info)
        if forecast_time is None:
            self._forecast_time = datetime.utcnow().replace(tzinfo=pytz.utc)
        else:
            self._forecast_time = forecast_time.replace(tzinfo=pytz.utc)
            self._test_mode = True
        _LOGGER.debug("Forecast Time: %s", self._forecast_time)

        self._sun_observer = None
        self._sun_observer_nautical = None
        self._sun_observer_astro = None
        self._moon_observer = None
        self._sun_next_rising_civil = None
        self._sun_next_setting_civil = None
        self._sun_next_rising_nautical = None
        self._sun_next_setting_nautical = None
        self._sun_next_rising_astro = None
        self._sun_next_setting_astro = None
        self._sun_altitude = None
        self._sun_azimuth = None
        self._moon_next_rising = None
        self._moon_next_setting = None
        self._moon_next_new_moon = None
        self._moon_next_full_moon = None
        self._moon_altitude = None
        self._moon_azimuth = None
        self._sun = None
        self._moon = None

        # Internal only
        self._sun_previous_rising_astro = None
        self._sun_previous_setting_astro = None
        self._moon_previous_rising = None
        self._moon_previous_setting = None
        # self._moon_day_after_next_rising = None
        # self._moon_day_after_next_setting = None

    def utc_to_local(self, utc_dt):
        """Localizes the datetime"""
        local_tz = pytz.timezone(self._timezone_info)
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(local_dt)

    def utc_to_local_diff(self):
        """returns the UTC Offset"""
        now = datetime.now(pytz.timezone(self._timezone_info))
        return now.utcoffset().total_seconds() / 3600

    #
    # Observers
    #
    def get_sun_observer(self, below_horizon=ASTRONOMICAL_DUSK_DAWN) -> ephem.Observer:
        """Retrieves the ephem sun observer for the current location"""
        observer = ephem.Observer()
        observer.lon = str(self._longitude)  # * degree
        observer.lat = str(self._latitude)  # * degree
        observer.elevation = self._elevation
        observer.horizon = below_horizon * degree
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")
        return observer

    def get_moon_observer(self) -> ephem.Observer:
        """Retrieves the ephem mon observer for the current location"""
        observer = ephem.Observer()
        observer.lon = str(self._longitude)  # * degree
        observer.lat = str(self._latitude)  # * degree
        observer.elevation = self._elevation
        # Naval Observatory Risings and Settings
        # Set horizon to minus 34 arcminutes
        # https://aa.usno.navy.mil/data/RS_OneDay
        observer.horizon = "-0:34"
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")
        return observer

    #
    # Sun & Moon
    #
    def calculate_sun(self):
        """Calculates sun risings and settings"""
        if self._sun_observer is None:
            self._sun_observer = self.get_sun_observer(CIVIL_DUSK_DAWN)
        if self._sun_observer_nautical is None:
            self._sun_observer_nautical = self.get_sun_observer(NAUTICAL_DUSK_DAWN)
        if self._sun_observer_astro is None:
            self._sun_observer_astro = self.get_sun_observer(ASTRONOMICAL_DUSK_DAWN)
        if self._sun is None:
            self._sun = ephem.Sun()

        # Rise and Setting (Civil)
        try:
            self._sun_next_rising_civil = (
                self._sun_observer.next_rising(ephem.Sun(), use_center=True).datetime().replace(tzinfo=pytz.utc)
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            # Search for the next rising
            start = self._sun_observer.date.datetime()
            end = self._sun_observer.date.datetime() + timedelta(days=365)
            timestamp = start
            while timestamp < end:
                timestamp += timedelta(minutes=1440)
                self._sun_observer.date = timestamp
                try:
                    self._sun_next_rising_astro = self._sun_observer.next_rising(
                        ephem.Sun(), use_center=True
                    ).datetime()
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_next_setting_civil = (
                self._sun_observer.next_setting(ephem.Sun(), use_center=True).datetime().replace(tzinfo=pytz.utc)
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            # Search for the next setting
            start = self._sun_observer.date.datetime()
            end = self._sun_observer.date.datetime() + timedelta(days=365)
            timestamp = start
            while timestamp < end:
                timestamp += timedelta(minutes=1440)
                self._sun_observer.date = timestamp
                try:
                    self._sun_next_setting_astro = self._sun_observer.next_setting(
                        ephem.Sun(), use_center=True
                    ).datetime()
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        # Rise and Setting (Nautical)
        self._sun_observer_nautical.date = self._forecast_time
        self._sun.compute(self._sun_observer_nautical)

        try:
            self._sun_next_rising_nautical = (
                self._sun_observer_nautical.next_rising(ephem.Sun(), use_center=True)
                .datetime()
                .replace(tzinfo=pytz.utc)
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            # Search for the next astronomical rising
            start = self._sun_observer_nautical.date.datetime()
            end = self._sun_observer_nautical.date.datetime() + timedelta(days=365)
            timestamp = start
            while timestamp < end:
                timestamp += timedelta(minutes=1440)
                self._sun_observer_nautical.date = timestamp
                try:
                    self._sun_next_rising_nautical = (
                        self._sun_observer_nautical.next_rising(ephem.Sun(), use_center=True)
                        .datetime()
                        .replace(tzinfo=pytz.utc)
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_next_setting_nautical = (
                self._sun_observer_nautical.next_setting(ephem.Sun(), use_center=True)
                .datetime()
                .replace(tzinfo=pytz.utc)
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            # Search for the next astronomical setting
            start = self._sun_observer_nautical.date.datetime()
            end = self._sun_observer_nautical.date.datetime() + timedelta(days=365)
            timestamp = start
            while timestamp < end:
                timestamp += timedelta(minutes=1440)
                self._sun_observer_nautical.date = timestamp
                try:
                    self._sun_next_setting_nautical = (
                        self._sun_observer_nautical.next_setting(ephem.Sun(), use_center=True)
                        .datetime()
                        .replace(tzinfo=pytz.utc)
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        # Rise and Setting (Astronomical)
        self._sun_observer_astro.date = self._forecast_time
        self._sun.compute(self._sun_observer_astro)

        try:
            self._sun_next_rising_astro = (
                self._sun_observer_astro.next_rising(ephem.Sun(), use_center=True).datetime().replace(tzinfo=pytz.utc)
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            # Search for the next astronomical rising
            start = self._sun_observer_astro.date.datetime()
            end = self._sun_observer_astro.date.datetime() + timedelta(days=365)
            timestamp = start
            while timestamp < end:
                timestamp += timedelta(minutes=1440)
                self._sun_observer_astro.date = timestamp
                try:
                    self._sun_next_rising_astro = (
                        self._sun_observer_astro.next_rising(ephem.Sun(), use_center=True)
                        .datetime()
                        .replace(tzinfo=pytz.utc)
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_previous_rising_astro = (
                self._sun_observer_astro.previous_rising(ephem.Sun(), use_center=True)
                .datetime()
                .replace(tzinfo=pytz.utc)
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            # Search for the previous astronomical rising
            start = self._sun_observer_astro.date.datetime()
            end = self._sun_observer_astro.date.datetime() - timedelta(days=365)
            timestamp = start
            while timestamp > end:
                timestamp -= timedelta(minutes=1440)
                self._sun_observer_astro.date = timestamp
                try:
                    self._sun_previous_rising_astro = (
                        self._sun_observer_astro.previous_rising(ephem.Sun(), use_center=True)
                        .datetime()
                        .replace(tzinfo=pytz.utc)
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_next_setting_astro = (
                self._sun_observer_astro.next_setting(ephem.Sun(), use_center=True).datetime().replace(tzinfo=pytz.utc)
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            # Search for the next astronomical setting
            start = self._sun_observer_astro.date.datetime()
            end = self._sun_observer_astro.date.datetime() + timedelta(days=365)
            timestamp = start
            while timestamp < end:
                timestamp += timedelta(minutes=1440)
                self._sun_observer_astro.date = timestamp
                try:
                    self._sun_next_setting_astro = (
                        self._sun_observer_astro.next_setting(ephem.Sun(), use_center=True)
                        .datetime()
                        .replace(tzinfo=pytz.utc)
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_previous_setting_astro = (
                self._sun_observer_astro.previous_setting(ephem.Sun(), use_center=True)
                .datetime()
                .replace(tzinfo=pytz.utc)
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            # Search for the previous astronomical setting
            start = self._sun_observer_astro.date.datetime()
            end = self._sun_observer_astro.date.datetime() - timedelta(days=365)
            timestamp = start
            while timestamp > end:
                timestamp -= timedelta(minutes=1440)
                self._sun_observer_astro.date = timestamp
                try:
                    self._sun_previous_setting_astro = (
                        self._sun_observer_astro.previous_setting(ephem.Sun(), use_center=True)
                        .datetime()
                        .replace(tzinfo=pytz.utc)
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

    def calculate_sun_altaz(self):
        """Calculates sun altitude and azimuth"""
        if self._sun_observer is None:
            self._sun_observer = self.get_sun_observer(CIVIL_DUSK_DAWN)
        if self._sun is None:
            self._sun = ephem.Sun()

        self._sun_observer.date = self._forecast_time
        self._sun.compute(self._sun_observer)

        # Sun Altitude
        self._sun_altitude = deg(float(self._sun.alt))

        # Sun Azimuth
        self._sun_azimuth = deg(float(self._sun.az))

    def calculate_moon(self):
        """Calculates moon rising and setting"""
        if self._moon_observer is None:
            self._moon_observer = self.get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()

        # Rise and Setting
        self._moon_observer.date = self._forecast_time
        self._moon.compute(self._moon_observer)

        try:
            self._moon_next_rising = self._moon_observer.next_rising(ephem.Moon()).datetime().replace(tzinfo=pytz.utc)
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            pass

        try:
            self._moon_next_setting = self._moon_observer.next_setting(ephem.Moon()).datetime().replace(tzinfo=pytz.utc)
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            pass

        try:
            self._moon_previous_rising = (
                self._moon_observer.previous_rising(ephem.Moon()).datetime().replace(tzinfo=pytz.utc)
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            pass

        try:
            self._moon_previous_setting = (
                self._moon_observer.previous_setting(ephem.Moon()).datetime().replace(tzinfo=pytz.utc)
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            pass

        # self._moon_observer.date = self._forecast_time + timedelta(days=1)
        # self._moon.compute(self._moon_observer)

        # try:
        #     self._moon_day_after_next_rising = self._moon_observer.next_rising(ephem.Moon()).datetime().replace(tzinfo=pytz.utc)
        # except (ephem.AlwaysUpError, ephem.NeverUpError):
        #     pass

        # try:
        #     self._moon_day_after_next_setting = self._moon_observer.next_setting(ephem.Moon()).datetime().replace(tzinfo=pytz.utc)
        # except (ephem.AlwaysUpError, ephem.NeverUpError):
        #     pass

        # Next new Moon
        self._moon_next_new_moon = ephem.next_new_moon(self._forecast_time).datetime().replace(tzinfo=pytz.utc)

        # Next full Moon
        self._moon_next_full_moon = ephem.next_full_moon(self._forecast_time).datetime().replace(tzinfo=pytz.utc)

    def calculate_moon_altaz(self):
        """Calculates moon altitude and azimuth"""
        if self._moon_observer is None:
            self._moon_observer = self.get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()

        self._moon_observer.date = self._forecast_time
        self._moon.compute(self._moon_observer)

        # Moon Altitude
        self._moon_altitude = deg(float(self._moon.alt))

        # Moon Azimuth
        self._moon_azimuth = deg(float(self._moon.az))

    async def sun_previous_rising_astro(self) -> datetime:
        """Returns sun previous astronomical rising"""
        if self._sun_previous_rising_astro is None or self._forecast_time > self._sun_previous_rising_astro:
            _LOGGER.debug("Astronomical calculations updating sun_previous_rising_astro")
            self.calculate_sun()

        if self._sun_previous_rising_astro is not None:
            return self._sun_previous_rising_astro

    async def sun_previous_setting_astro(self) -> datetime:
        """Returns sun previous astronomical setting"""
        if self._sun_previous_setting_astro is None or self._forecast_time > self._sun_previous_setting_astro:
            _LOGGER.debug("Astronomical calculations updating sun_previous_setting_astro")
            self.calculate_sun()

        if self._sun_previous_setting_astro is not None:
            return self._sun_previous_setting_astro

    def astronomical_darkness(self) -> bool:
        """Returns true during astronomical night"""

        if self._sun_next_setting_astro > self._sun_next_rising_astro:
            return True
        return False

    def moon_down(self) -> bool:
        """Returns true while moon is set"""

        if self._moon_next_setting > self._moon_next_rising:
            return True
        return False

    #
    # Public methods
    #
    async def time_shift(self) -> int:
        """Returns the time_shift to UTC"""
        return self.utc_to_local_diff() * 3600
        
    async def need_update(self, forecast_time=None):
        """Update Sun and Moon"""
        if forecast_time is not None:
            self._forecast_time = forecast_time.replace(tzinfo=pytz.utc)

        self.calculate_sun_altaz()
        self.calculate_moon_altaz()

        if (
            self._sun_next_setting_civil is None
            or self._sun_next_setting_nautical is None
            or self._sun_next_setting_astro is None
            or self._sun_next_rising_astro is None
            or self._sun_next_rising_nautical is None
            or self._sun_next_rising_civil is None
            or self._moon_next_rising is None
            or self._moon_next_setting is None
            or self._forecast_time > self._sun_next_setting_civil
            or self._forecast_time > self._sun_next_setting_nautical
            or self._forecast_time > self._sun_next_setting_astro
            or self._forecast_time > self._sun_next_rising_astro
            or self._forecast_time > self._sun_next_rising_nautical
            or self._forecast_time > self._sun_next_rising_civil
            or self._forecast_time > self._moon_next_rising
            or self._forecast_time > self._moon_next_setting
        ):
            _LOGGER.debug("Astronomical calculations updating")
            self.calculate_sun()
            self.calculate_moon()

    # Return Sun information
    async def sun_next_rising(self) -> datetime:
        """Returns sun next rising"""
        if (
            self._sun_next_rising_astro is None
            or self._sun_next_rising_nautical is None
            or self._sun_next_rising_civil is None
            or self._forecast_time > self._sun_next_rising_astro
            or self._forecast_time > self._sun_next_rising_nautical
            or self._forecast_time > self._sun_next_rising_civil
        ):
            _LOGGER.debug("Astronomical calculations updating sun_next_rising")
            self.calculate_sun()

        if self._sun_next_rising_astro is not None:
            return self._sun_next_rising_astro
        if self._sun_next_rising_nautical is not None:
            return self._sun_next_rising_nautical
        if self._sun_next_rising_civil is not None:
            return self._sun_next_rising_civil

    async def sun_next_rising_civil(self) -> datetime:
        """Returns sun next rising"""
        if self._sun_next_setting_civil is None or self._forecast_time > self._sun_next_setting_civil:
            _LOGGER.debug("Astronomical calculations updating sun_next_rising_civil")
            self.calculate_sun()

        if self._sun_next_rising_civil is not None:
            return self._sun_next_rising_civil

    async def sun_next_rising_nautical(self) -> datetime:
        """Returns sun next nautical rising"""
        if self._sun_next_rising_nautical is None or self._forecast_time > self._sun_next_rising_nautical:
            _LOGGER.debug("Astronomical calculations updating sun_next_rising_nautical")
            self.calculate_sun()

        if self._sun_next_rising_nautical is not None:
            return self._sun_next_rising_nautical

    async def sun_next_rising_astro(self) -> datetime:
        """Returns sun next astronomical rising"""
        if self._sun_next_rising_astro is None or self._forecast_time > self._sun_next_rising_astro:
            _LOGGER.debug("Astronomical calculations updating sun_next_rising_astro")
            self.calculate_sun()

        if self._sun_next_rising_astro is not None:
            return self._sun_next_rising_astro

    async def sun_next_setting(self) -> datetime:
        """Returns sun next setting"""
        if (
            self._sun_next_setting_civil is None
            or self._sun_next_setting_nautical is None
            or self._sun_next_setting_astro is None
            or self._forecast_time > self._sun_next_setting_civil
            or self._forecast_time > self._sun_next_setting_nautical
            or self._forecast_time > self._sun_next_setting_astro
        ):
            _LOGGER.debug("Astronomical calculations updating sun_next_setting")
            self.calculate_sun()

        if self._sun_next_setting_astro is not None:
            return self._sun_next_setting_astro
        if self._sun_next_setting_nautical is not None:
            return self._sun_next_setting_nautical
        if self._sun_next_setting_civil is not None:
            return self._sun_next_setting_civil

    async def sun_next_setting_civil(self) -> datetime:
        """Returns sun next setting"""
        if self._sun_next_setting_civil is None or self._forecast_time > self._sun_next_setting_civil:
            _LOGGER.debug("Astronomical calculations updating sun_next_setting_civil")
            self.calculate_sun()

        if self._sun_next_setting_civil is not None:
            return self._sun_next_setting_civil

    async def sun_next_setting_nautical(self) -> datetime:
        """Returns sun next nautical setting"""
        if self._sun_next_setting_nautical is None or self._forecast_time > self._sun_next_setting_nautical:
            _LOGGER.debug("Astronomical calculations updating sun_next_setting_nautical")
            self.calculate_sun()

        if self._sun_next_setting_nautical is not None:
            return self._sun_next_setting_nautical

    async def sun_next_setting_astro(self) -> datetime:
        """Returns sun next astronomical setting"""
        if self._sun_next_setting_astro is None or self._forecast_time > self._sun_next_setting_astro:
            _LOGGER.debug("Astronomical calculations updating sun_next_setting_astro")
            self.calculate_sun()

        if self._sun_next_setting_astro is not None:
            return self._sun_next_setting_astro

    async def sun_altitude(self) -> float:
        """Returns the sun altitude"""
        self.calculate_sun_altaz()

        if self._sun_altitude is not None:
            return self._sun_altitude

    async def sun_azimuth(self) -> float:
        """Returns the sun azimuth"""
        self.calculate_sun_altaz()

        if self._sun_azimuth is not None:
            return self._sun_azimuth

    # Return Moon information
    async def moon_next_rising(self) -> datetime:
        if self._moon_next_rising is None or self._forecast_time > self._moon_next_rising:
            _LOGGER.debug("Astronomical calculations updating moon_next_rising")
            self.calculate_moon()

        """Returns moon next rising"""
        if self._moon_next_rising is not None:
            return self._moon_next_rising

    async def moon_next_setting(self) -> datetime:
        if self._moon_next_setting is None or self._forecast_time > self._moon_next_setting:
            _LOGGER.debug("Astronomical calculations updating moon_next_setting")
            self.calculate_moon()

        """Returns moon next setting"""
        if self._moon_next_setting is not None:
            return self._moon_next_setting

    async def moon_phase(self) -> float:
        """Returns the moon phase"""
        self.calculate_moon()

        if self._moon is not None:
            return self._moon.phase

    async def moon_next_new_moon(self) -> float:
        """Returns the next new moon"""
        if self._moon_next_new_moon is None or self._forecast_time > self._moon_next_new_moon:
            _LOGGER.debug("Astronomical calculations updating moon_next_new_moon")
            self.calculate_moon()

        if self._moon_next_new_moon is not None:
            return self._moon_next_new_moon

    async def moon_next_full_moon(self) -> float:
        """Returns the next full moon"""
        if self._moon_next_full_moon is None or self._forecast_time > self._moon_next_full_moon:
            _LOGGER.debug("Astronomical calculations updating moon_next_full_moon")
            self.calculate_moon()

        if self._moon_next_full_moon is not None:
            return self._moon_next_full_moon

    async def moon_altitude(self) -> float:
        """Returns the moon altitude"""
        self.calculate_moon_altaz()

        if self._moon_altitude is not None:
            return self._moon_altitude

    async def moon_azimuth(self) -> float:
        """Returns the moon azimuth"""
        self.calculate_moon_altaz()

        if self._moon_azimuth is not None:
            return self._moon_azimuth

    # Astronomical Night and Darkness information
    async def night_duration_astronomical(self) -> float:
        """Returns the remaining timespan of astronomical darkness"""
        start_timestamp = None

        # Are we already in darkness?
        if self.astronomical_darkness():
            start_timestamp = self._sun_previous_setting_astro
        else:
            start_timestamp = self._sun_next_setting_astro

        astroduration = self._sun_next_rising_astro - start_timestamp

        return astroduration.total_seconds()

    async def deep_sky_darkness_moon_rises(self) -> bool:
        """Returns true if moon rises during astronomical night"""
        start_timestamp = None

        # Are we already in darkness?
        if self.astronomical_darkness():
            start_timestamp = self._sun_previous_setting_astro
        else:
            start_timestamp = self._sun_next_setting_astro

        if self._moon_next_rising > start_timestamp and self._moon_next_rising < self._sun_next_rising_astro:
            _LOGGER.debug("Moon rises during astronomical night")
            return True
        return False

    async def deep_sky_darkness_moon_sets(self) -> bool:
        """Returns true if moon sets during astronomical night"""
        start_timestamp = None

        # Are we already in darkness?
        if self.astronomical_darkness():
            start_timestamp = self._sun_previous_setting_astro
        else:
            start_timestamp = self._sun_next_setting_astro

        # Did Moon already set in darkness?
        if self.moon_down() and self.astronomical_darkness():
            start_timestamp_moon = self._moon_previous_setting
        else:
            start_timestamp_moon = self._moon_next_setting

        if start_timestamp_moon > start_timestamp and start_timestamp_moon < self._sun_next_rising_astro:
            _LOGGER.debug("Moon sets during astronomical night")
            return True
        return False

    async def deep_sky_darkness_moon_always_up(self) -> bool:
        """Returns true if moon is up during astronomical night"""
        start_timestamp = None

        # Are we already in darkness?
        if self.astronomical_darkness():
            start_timestamp = self._sun_previous_setting_astro
        else:
            start_timestamp = self._sun_next_setting_astro

        if self._moon_next_rising < start_timestamp and self._moon_next_setting > self._sun_next_rising_astro:
            _LOGGER.debug("Moon is up during astronomical night")
            return True
        return False

    async def deep_sky_darkness_moon_always_down(self) -> bool:
        """Returns true if moon is down during astronomical night"""
        start_timestamp = None

        # Are we already in darkness?
        if self.astronomical_darkness():
            start_timestamp = self._sun_previous_setting_astro
        else:
            start_timestamp = self._sun_next_setting_astro

        if self._moon_previous_setting < start_timestamp and self._moon_next_rising > self._sun_next_rising_astro:
            _LOGGER.debug("Moon is down during astronomical night")
            return True
        return False

    async def deep_sky_darkness(self) -> float:
        """Returns the remaining timespan of deep sky darkness"""
        dsd = timedelta(0)

        _LOGGER.debug(f"DSD - Calculating")

        if self.astronomical_darkness():
            _LOGGER.debug(f"DSD - In astronomical darkness")
            if await self.deep_sky_darkness_moon_rises():
                dsd = self._moon_next_rising - self._forecast_time
                _LOGGER.debug(f"DSD - Sun down, Moon rises {dsd}")

            if await self.deep_sky_darkness_moon_sets():
                if self.moon_down():
                    dsd = self._sun_next_rising_astro - self._forecast_time
                    _LOGGER.debug(f"DSD - Sun down, Moon is down {dsd}")
                else:
                    dsd = self._sun_next_rising_astro - self._moon_next_setting
                    _LOGGER.debug(f"DSD - Sun down, Moon sets {dsd}")

            if await self.deep_sky_darkness_moon_always_down():
                dsd = self._sun_next_rising_astro - self._forecast_time
                _LOGGER.debug(f"DSD - Moon always down {dsd}")
            else:
                _LOGGER.debug(f"DSD - Moon NOT always down {dsd}")


        if not self.astronomical_darkness():
            _LOGGER.debug(f"DSD - At sunlight")
            if await self.deep_sky_darkness_moon_rises():
                dsd = self._moon_next_rising - self._sun_next_setting_astro
                _LOGGER.debug(f"DSD - Sun up, Moon rises {dsd}")

            if await self.deep_sky_darkness_moon_sets():
                dsd = self._sun_next_rising_astro - self._moon_next_setting
                _LOGGER.debug(f"DSD - Sun up, Moon sets {dsd}")

            if await self.deep_sky_darkness_moon_always_down():
                dsd = self._sun_next_rising_astro - self._sun_next_setting_astro
                _LOGGER.debug(f"DSD - Sun up, Moon down {dsd}")

        if await self.deep_sky_darkness_moon_always_up():
            dsd = timedelta(0)
            _LOGGER.debug(f"DSD - Moon always up {dsd}")
        else:
            _LOGGER.debug(f"DSD - Moon NOT always up {dsd}")

        return dsd.total_seconds()
