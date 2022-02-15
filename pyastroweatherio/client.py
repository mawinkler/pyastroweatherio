"""Define a client to interact with 7Timer."""
import asyncio
import json
import logging
import time
import ephem
from ephem import AlwaysUpError, NeverUpError
from datetime import datetime, timedelta
from typing import Optional
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from pyastroweatherio.const import (
    BASE_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_CACHE_TIMEOUT,
    DEFAULT_ELEVATION,
    HOME_LATITUDE,
    HOME_LONGITUDE,
    STIMER_OUTPUT,
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
)
from pyastroweatherio.dataclasses import (
    ForecastData,
    LocationData,
    NightlyConditionsData,
)
from pyastroweatherio.errors import RequestError
from pyastroweatherio.helper_functions import ConversionFunctions, AstronomicalRoutines

_LOGGER = logging.getLogger(__name__)


class AstroWeather:
    """AstroWeather Communication Client."""

    def __init__(
        self,
        session: Optional[ClientSession] = None,
        latitude=HOME_LATITUDE,
        longitude=HOME_LONGITUDE,
        elevation=DEFAULT_ELEVATION,
    ):
        self._session: ClientSession = session
        self._latitude = latitude
        self._longitude = longitude
        self._elevation = elevation
        self._weather_data = []
        self._weather_data_init = ""
        self._weather_data_timestamp = datetime.now() - timedelta(
            seconds=(DEFAULT_CACHE_TIMEOUT + 1)
        )
        self.req = session

    # Public functions
    async def get_location_data(
        self,
        time_zone=0,
        hours_to_show=24,
    ) -> None:
        """Returns station Weather Forecast."""
        _LOGGER.debug("get_location_data called")
        return await self._get_location_data()

    # async def get_forecast(self, forecast_type=FORECAST_TYPE_DAILY, hours_to_show=24, time_zone=0) -> None:
    #     """Returns station Weather Forecast."""
    #     _LOGGER.debug("get_forecast called")
    #     return await self._forecast_data(forecast_type, hours_to_show, time_zone)

    async def get_daily_forecast(self) -> None:
        """Returns daily Weather Forecast."""
        return await self._forecast_data(FORECAST_TYPE_DAILY, 72, time_zone=0)

    async def get_hourly_forecast(self) -> None:
        """Returns hourly Weather Forecast."""
        return await self._forecast_data(FORECAST_TYPE_HOURLY, 72, time_zone=0)

    async def get_deepsky_forecast(self) -> None:
        """Returns Deep Sky Forecast."""
        return await self._deepsky_forecast(time_zone=0)

    # Private functions
    async def _get_location_data(self) -> None:
        """Return Forecast data for the Station."""

        # Timezone Offset is currently calculated based on system time
        offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        offset = offset / 60 / 60 * (-1)

        cnv = ConversionFunctions()
        items = []

        _LOGGER.debug("Timezone offset: %s", str(offset))
        await self.retrieve_data()
        now = datetime.now()

        # Anchor timestamp of forecast considering offset
        init_ts = (await cnv.anchor_timestamp(self._weather_data_init)) + timedelta(
            hours=offset
        )

        for row in self._weather_data:
            # Skip over past forecasts
            forecast_time = init_ts + timedelta(hours=row["timepoint"])
            if now > forecast_time:
                continue

            # Astro Routines
            astro_routines = AstronomicalRoutines(
                self._latitude, self._longitude, self._elevation, forecast_time, offset
            )

            item = {
                "init": init_ts,
                "timepoint": row["timepoint"],
                "timestamp": forecast_time,
                "latitude": self._latitude,
                "longitude": self._longitude,
                "elevation": self._elevation,
                "cloudcover": row["cloudcover"],
                "seeing": row["seeing"],
                "transparency": row["transparency"],
                "lifted_index": row["lifted_index"],
                "rh2m": row["rh2m"],
                "wind10m": row["wind10m"],
                "temp2m": row["temp2m"],
                "prec_type": row["prec_type"],
                "sun_next_rising": await astro_routines.sun_next_rising(),
                "sun_next_rising_astro": await astro_routines.sun_next_rising_astro(),
                "sun_next_setting": await astro_routines.sun_next_setting(),
                "sun_next_setting_astro": await astro_routines.sun_next_setting_astro(),
                "moon_next_rising": await astro_routines.moon_next_rising(),
                "moon_next_setting": await astro_routines.moon_next_setting(),
                "moon_phase": await astro_routines.moon_phase(),
                "weather": row.get("weather", ""),
                "deepsky_forecast": await self._deepsky_forecast(time_zone=0),
            }
            items.append(LocationData(item))
            break

        return items

    async def _forecast_data(self, forecast_type, hours_to_show, time_zone) -> None:
        """Return Forecast data for the Station."""

        # Timezone Offset is currently calculated based on system time
        offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        offset = offset / 60 / 60 * (-1)

        cnv = ConversionFunctions()
        items = []

        _LOGGER.debug("Timezone offset: %s", str(offset))
        await self.retrieve_data()
        now = datetime.now()

        # Create items
        cnt = 0

        # Anchor timestamp of forecast considering offset
        init_ts = (await cnv.anchor_timestamp(self._weather_data_init)) + timedelta(
            hours=offset
        )

        _LOGGER.debug("Forecast length: %s", str(len(self._weather_data)))

        for row in self._weather_data:
            # Skip over past forecasts
            forecast_time = init_ts + timedelta(hours=row["timepoint"])
            if now > forecast_time:
                continue

            hour_of_day = forecast_time.hour % 24

            cloudcover = row["cloudcover"]
            seeing = row["seeing"]
            transparency = row["transparency"]

            item = {
                "init": init_ts,
                "timepoint": row["timepoint"],
                "timestamp": forecast_time,
                "hour": hour_of_day,
                "cloudcover": cloudcover,
                "seeing": seeing,
                "transparency": transparency,
                "lifted_index": row["lifted_index"],
                "rh2m": row["rh2m"],
                "wind10m": row["wind10m"],
                "temp2m": row["temp2m"],
                "prec_type": row["prec_type"],
                "weather": row.get("weather", ""),
            }
            items.append(ForecastData(item))
            # Limit number of Hours
            cnt += 3
            if cnt >= hours_to_show:
                break

        return items

    async def _deepsky_forecast(self, time_zone):
        # Timezone Offset is currently calculated based on system time
        offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        offset = offset / 60 / 60 * (-1)

        cnv = ConversionFunctions()
        items = []

        _LOGGER.debug("Timezone offset: %s", str(offset))
        await self.retrieve_data()
        now = datetime.now()

        # Anchor timestamp of forecast considering offset
        init_ts = (await cnv.anchor_timestamp(self._weather_data_init)) + timedelta(
            hours=offset
        )

        # Calc time difference in between init timestamp and 9pm
        # init_night_diff = 21 - init_ts.hour

        # Create forecast
        start_forecast_hour = 0
        start_weather = ""
        interval_points = []
        for row in self._weather_data:
            # Skip over past forecasts
            forecast_time = init_ts + timedelta(hours=row["timepoint"])
            if now > forecast_time:
                continue

            hour_of_day = forecast_time.hour % 24

            # Skip daytime, we're only interested in the forecasts in
            # between 9pm to 3am.
            # Possible timestamps within the data:
            # 15 18 (21 00 03) 06 09 12
            # 16 (19 22 01) 04 07 10 13
            # 17 (20 23 02) 05 08 11 14
            # Relevant ones in brackets
            if hour_of_day < 19 and hour_of_day > 3:
                start_forecast_hour = 0
                start_weather = ""
                interval_points = []
                continue

            cloudcover = row["cloudcover"]
            seeing = row["seeing"]
            transparency = row["transparency"]
            if len(interval_points) == 0:
                start_forecast_hour = hour_of_day
                start_weather = row.get("weather", "")

            # Calculate Condition
            # round( (3*cloudcover + seeing + transparency) / (3*9+8+8) * 5)
            condition = int(
                100 - (3 * cloudcover + seeing + transparency - 5) * 100 / (43 - 5)
            )
            interval_points.append(condition)

            if len(interval_points) == 3:
                item = {
                    "init": init_ts,
                    "hour": start_forecast_hour,
                    "nightly_conditions": interval_points,
                    "weather": start_weather,
                }
                items.append(NightlyConditionsData(item))
                _LOGGER.debug(
                    "Nightly conditions start hour: %s, condition percentages: %s",
                    str(start_forecast_hour),
                    str(interval_points),
                )
            if len(items) == 2:
                break

        return items

    async def retrieve_data(self):

        if (
            (datetime.now() - self._weather_data_timestamp).total_seconds()
        ) > DEFAULT_CACHE_TIMEOUT:
            self._weather_data_timestamp = datetime.now()
            _LOGGER.debug("Updating data")

            # Testing
            # json_data_astro = {"init": "2022020900"}
            # with open("astro.json") as json_file:
            #     astro_dataseries = json.load(json_file)
            # with open("civil.json") as json_file:
            #     civil_dataseries = json.load(json_file)
            # /Testing
            json_data_astro = await self.async_request("astro", "get")
            json_data_civil = await self.async_request("civil", "get")

            astro_dataseries = json_data_astro.get("dataseries")
            civil_dataseries = json_data_civil.get("dataseries")
            # /Testing

            for a, c in zip(astro_dataseries, civil_dataseries):
                if a["timepoint"] == c["timepoint"]:
                    a["weather"] = c["weather"]

            self._weather_data = astro_dataseries
            self._weather_data_init = json_data_astro.get("init")
        else:
            _LOGGER.debug("Using cached data")

    async def async_request(self, product="astro", method="get") -> dict:
        """Make a request against the AstroWeather API."""

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(
                timeout=ClientTimeout(total=DEFAULT_TIMEOUT),
            )

        # BASE_URL = "http://www.7timer.info/bin/api.pl?lon=XX.XXX&lat=YY.YYY&product=astro&output=json"
        # STIMER_OUTPUT = "json"
        url = (
            str(f"{BASE_URL}")
            + "?lon="
            + str(self._longitude)
            + "&lat="
            + str(self._latitude)
            + "&product="
            + str(product)
            + "&output="
            + STIMER_OUTPUT
        )
        try:
            _LOGGER.debug(f"Query url: {url}")
            async with session.request(method, url) as resp:
                resp.raise_for_status()
                plain = str(await resp.text()).replace("\n", " ")
                data = json.loads(plain)
                return data
        except asyncio.TimeoutError:
            raise RequestError("Request to endpoint timed out")
        except ClientError as err:
            raise RequestError(f"Error requesting data: {err}") from None

        finally:
            if not use_running_session:
                await session.close()
