""" Contains Helper functions for AstroWeather."""
from datetime import datetime, timedelta
import logging
import ephem
from ephem import degree, AlwaysUpError, NeverUpError
from pyastroweatherio.const import (
    DEFAULT_ELEVATION,
    HOME_LATITUDE,
    HOME_LONGITUDE,
    ASTRONOMICAL_TWILIGHT,
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
        forecast_time=datetime.now(),
        offset=0,
    ):
        self._latitude = latitude
        self._longitude = longitude
        self._elevation = elevation
        self._forecast_time = forecast_time
        self._offset = offset

        self._sun_observer = None
        self._sun_observer_astro = None
        self._moon_observer = None
        self._sun_next_rising = None
        self._sun_next_setting = None
        self._sun_next_rising_astro = None
        self._sun_next_setting_astro = None
        self._moon_next_rising = None
        self._moon_next_setting = None
        self._moon = None

        self.calculate_sun()
        self.calculate_moon()

    def get_sun_observer(self) -> ephem.Observer:
        """Retrieves the ephem sun observer for the current location"""
        observer = ephem.Observer()
        observer.lon = self._longitude * degree
        observer.lat = self._latitude * degree
        observer.elevation = self._elevation
        observer.horizon = degree
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")
        self._sun_observer = observer

    def get_sun_observer_astro(self) -> ephem.Observer:
        """Retrieves the ephem sun astro observer for the current location"""
        observer = ephem.Observer()
        observer.lon = self._longitude * degree
        observer.lat = self._latitude * degree
        observer.elevation = self._elevation
        observer.horizon = ASTRONOMICAL_TWILIGHT * degree
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")
        self._sun_observer_astro = observer

    def get_moon_observer(self) -> ephem.Observer:
        """Retrieves the ephem mon observer for the current location"""
        observer = ephem.Observer()
        observer.lon = self._longitude * degree
        observer.lat = self._latitude * degree
        observer.elevation = self._elevation
        observer.horizon = 0
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")
        self._moon_observer = observer

    def calculate_sun(self):
        """Calculates sun risings and settings"""
        if self._sun_observer is None:
            self.get_sun_observer()
        if self._sun_observer_astro is None:
            self.get_sun_observer_astro()

        sun = ephem.Sun()

        self._sun_observer.date = self._forecast_time - timedelta(hours=self._offset)
        sun.compute(self._sun_observer)

        try:
            self._sun_next_rising = (
                self._sun_observer.next_rising(ephem.Sun(), use_center=True).datetime()
                + timedelta(hours=self._offset)
            ).strftime("%Y-%m-%d %H:%M:%S")
        except AlwaysUpError:
            self._sun_next_rising = "Always up"
        except NeverUpError:
            self._sun_next_rising = "Always down"

        try:
            self._sun_next_setting = (
                self._sun_observer.next_setting(ephem.Sun(), use_center=True).datetime()
                + timedelta(hours=self._offset)
            ).strftime("%Y-%m-%d %H:%M:%S")
        except AlwaysUpError:
            self._sun_next_setting = "Always up"
        except NeverUpError:
            self._sun_next_setting = "Always down"

        self._sun_observer_astro.date = self._forecast_time - timedelta(
            hours=self._offset
        )
        sun.compute(self._sun_observer_astro)

        try:
            self._sun_next_rising_astro = (
                self._sun_observer_astro.next_rising(
                    ephem.Sun(), use_center=True
                ).datetime()
                + timedelta(hours=self._offset)
            ).strftime("%Y-%m-%d %H:%M:%S")
        except AlwaysUpError:
            self._sun_next_rising_astro = "Always up"
        except NeverUpError:
            self._sun_next_rising_astro = "Always down"

        try:
            self._sun_next_setting_astro = (
                self._sun_observer_astro.next_setting(
                    ephem.Sun(), use_center=True
                ).datetime()
                + timedelta(hours=self._offset)
            ).strftime("%Y-%m-%d %H:%M:%S")
        except AlwaysUpError:
            self._sun_next_setting_astro = "Always up"
        except NeverUpError:
            self._sun_next_setting_astro = "Always down"

    def calculate_moon(self):
        """Calculates moon rising and setting"""
        if self._moon_observer is None:
            self.get_moon_observer()
        if self._moon is None:
            self._moon = ephem.Moon()

        self._moon_observer.date = self._forecast_time - timedelta(hours=self._offset)
        self._moon.compute(self._moon_observer)

        try:
            self._moon_next_rising = (
                self._moon_observer.next_rising(
                    ephem.Moon(), use_center=True
                ).datetime()
                + timedelta(hours=self._offset)
            ).strftime("%Y-%m-%d %H:%M:%S")
        except AlwaysUpError:
            self._moon_next_rising = "Always up"
        except NeverUpError:
            self._moon_next_rising = "Always down"

        try:
            self._moon_next_setting = (
                self._moon_observer.next_setting(
                    ephem.Moon(), use_center=True
                ).datetime()
                + timedelta(hours=self._offset)
            ).strftime("%Y-%m-%d %H:%M:%S")
        except AlwaysUpError:
            self._moon_next_setting = "Always up"
        except NeverUpError:
            self._moon_next_setting = "Always down"

    async def sun_next_rising(self) -> str:
        """Returns sun next rising"""
        return self._sun_next_rising

    async def sun_next_setting(self) -> str:
        """Returns sun next setting"""
        return self._sun_next_setting

    async def sun_next_rising_astro(self) -> str:
        """Returns sun next astronomical rising"""
        return self._sun_next_rising_astro

    async def sun_next_setting_astro(self) -> str:
        """Returns sun next astronomical setting"""
        return self._sun_next_setting_astro

    async def moon_next_rising(self) -> str:
        """Returns moon next rising"""
        return self._moon_next_rising

    async def moon_next_setting(self) -> str:
        """Returns moon next setting"""
        return self._moon_next_setting

    async def moon_phase(self) -> str:
        """Returns the moon phase"""
        return self._moon.phase
