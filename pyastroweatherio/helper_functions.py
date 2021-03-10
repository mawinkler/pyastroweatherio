""" Contains Helper functions for AstroWeather."""
import asyncio
import logging
from datetime import datetime
import ephem
from ephem import degree

_LOGGER = logging.getLogger(__name__)
ASTRONOMICAL_TWILIGHT = -18


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

    async def get_sun_observer(self, lat, lon, elevation) -> ephem.Observer:
        # async def set_observer(self, lat, lon):
        """Returns the ephem observer for the current location"""
        observer = ephem.Observer()
        observer.lon = lon * degree
        observer.lat = lat * degree
        observer.elevation = elevation
        observer.horizon = ASTRONOMICAL_TWILIGHT * degree
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")
        return observer

    async def get_moon_observer(self, lat, lon, elevation) -> ephem.Observer:
        # async def set_observer(self, lat, lon):
        """Returns the ephem observer for the current location"""
        observer = ephem.Observer()
        observer.lon = lon * degree
        observer.lat = lat * degree
        observer.elevation = elevation
        observer.horizon = 0
        observer.pressure = 0
        observer.epoch = datetime.now().strftime("%Y/%m/%d")
        return observer
