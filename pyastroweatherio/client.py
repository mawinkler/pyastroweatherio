"""Define a client to interact with 7Timer."""
import asyncio
import json
import logging
import time
from datetime import datetime
from datetime import timedelta
from typing import Optional

from aiohttp import ClientSession
from aiohttp import ClientTimeout
from aiohttp.client_exceptions import ClientError

from pyastroweatherio.const import BASE_URL
from pyastroweatherio.const import CONDITION
from pyastroweatherio.const import DEEP_SKY_THRESHOLD
from pyastroweatherio.const import DEFAULT_TIMEOUT
from pyastroweatherio.const import HOME_LATITUDE
from pyastroweatherio.const import HOME_LONGITUDE
from pyastroweatherio.const import STIMER_OUTPUT
from pyastroweatherio.const import STIMER_PRODUCT
from pyastroweatherio.dataclasses import ForecastData
from pyastroweatherio.errors import RequestError
from pyastroweatherio.errors import ResultError
from pyastroweatherio.helper_functions import ConversionFunctions

_LOGGER = logging.getLogger(__name__)


class AstroWeather:
    """AstroWeather Communication Client."""

    def __init__(
        self,
        session: Optional[ClientSession] = None,
        latitude=HOME_LATITUDE,
        longitude=HOME_LONGITUDE,
    ):
        self._session: ClientSession = session
        self._latitude = latitude
        self._longitude = longitude
        self.req = session

    async def get_forecast(
        self,
        time_zone=0,
        hours_to_show=24,
    ) -> None:
        """Returns station Weather Forecast."""
        return await self._forecast_data(time_zone, hours_to_show)

    async def _forecast_data(
        self,
        time_zone,
        hours_to_show,
    ) -> None:
        """Return Forecast data for the Station."""

        latitude = self._latitude
        longitude = self._longitude

        # Timezone Offset is currently calculated based on system time
        offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        offset = offset / 60 / 60 * (-1)

        cnv = ConversionFunctions()
        json_data = await self.async_request(latitude, longitude, "get")
        items = []

        _LOGGER.debug("TIMEZONE OFFSET: " + str(offset))
        # We need a few Items from the Current Conditions section
        product = json_data.get("product")
        init = json_data.get("init")

        now = datetime.now()
        forecast = json_data.get("dataseries")

        # Create items
        cnt = 0

        # Anchor timestamp of forecast considering offset
        init_ts = (await cnv.anchor_timestamp(init)) + timedelta(hours=offset)

        # Calc time difference in between init timestamp and 9pm
        init_night_diff = 21 - init_ts.hour
        _LOGGER.debug("\n" + "INIT NIGHT DIFF: " + str(init_night_diff))

        for row in forecast:
            # Skip over past forecasts
            forecast_time = init_ts + timedelta(hours=row["timepoint"])
            if now > forecast_time:
                continue

            item = {
                "product": product,
                "init": init_ts,
                "timepoint": row["timepoint"],
                "latitude": latitude,
                "longitude": longitude,
                "cloudcover": row["cloudcover"],
                "seeing": row["seeing"],
                "transparency": row["transparency"],
                "lifted_index": row["lifted_index"],
                "rh2m": row["rh2m"],
                "wind10m": row["wind10m"],
                "temp2m": row["temp2m"],
                "prec_type": row["prec_type"],
                "forecast": await self.deepsky_forecast(
                    forecast,
                    now,
                    init_ts,
                    row["timepoint"],
                ),
            }
            items.append(ForecastData(item))
            # Limit number of Hours
            cnt += 1
            if cnt >= hours_to_show:
                break

        return items

    async def deepsky_forecast(self, forecast, now, init_ts, timepoint):

        dsforecast = []

        # Create forecast
        for row in forecast:
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
            if hour_of_day > 3 and hour_of_day < 19:
                continue

            cloudcover = row["cloudcover"]
            seeing = row["seeing"]
            transparency = row["transparency"]

            # Calculate Condition
            # round( (3*cloudcover + seeing + transparency) / (3*9+8+8) * 5)
            condition = round(
                (3 * cloudcover + seeing + transparency) / 43 * 5,
            )

            forecast_item = {
                "hour": hour_of_day,
                "cloudcover": cloudcover,
                "seeing": seeing,
                "transparency": transparency,
                "condition": condition,
            }
            dsforecast.append(forecast_item)

        return dsforecast

    async def async_request(self, latitude, longitude, method: str) -> dict:
        """Make a request against the AstroWeather API."""

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(
                timeout=ClientTimeout(total=DEFAULT_TIMEOUT),
            )

        # BASE_URL = "http://www.7timer.info/bin/api.pl?lon=XX.XXX&lat=YY.YYY&product=astro&output=json"
        # STIMER_PRODUCT = "astro"
        # STIMER_OUTPUT = "json"

        url = (
            str(f"{BASE_URL}")
            + "?lon="
            + str(longitude)
            + "&lat="
            + str(latitude)
            + "&product="
            + STIMER_PRODUCT
            + "&output="
            + STIMER_OUTPUT
        )
        try:
            _LOGGER.debug("\n" + "QUERY URL: " + url)
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
