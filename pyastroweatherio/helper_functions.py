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
        return datetime.strptime(value, "%Y%m%d%H")


class AstronomicalRoutines:
    """Calculate different astronomical objects"""

    def __init__(
        self,
        latitude=HOME_LATITUDE,
        longitude=HOME_LONGITUDE,
        elevation=DEFAULT_ELEVATION,
        timezone_info=DEFAULT_TIMEZONE,
        forecast_time=datetime.utcnow(),
    ):
        self._latitude = latitude
        self._longitude = longitude
        self._elevation = elevation
        self._timezone_info = timezone_info
        # tz_find = TimezoneFinder()
        # self._timezone_info = tz_find.timezone_at(lng=longitude, lat=latitude)
        _LOGGER.debug("Timezone: %s", self._timezone_info)
        self._forecast_time = forecast_time

        self._sun_observer = None
        self._sun_observer_nautical = None
        self._sun_observer_astro = None
        self._moon_observer = None
        self._sun_next_rising = None
        self._sun_next_setting = None
        self._sun_next_rising_nautical = None
        self._sun_next_setting_nautical = None
        self._sun_next_rising_astro = None
        self._sun_next_setting_astro = None
        self._sun_altitude = None
        self._sun_azimuth = None
        self._moon_next_rising = None
        self._moon_next_setting = None
        self._moon_altitude = None
        self._moon_azimuth = None
        self._sun = None
        self._moon = None

        self.calculate_sun()
        self.calculate_moon()

    def utc_to_local(self, utc_dt):
        """Localizes the datetime"""
        local_tz = pytz.timezone(self._timezone_info)
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(local_dt)

    def utc_to_local_diff(self):
        """returns the UTC Offset"""
        local = self.utc_to_local(datetime.now())
        return local.utcoffset().seconds // 3600

    def get_sun_observer(self, below_horizon=ASTRONOMICAL_DUSK_DAWN) -> ephem.Observer:
        """Retrieves the ephem sun observer for the current location"""
        observer = ephem.Observer()
        observer.lon = self._longitude * degree
        observer.lat = self._latitude * degree
        observer.elevation = self._elevation
        observer.horizon = below_horizon * degree
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")
        return observer

    def get_moon_observer(self) -> ephem.Observer:
        """Retrieves the ephem mon observer for the current location"""
        observer = ephem.Observer()
        observer.lon = self._longitude * degree
        observer.lat = self._latitude * degree
        observer.elevation = self._elevation
        observer.horizon = 0
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")
        return observer

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

        # Alt / Az
        self._sun_observer.date = self.utc_to_local(self._forecast_time)
        self._sun.compute(self._sun_observer)

        self._sun_altitude = deg(float(self._sun.alt))
        self._sun_azimuth = deg(float(self._sun.az))

        try:
            self._sun_next_rising = self.utc_to_local(
                self._sun_observer.next_rising(ephem.Sun(), use_center=True).datetime()
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
                    self._sun_next_rising_astro = self.utc_to_local(
                        self._sun_observer.next_rising(
                            ephem.Sun(), use_center=True
                        ).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_next_setting = self.utc_to_local(
                self._sun_observer.next_setting(ephem.Sun(), use_center=True).datetime()
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
                    self._sun_next_setting_astro = self.utc_to_local(
                        self._sun_observer.next_setting(
                            ephem.Sun(), use_center=True
                        ).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        # Rise and Setting (Nautical)
        self._sun_observer_nautical.date = self.utc_to_local(self._forecast_time)
        self._sun.compute(self._sun_observer_nautical)

        try:
            self._sun_next_rising_nautical = self.utc_to_local(
                self._sun_observer_nautical.next_rising(
                    ephem.Sun(), use_center=True
                ).datetime()
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
                    self._sun_next_rising_nautical = self.utc_to_local(
                        self._sun_observer_nautical.next_rising(
                            ephem.Sun(), use_center=True
                        ).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_next_setting_nautical = self.utc_to_local(
                self._sun_observer_nautical.next_setting(
                    ephem.Sun(), use_center=True
                ).datetime()
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
                    self._sun_next_setting_nautical = self.utc_to_local(
                        self._sun_observer_nautical.next_setting(
                            ephem.Sun(), use_center=True
                        ).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        # Rise and Setting (Astronomical)
        self._sun_observer_astro.date = self.utc_to_local(self._forecast_time)
        self._sun.compute(self._sun_observer_astro)

        try:
            self._sun_next_rising_astro = self.utc_to_local(
                self._sun_observer_astro.next_rising(
                    ephem.Sun(), use_center=True
                ).datetime()
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
                    self._sun_next_rising_astro = self.utc_to_local(
                        self._sun_observer_astro.next_rising(
                            ephem.Sun(), use_center=True
                        ).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_next_setting_astro = self.utc_to_local(
                self._sun_observer_astro.next_setting(
                    ephem.Sun(), use_center=True
                ).datetime()
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
                    self._sun_next_setting_astro = self.utc_to_local(
                        self._sun_observer_astro.next_setting(
                            ephem.Sun(), use_center=True
                        ).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

    def calculate_moon(self):
        """Calculates moon rising and setting"""
        if self._moon_observer is None:
            self._moon_observer = self.get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()

        # Alt / Az
        self._moon_observer.date = self.utc_to_local(self._forecast_time)
        self._moon.compute(self._moon_observer)

        self._moon_altitude = deg(float(self._moon.alt))
        self._moon_azimuth = deg(float(self._moon.az))

        # Rise and Setting
        self._moon_observer.date = self._forecast_time
        self._moon.compute(self._moon_observer)

        try:
            self._moon_next_rising = self.utc_to_local(
                self._moon_observer.next_rising(
                    ephem.Moon(), use_center=True
                ).datetime()
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            pass

        try:
            self._moon_next_setting = self.utc_to_local(
                self._moon_observer.next_setting(
                    ephem.Moon(), use_center=True
                ).datetime()
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            pass

    async def sun_next_rising(self) -> datetime:
        """Returns sun next rising"""
        if self._sun_next_rising is not None:
            return self._sun_next_rising

    async def sun_next_rising_nautical(self) -> datetime:
        """Returns sun next nautical rising"""
        if self._sun_next_rising_nautical is not None:
            return self._sun_next_rising_nautical

    async def sun_next_rising_astro(self) -> datetime:
        """Returns sun next astronomical rising"""
        if self._sun_next_rising_astro is not None:
            return self._sun_next_rising_astro

    async def sun_next_setting(self) -> datetime:
        """Returns sun next setting"""
        if self._sun_next_setting is not None:
            return self._sun_next_setting

    async def sun_next_setting_nautical(self) -> datetime:
        """Returns sun next nautical setting"""
        if self._sun_next_setting_nautical is not None:
            return self._sun_next_setting_nautical

    async def sun_next_setting_astro(self) -> datetime:
        """Returns sun next astronomical setting"""
        if self._sun_next_setting_astro is not None:
            return self._sun_next_setting_astro

    async def sun_altitude(self) -> float:
        """Returns the sun altitude"""
        if self._sun_altitude is not None:
            return self._sun_altitude

    async def sun_azimuth(self) -> float:
        """Returns the sun azimuth"""
        if self._sun_azimuth is not None:
            return self._sun_azimuth

    async def moon_next_rising(self) -> datetime:
        """Returns moon next rising"""
        if self._moon_next_rising is not None:
            return self._moon_next_rising

    async def moon_next_setting(self) -> datetime:
        """Returns moon next setting"""
        if self._moon_next_setting is not None:
            return self._moon_next_setting

    async def moon_phase(self) -> float:
        """Returns the moon phase"""
        return self._moon.phase

    async def moon_altitude(self) -> float:
        """Returns the moon altitude"""
        if self._moon_altitude is not None:
            return self._moon_altitude

    async def moon_azimuth(self) -> float:
        """Returns the moon azimuth"""
        if self._moon_azimuth is not None:
            return self._moon_azimuth
