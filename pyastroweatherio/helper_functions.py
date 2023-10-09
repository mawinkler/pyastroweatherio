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
        self._moon_altitude = None
        self._moon_azimuth = None
        self._sun = None
        self._moon = None

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

        try:
            self._sun_next_rising_civil = self.utc_to_local(
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
                        self._sun_observer.next_rising(ephem.Sun(), use_center=True).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_next_setting_civil = self.utc_to_local(
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
                        self._sun_observer.next_setting(ephem.Sun(), use_center=True).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        # Rise and Setting (Nautical)
        self._sun_observer_nautical.date = self.utc_to_local(self._forecast_time)
        self._sun.compute(self._sun_observer_nautical)

        try:
            self._sun_next_rising_nautical = self.utc_to_local(
                self._sun_observer_nautical.next_rising(ephem.Sun(), use_center=True).datetime()
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
                        self._sun_observer_nautical.next_rising(ephem.Sun(), use_center=True).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_next_setting_nautical = self.utc_to_local(
                self._sun_observer_nautical.next_setting(ephem.Sun(), use_center=True).datetime()
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
                        self._sun_observer_nautical.next_setting(ephem.Sun(), use_center=True).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        # Rise and Setting (Astronomical)
        self._sun_observer_astro.date = self.utc_to_local(self._forecast_time)
        self._sun.compute(self._sun_observer_astro)

        try:
            self._sun_next_rising_astro = self.utc_to_local(
                self._sun_observer_astro.next_rising(ephem.Sun(), use_center=True).datetime()
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
                        self._sun_observer_astro.next_rising(ephem.Sun(), use_center=True).datetime()
                    )
                except (ephem.AlwaysUpError, ephem.NeverUpError):
                    continue
                break

        try:
            self._sun_next_setting_astro = self.utc_to_local(
                self._sun_observer_astro.next_setting(ephem.Sun(), use_center=True).datetime()
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
                        self._sun_observer_astro.next_setting(ephem.Sun(), use_center=True).datetime()
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

        # Alt / Az
        self._sun_observer.date = self.utc_to_local(self._forecast_time)
        self._sun.compute(self._sun_observer)

        self._sun_altitude = deg(float(self._sun.alt))
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
            self._moon_next_rising = self.utc_to_local(
                self._moon_observer.next_rising(ephem.Moon(), use_center=True).datetime()
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            pass

        try:
            self._moon_next_setting = self.utc_to_local(
                self._moon_observer.next_setting(ephem.Moon(), use_center=True).datetime()
            )
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            pass

        # Next new Moon
        self._moon_next_new_moon = self.utc_to_local(ephem.next_new_moon(self._forecast_time).datetime())

    def calculate_moon_altaz(self):
        """Calculates moon altitude and azimuth"""
        if self._moon_observer is None:
            self._moon_observer = self.get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()

        # Alt / Az
        self._moon_observer.date = self.utc_to_local(self._forecast_time)
        self._moon.compute(self._moon_observer)

        self._moon_altitude = deg(float(self._moon.alt))
        self._moon_azimuth = deg(float(self._moon.az))

    async def need_update(self):
        self._forecast_time = datetime.utcnow()
        self.calculate_sun_altaz()
        self.calculate_moon_altaz()

        localtime = self.utc_to_local(datetime.utcnow())
        if (
            self._sun_next_setting_civil is None
            or self._sun_next_setting_nautical is None
            or self._sun_next_setting_astro is None
            or self._sun_next_rising_astro is None
            or self._sun_next_rising_nautical is None
            or self._sun_next_rising_civil is None
            or self._moon_next_rising is None
            or self._moon_next_setting is None
            or localtime > self._sun_next_setting_civil
            or localtime > self._sun_next_setting_nautical
            or localtime > self._sun_next_setting_astro
            or localtime > self._sun_next_rising_astro
            or localtime > self._sun_next_rising_nautical
            or localtime > self._sun_next_rising_civil
            or localtime > self._moon_next_rising
            or localtime > self._moon_next_setting
        ):
            _LOGGER.debug("Astronomical calculations updating")
            self.calculate_sun()
            self.calculate_moon()
        # else:
        #     _LOGGER.debug("Astronomical calculations are up to date")
        #     _LOGGER.debug("time %s", str(localtime))
        #     _LOGGER.debug("set  %s, %s, %s", str(self._sun_next_setting_civil), str(self._sun_next_setting_nautical), str(self._sun_next_setting_astro))
        #     _LOGGER.debug("rise %s, %s, %s", str(self._sun_next_rising_astro), str(self._sun_next_rising_nautical), str(self._sun_next_rising_civil))
        #     _LOGGER.debug("moon %s, %s", str(self._moon_next_rising), str(self._moon_next_setting))

    # Return Sun setting and rising
    async def sun_next_rising(self) -> datetime:
        """Returns sun next rising"""
        localtime = self.utc_to_local(datetime.utcnow())
        if (
            self._sun_next_rising_astro is None
            or self._sun_next_rising_nautical is None
            or self._sun_next_rising_civil is None
            or localtime > self._sun_next_rising_astro
            or localtime > self._sun_next_rising_nautical
            or localtime > self._sun_next_rising_civil
        ):
            _LOGGER.debug("Astronomical calculations updating sun_next_rising")
            self._forecast_time = datetime.utcnow()
            self.calculate_sun()

        if self._sun_next_rising_astro is not None:
            return self._sun_next_rising_astro
        if self._sun_next_rising_nautical is not None:
            return self._sun_next_rising_nautical
        if self._sun_next_rising_civil is not None:
            return self._sun_next_rising_civil

    async def sun_next_rising_civil(self) -> datetime:
        """Returns sun next rising"""
        localtime = self.utc_to_local(datetime.utcnow())
        if self._sun_next_setting_civil is None or localtime > self._sun_next_setting_civil:
            _LOGGER.debug("Astronomical calculations updating sun_next_rising_civil")
            self._forecast_time = datetime.utcnow()
            self.calculate_sun()
        else:
            _LOGGER.debug(
                "Astronomical calculations sun_next_rising_civil in %s", str(self._sun_next_setting_civil - localtime)
            )

        self._forecast_time = datetime.utcnow()
        if self._sun_next_rising_civil is not None:
            return self._sun_next_rising_civil

    async def sun_next_rising_nautical(self) -> datetime:
        """Returns sun next nautical rising"""
        localtime = self.utc_to_local(datetime.utcnow())
        if self._sun_next_rising_nautical is None or localtime > self._sun_next_rising_nautical:
            _LOGGER.debug("Astronomical calculations updating sun_next_rising_nautical")
            self._forecast_time = datetime.utcnow()
            self.calculate_sun()
        else:
            _LOGGER.debug(
                "Astronomical calculations sun_next_rising_nautical in %s",
                str(self._sun_next_rising_nautical - localtime),
            )

        if self._sun_next_rising_nautical is not None:
            return self._sun_next_rising_nautical

    async def sun_next_rising_astro(self) -> datetime:
        """Returns sun next astronomical rising"""
        localtime = self.utc_to_local(datetime.utcnow())
        if self._sun_next_rising_astro is None or localtime > self._sun_next_rising_astro:
            _LOGGER.debug("Astronomical calculations updating sun_next_rising_astro")
            self._forecast_time = datetime.utcnow()
            self.calculate_sun()
        else:
            _LOGGER.debug(
                "Astronomical calculations sun_next_rising_astro in %s", str(self._sun_next_rising_astro - localtime)
            )

        if self._sun_next_rising_astro is not None:
            return self._sun_next_rising_astro

    async def sun_next_setting(self) -> datetime:
        """Returns sun next setting"""
        localtime = self.utc_to_local(datetime.utcnow())
        if (
            self._sun_next_setting_civil is None
            or self._sun_next_setting_nautical is None
            or self._sun_next_setting_astro is None
            or localtime > self._sun_next_setting_civil
            or localtime > self._sun_next_setting_nautical
            or localtime > self._sun_next_setting_astro
        ):
            _LOGGER.debug("Astronomical calculations updating sun_next_setting")
            self._forecast_time = datetime.utcnow()
            self.calculate_sun()

        if self._sun_next_setting_astro is not None:
            return self._sun_next_setting_astro
        if self._sun_next_setting_nautical is not None:
            return self._sun_next_setting_nautical
        if self._sun_next_setting_civil is not None:
            return self._sun_next_setting_civil

    async def sun_next_setting_civil(self) -> datetime:
        """Returns sun next setting"""
        localtime = self.utc_to_local(datetime.utcnow())
        if self._sun_next_setting_civil is None or localtime > self._sun_next_setting_civil:
            _LOGGER.debug("Astronomical calculations updating sun_next_setting_civil")
            self._forecast_time = datetime.utcnow()
            self.calculate_sun()
        else:
            _LOGGER.debug(
                "Astronomical calculations sun_next_setting_civil in %s", str(self._sun_next_setting_civil - localtime)
            )

        if self._sun_next_setting_civil is not None:
            return self._sun_next_setting_civil

    async def sun_next_setting_nautical(self) -> datetime:
        """Returns sun next nautical setting"""
        localtime = self.utc_to_local(datetime.utcnow())
        if self._sun_next_setting_nautical is None or localtime > self._sun_next_setting_nautical:
            _LOGGER.debug("Astronomical calculations updating sun_next_setting_nautical")
            self._forecast_time = datetime.utcnow()
            self.calculate_sun()
        else:
            _LOGGER.debug(
                "Astronomical calculations sun_next_setting_nautical in %s",
                str(self._sun_next_setting_nautical - localtime),
            )

        if self._sun_next_setting_nautical is not None:
            return self._sun_next_setting_nautical

    async def sun_next_setting_astro(self) -> datetime:
        """Returns sun next astronomical setting"""
        localtime = self.utc_to_local(datetime.utcnow())
        if self._sun_next_setting_astro is None or localtime > self._sun_next_setting_astro:
            _LOGGER.debug("Astronomical calculations updating sun_next_setting_astro")
            self._forecast_time = datetime.utcnow()
            self.calculate_sun()
        else:
            _LOGGER.debug(
                "Astronomical calculations sun_next_setting_astro in %s", str(self._sun_next_setting_astro - localtime)
            )

        if self._sun_next_setting_astro is not None:
            return self._sun_next_setting_astro

    # Return Moon setting and rising
    async def moon_next_rising(self) -> datetime:
        localtime = self.utc_to_local(datetime.utcnow())
        if self._moon_next_rising is None or localtime > self._moon_next_rising:
            _LOGGER.debug("Astronomical calculations updating moon_next_rising")
            self.calculate_moon()
        else:
            _LOGGER.debug("Astronomical calculations moon_next_rising in %s", str(self._moon_next_rising - localtime))

        """Returns moon next rising"""
        if self._moon_next_rising is not None:
            return self._moon_next_rising

    async def moon_next_setting(self) -> datetime:
        localtime = self.utc_to_local(datetime.utcnow())
        if self._moon_next_setting is None or localtime > self._moon_next_setting:
            _LOGGER.debug("Astronomical calculations updating moon_next_setting")
            self.calculate_moon()
        else:
            _LOGGER.debug("Astronomical calculations moon_next_setting in %s", str(self._moon_next_setting - localtime))

        """Returns moon next setting"""
        if self._moon_next_setting is not None:
            return self._moon_next_setting

    async def moon_phase(self) -> float:
        """Returns the moon phase"""
        self._forecast_time = datetime.utcnow()
        self.calculate_moon()

        if self._moon is not None:
            return self._moon.phase

    async def moon_next_new_moon(self) -> float:
        """Returns the next new moon"""
        localtime = self.utc_to_local(datetime.utcnow())
        if self._moon_next_new_moon is None or localtime > self._moon_next_new_moon:
            _LOGGER.debug("Astronomical calculations updating moon_next_new_moon")
            self.calculate_moon()
        else:
            _LOGGER.debug(
                "Astronomical calculations moon_next_new_moon in %s", str(self._moon_next_new_moon - localtime)
            )

        if self._moon_next_new_moon is not None:
            return self._moon_next_new_moon

    # Return Alt Azimuth of Sun and Moon
    async def sun_altitude(self) -> float:
        """Returns the sun altitude"""
        self._forecast_time = datetime.utcnow()
        self.calculate_sun_altaz()

        if self._sun_altitude is not None:
            return self._sun_altitude

    async def sun_azimuth(self) -> float:
        """Returns the sun azimuth"""
        self._forecast_time = datetime.utcnow()
        self.calculate_sun_altaz()

        if self._sun_azimuth is not None:
            return self._sun_azimuth

    async def moon_altitude(self) -> float:
        """Returns the moon altitude"""
        self._forecast_time = datetime.utcnow()
        self.calculate_moon_altaz()

        if self._moon_altitude is not None:
            return self._moon_altitude

    async def moon_azimuth(self) -> float:
        """Returns the moon azimuth"""
        self._forecast_time = datetime.utcnow()
        self.calculate_moon_altaz()

        if self._moon_azimuth is not None:
            return self._moon_azimuth

    async def night_duration_astronomical(self) -> float:
        """Returns the remaining timespan of astronomical darkness"""

        start_timestamp = None

        # Are we already in darkness?
        if self._sun_next_setting_astro > self._sun_next_rising_astro:
            start_timestamp = self.utc_to_local(datetime.utcnow())
        else:
            start_timestamp = self._sun_next_setting_astro

        astroduration = self._sun_next_rising_astro - start_timestamp

        return astroduration.total_seconds()

    async def deep_sky_darkness_moon_rises(self) -> bool:
        """Returns true if moon rises during astronomical night"""

        if (
            self._moon_next_rising > self._sun_next_setting_astro
            and self._moon_next_rising < self._sun_next_rising_astro
        ):
            return True
        return False

    async def deep_sky_darkness_moon_sets(self) -> bool:
        """Returns true if moon sets during astronomical night"""

        if (
            self._moon_next_setting < self._sun_next_rising_astro
            and self._moon_next_setting > self._sun_next_setting_astro
        ):
            return True
        return False

    async def deep_sky_darkness_moon_always_up(self) -> bool:
        """Returns true if moon is up during astronomical night"""

        if (
            self._moon_next_rising < self._sun_next_setting_astro
            and self._moon_next_setting > self._sun_next_rising_astro
        ):
            return True
        return False

    async def deep_sky_darkness(self) -> float:
        """Returns the remaining timespan of deep sky darkness"""

        start_timestamp = None

        # Are we already in darkness?
        if self._sun_next_setting_astro > self._sun_next_rising_astro:
            start_timestamp = self.utc_to_local(datetime.utcnow())
        else:
            start_timestamp = self._sun_next_setting_astro

        dsd = self._sun_next_rising_astro - start_timestamp

        # Moon rises during darkness
        if (
            self._moon_next_rising > self._sun_next_setting_astro
            and self._moon_next_rising < self._sun_next_rising_astro
        ):
            _LOGGER.debug("Astronomical calculations Moon rises during darkness")
            dsd = dsd - (self._sun_next_rising_astro - self._moon_next_rising)

        # Moon sets during darkness
        if (
            self._moon_next_setting < self._sun_next_rising_astro
            and self._moon_next_setting > self._sun_next_setting_astro
        ):
            _LOGGER.debug("Astronomical calculations Moon sets during darkness")
            dsd = dsd - (self._moon_next_setting - self._sun_next_setting_astro)

        # Moon up during darkness
        if (
            self._moon_next_rising < self._sun_next_setting_astro
            and self._moon_next_setting > self._sun_next_rising_astro
        ):
            _LOGGER.debug("Astronomical calculations Moon up during darkness")
            dsd = timedelta(0)

        return dsd.total_seconds()
