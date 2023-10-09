"""Define a client to interact with 7Timer."""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from pyastroweatherio.const import (
    BASE_URL_SEVENTIMER,
    BASE_URL_MET,
    DEFAULT_TIMEOUT,
    DEFAULT_CACHE_TIMEOUT,
    DEFAULT_ELEVATION,
    DEFAULT_TIMEZONE,
    DEFAULT_CONDITION_CLOUDCOVER_WEIGHT,
    DEFAULT_CONDITION_SEEING_WEIGHT,
    DEFAULT_CONDITION_TRANSPARENCY_WEIGHT,
    HOME_LATITUDE,
    HOME_LONGITUDE,
    STIMER_OUTPUT,
    # FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
    MAGNUS_COEFFICIENT_A,
    MAGNUS_COEFFICIENT_B,
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
        timezone_info=DEFAULT_TIMEZONE,
        cloudcover_weight=DEFAULT_CONDITION_CLOUDCOVER_WEIGHT,
        seeing_weight=DEFAULT_CONDITION_SEEING_WEIGHT,
        transparency_weight=DEFAULT_CONDITION_TRANSPARENCY_WEIGHT,
    ):
        self._session: ClientSession = session
        self._latitude = latitude
        self._longitude = longitude
        self._elevation = elevation
        self._timezone_info = timezone_info
        self._weather_data_seventimer = []
        self._weather_data_seventimer_init = ""
        self._weather_data_metno = []
        self._weather_data_metno_init = ""
        self._weather_data_seventimer_timestamp = datetime.now() - timedelta(seconds=(DEFAULT_CACHE_TIMEOUT + 1))
        self._weather_data_metno_timestamp = datetime.now() - timedelta(seconds=(DEFAULT_CACHE_TIMEOUT + 1))
        self._cloudcover_weight = cloudcover_weight
        self._seeing_weight = seeing_weight
        self._transparency_weight = transparency_weight

        self._forecast_data = None

        self.req = session

        # Astro Routines
        self._astro_routines = AstronomicalRoutines(
            self._latitude, self._longitude, self._elevation, self._timezone_info
        )

        # Testing
        self.test_mode = False
        self.dump_json = False

    # Public functions
    async def get_location_data(
        self,
    ) -> None:
        """Returns station Weather Forecast."""
        return await self._get_location_data()

    # async def get_forecast(self, forecast_type=FORECAST_TYPE_DAILY, hours_to_show=24) -> None:
    #     """Returns station Weather Forecast."""
    #     _LOGGER.debug("get_forecast called")
    #     return await self._get_forecast_data(forecast_type, hours_to_show)

    # async def get_daily_forecast(self) -> None:
    #     """Returns daily Weather Forecast."""
    #     return await self._get_forecast_data(FORECAST_TYPE_DAILY, 72)

    async def get_hourly_forecast(self) -> None:
        """Returns hourly Weather Forecast."""
        return await self._get_forecast_data(FORECAST_TYPE_HOURLY, 72)

    async def get_deepsky_forecast(self) -> None:
        """Returns Deep Sky Forecast."""
        return await self._get_deepsky_forecast()

    # Private functions
    async def _get_location_data(self) -> None:
        """Return Forecast data"""

        cnv = ConversionFunctions()
        items = []

        await self.retrieve_data_seventimer()
        await self.retrieve_data_metno()
        now = datetime.utcnow()

        # Anchor timestamp
        init_ts = await cnv.anchor_timestamp(self._weather_data_seventimer_init)

        await self._astro_routines.need_update()

        # Met.no
        metno_index = -1
        forecast_skipped = 0
        for row in self._weather_data_seventimer:
            # 7Timer: Skip over past forecasts
            forecast_time = init_ts + timedelta(hours=row["timepoint"])
            if now > forecast_time:
                forecast_skipped += 1
                continue

            _LOGGER.debug("7Timer forecast time: %s", str(forecast_time))

            # Met.no: Search for 7Timer forecast time
            for datapoint in self._weather_data_metno:
                metno_index += 1
                if forecast_time == datetime.strptime(datapoint.get("time"), "%Y-%m-%dT%H:%M:%SZ"):
                    break
            _LOGGER.debug("Met.no start index: %s", str(metno_index))

            item = {
                "init": init_ts,
                "timepoint": row["timepoint"],
                "timestamp": forecast_time,
                "forecast_length": (len(self._weather_data_seventimer) - forecast_skipped) * 3,
                "latitude": self._latitude,
                "longitude": self._longitude,
                "elevation": self._elevation,
                "seeing": row["seeing"],
                "transparency": row["transparency"],
                "lifted_index": row["lifted_index"],
                "sun_next_rising": await self._astro_routines.sun_next_rising_civil(),
                "sun_next_rising_nautical": await self._astro_routines.sun_next_rising_nautical(),
                "sun_next_rising_astro": await self._astro_routines.sun_next_rising_astro(),
                "sun_next_setting": await self._astro_routines.sun_next_setting_civil(),
                "sun_next_setting_nautical": await self._astro_routines.sun_next_setting_nautical(),
                "sun_next_setting_astro": await self._astro_routines.sun_next_setting_astro(),
                "sun_altitude": await self._astro_routines.sun_altitude(),
                "sun_azimuth": await self._astro_routines.sun_azimuth(),
                "moon_next_rising": await self._astro_routines.moon_next_rising(),
                "moon_next_setting": await self._astro_routines.moon_next_setting(),
                "moon_phase": await self._astro_routines.moon_phase(),
                "moon_next_new_moon": await self._astro_routines.moon_next_new_moon(),
                "moon_altitude": await self._astro_routines.moon_altitude(),
                "moon_azimuth": await self._astro_routines.moon_azimuth(),
                "night_duration_astronomical": await self._astro_routines.night_duration_astronomical(),
                "deep_sky_darkness_moon_rises": await self._astro_routines.deep_sky_darkness_moon_rises(),
                "deep_sky_darkness_moon_sets": await self._astro_routines.deep_sky_darkness_moon_sets(),
                "deep_sky_darkness_moon_always_up": await self._astro_routines.deep_sky_darkness_moon_always_up(),
                "deep_sky_darkness": await self._astro_routines.deep_sky_darkness(),
                "deepsky_forecast": await self._get_deepsky_forecast(),
            }
            # Met.no
            if (
                datetime.strptime(
                    self._weather_data_metno[metno_index].get("time"),
                    "%Y-%m-%dT%H:%M:%SZ",
                )
                == forecast_time
            ):
                # _LOGGER.debug("Met.no Cloud Area Fraction timestamp match: %s", str(forecast_time))
                details = self._weather_data_metno[metno_index].get("data", {}).get("instant", {}).get("details", {})
                item["cloudcover"] = int(details.get("cloud_area_fraction", -1) / 12.5 + 1)

                item["cloud_area_fraction"] = details.get("cloud_area_fraction", -1)
                item["cloud_area_fraction_high"] = details.get("cloud_area_fraction_high", -1)
                item["cloud_area_fraction_low"] = details.get("cloud_area_fraction_low", -1)
                item["cloud_area_fraction_medium"] = details.get("cloud_area_fraction_medium", -1)
                item["fog_area_fraction"] = details.get("fog_area_fraction", -1)

                item["condition_percentage"] = await self.calc_condition_percentage(
                    item["cloud_area_fraction"] / 12.5 + 1,
                    row["seeing"],
                    row["transparency"],
                )

                item["rh2m"] = details.get("relative_humidity", -1)
                item["wind_speed"] = details.get("wind_speed", -1)
                item["wind_from_direction"] = details.get("wind_from_direction", -1)
                item["temp2m"] = details.get("air_temperature", -1)
                item["dewpoint2m"] = details.get("dew_point_temperature", -1)
                item["weather"] = (
                    self._weather_data_metno[metno_index]
                    .get("data", {})
                    .get("next_1_hours", {})
                    .get("summary", {})
                    .get("symbol_code", "")
                )
                item["weather6"] = (
                    self._weather_data_metno[metno_index]
                    .get("data", {})
                    .get("next_6_hours", {})
                    .get("summary", {})
                    .get("symbol_code", "")
                )
                item["precipitation_amount"] = (
                    self._weather_data_metno[metno_index]
                    .get("data", {})
                    .get("next_1_hours", {})
                    .get("details", {})
                    .get("precipitation_amount", "")
                )

            else:
                break

            items.append(LocationData(item))
            break

        return items

    async def _get_forecast_data(self, forecast_type, hours_to_show) -> None:
        """Return Forecast data for the Station."""

        cnv = ConversionFunctions()
        items = []

        await self.retrieve_data_seventimer()
        await self.retrieve_data_metno()
        now = datetime.utcnow()

        # Create items
        cnt = 0

        # Anchor timestamp
        init_ts = await cnv.anchor_timestamp(self._weather_data_seventimer_init)

        utc_to_local_diff = self._astro_routines.utc_to_local_diff()
        _LOGGER.debug("UTC to local diff: %s", str(utc_to_local_diff))
        _LOGGER.debug("Forecast length: %s", str(len(self._weather_data_seventimer)))

        # Met.no
        metno_index = -1
        for row in self._weather_data_seventimer:
            # 7Timer: Skip over past forecasts
            forecast_time = init_ts + timedelta(hours=row["timepoint"])
            if now > forecast_time:
                continue

            # Met.no: Search for 7Timer forecast time
            if metno_index == -1:
                for datapoint in self._weather_data_metno:
                    metno_index += 1
                    if forecast_time == datetime.strptime(datapoint.get("time"), "%Y-%m-%dT%H:%M:%SZ"):
                        break
                _LOGGER.debug("Met.no start index: %s", str(metno_index))

            # Hour of day needs to be in local time
            hour_of_day = (forecast_time.hour + utc_to_local_diff) % 24

            cloudcover = row["cloudcover"]
            seeing = row["seeing"]
            transparency = row["transparency"]

            item = {
                "init": init_ts,
                "timepoint": row["timepoint"],
                "timestamp": forecast_time,
                "hour": hour_of_day,
                "seeing": seeing,
                "transparency": transparency,
                "lifted_index": row["lifted_index"],
            }
            # Met.no
            if (
                datetime.strptime(
                    self._weather_data_metno[metno_index + cnt].get("time"),
                    "%Y-%m-%dT%H:%M:%SZ",
                )
                == forecast_time
            ):
                # _LOGGER.debug("Met.no Cloud Area Fraction timestamp match: %s", str(forecast_time))
                # Continue hourly
                for i in range(0, 3):
                    details = (
                        self._weather_data_metno[metno_index + cnt + i]
                        .get("data", {})
                        .get("instant", {})
                        .get("details", {})
                    )
                    # Overwrite cloudcover
                    if details.get("cloud_area_fraction") is None:
                        break
                    item["cloudcover"] = int(details.get("cloud_area_fraction", -1) / 12.5 + 1)

                    item["cloud_area_fraction"] = details.get("cloud_area_fraction", -1)
                    item["cloud_area_fraction_high"] = details.get("cloud_area_fraction_high", -1)
                    item["cloud_area_fraction_low"] = details.get("cloud_area_fraction_low", -1)
                    item["cloud_area_fraction_medium"] = details.get("cloud_area_fraction_medium", -1)
                    item["fog_area_fraction"] = details.get("fog_area_fraction", -1)

                    item["condition_percentage"] = await self.calc_condition_percentage(
                        item["cloud_area_fraction"] / 12.5 + 1,
                        row["seeing"],
                        row["transparency"],
                    )
                    item["rh2m"] = details.get("relative_humidity", -1)
                    item["wind_speed"] = details.get("wind_speed", -1)
                    item["wind_from_direction"] = details.get("wind_from_direction", -1)
                    item["temp2m"] = details.get("air_temperature", -1)
                    item["dewpoint2m"] = details.get("dew_point_temperature", -1)
                    if self._weather_data_metno[metno_index + cnt + i].get("data", {}).get("next_1_hours", {}) == {}:
                        # No more hourly data
                        break
                    if self._weather_data_metno[metno_index + cnt + i].get("data", {}).get("next_6_hours", {}) == {}:
                        # No more 6-hourly data
                        break
                    item["weather"] = (
                        self._weather_data_metno[metno_index + cnt + i]
                        .get("data", {})
                        .get("next_1_hours", {})
                        .get("summary", {})
                        .get("symbol_code", "")
                    )
                    item["weather6"] = (
                        self._weather_data_metno[metno_index + cnt + i]
                        .get("data", {})
                        .get("next_6_hours", {})
                        .get("summary", {})
                        .get("symbol_code", "")
                    )
                    item["precipitation_amount"] = (
                        self._weather_data_metno[metno_index + cnt + i]
                        .get("data", {})
                        .get("next_1_hours", {})
                        .get("details", {})
                        .get("precipitation_amount", "")
                    )

                    items.append(ForecastData(item))

                    item["timepoint"] = item["timepoint"] + 1
                    item["timestamp"] = item["timestamp"] + timedelta(hours=1)
                    item["hour"] = item["hour"] + 1
            else:
                break

            # Limit number of Hours
            cnt += 3
            if cnt >= hours_to_show:
                break

        self._forecast_data = items

        return items

    async def _get_deepsky_forecast(self):
        """Return Deepsky Forecast data"""

        cnv = ConversionFunctions()
        items = []

        if self._forecast_data == None:
            await self._get_forecast_data(FORECAST_TYPE_HOURLY, 72)
        now = datetime.utcnow()

        # Anchor timestamp
        init_ts = await cnv.anchor_timestamp(self._weather_data_seventimer_init)

        utc_to_local_diff = self._astro_routines.utc_to_local_diff()

        # Create forecast
        forecast_dayname = ""
        start_forecast_hour = 0
        start_weather = ""
        interval_points = []

        sun_next_setting = await self._astro_routines.sun_next_setting()
        sun_next_rising = await self._astro_routines.sun_next_rising()

        _LOGGER.debug(
            "sun_next_setting: %s, sun_next_rising: %s",
            str(sun_next_setting),
            str(sun_next_rising),
        )
        for row in self._forecast_data:
            # Hour of day needs to be in local time
            hour_of_day = (row.timestamp.hour + utc_to_local_diff) % 24

            # Skip daytime, we're only interested in the forecasts at
            # darkness.
            if hour_of_day < sun_next_setting.hour and hour_of_day > sun_next_rising.hour:
                start_forecast_hour = 0
                start_weather = ""
                interval_points = []
                continue
            # cloudcover = row.cloudcover
            seeing = row.seeing
            transparency = row.transparency
            cloud_area_fraction = 0

            # Met.no
            cloud_area_fraction = row.cloud_area_fraction_percentage / 12.5 + 1

            if len(interval_points) == 0:
                forecast_dayname = row.timestamp.strftime("%A")
                start_forecast_hour = hour_of_day
                start_weather = row.weather6

            # Calculate Condition
            interval_points.append(await self.calc_condition_percentage(cloud_area_fraction, seeing, transparency))

            if hour_of_day == sun_next_rising.hour:
                item = {
                    "init": init_ts,
                    "dayname": forecast_dayname,
                    "hour": start_forecast_hour,
                    "nightly_conditions": interval_points,
                    "weather": start_weather,
                }
                items.append(NightlyConditionsData(item))

                conditions_numeric = ""
                for condition in interval_points:
                    conditions_numeric += str(condition) + ", "
                _LOGGER.debug(
                    "Nightly conditions day: %s, start hour: %s, nightly conditions: %s, weather: %s, conditions numeric: %s",
                    str(forecast_dayname),
                    str(start_forecast_hour),
                    str(len(interval_points)),
                    str(start_weather),
                    conditions_numeric,
                )

            # Forecast for two nights only
            if len(items) == 2:
                break

        return items

    async def calc_condition_percentage(self, cloudcover, seeing, transparency):
        """Return condition based on cloud cover, seeing and transparency"""
        # Possible Values:
        #   Clouds: 1-9
        #   Seeing: 1-8
        #   Transparency: 1-8
        condition = int(
            100
            - (
                self._cloudcover_weight * cloudcover
                + self._seeing_weight * seeing
                + self._transparency_weight * transparency
                - self._cloudcover_weight
                - self._seeing_weight
                - self._transparency_weight
            )
            * 100
            / (
                self._cloudcover_weight * 9
                + self._seeing_weight * 8
                + self._transparency_weight * 8
                - self._cloudcover_weight
                - self._seeing_weight
                - self._transparency_weight
            )
        )
        # _LOGGER.debug(
        #     "Calc condition cloudcover: %d(%d), seeing %d(%d), transparency: %d(%d), condition %d",
        #     cloudcover,
        #     self._cloudcover_weight,
        #     seeing,
        #     self._seeing_weight,
        #     transparency,
        #     self._transparency_weight,
        #     condition,
        # )
        return condition

    async def calc_dewpoint2m(self, rh2m, temp2m):
        """Calculate 2m Dew Point."""
        # α(T,RH) = ln(RH/100) + aT/(b+T)
        # Ts = (b × α(T,RH)) / (a - α(T,RH))
        alpha = float(Decimal(str(rh2m / 100)).ln()) + MAGNUS_COEFFICIENT_A * temp2m / (MAGNUS_COEFFICIENT_B + temp2m)
        dewpoint = (MAGNUS_COEFFICIENT_B * alpha) / (MAGNUS_COEFFICIENT_A - alpha)

        return dewpoint

    async def retrieve_data_seventimer(self):
        """Retrieves current data from 7timer"""

        if ((datetime.now() - self._weather_data_seventimer_timestamp).total_seconds()) > DEFAULT_CACHE_TIMEOUT:
            self._weather_data_seventimer_timestamp = datetime.now()
            _LOGGER.debug("Updating data from 7Timer")

            astro_dataseries = None
            # civil_dataseries = None

            # Testing
            if self.test_mode:
                with open("astro.json") as json_file:
                    astro_dataseries_json = json.load(json_file)
                    astro_dataseries = astro_dataseries_json.get("dataseries", {})
                    json_data_astro = {"init": astro_dataseries_json.get("init")}
                # with open("civil.json") as json_file:
                #     civil_dataseries = json.load(json_file).get("dataseries", {})
            else:
                json_data_astro = await self.async_request_seventimer("astro", "get")
                astro_dataseries = json_data_astro.get("dataseries", {})

            self._weather_data_seventimer = astro_dataseries
            self._weather_data_seventimer_init = json_data_astro.get("init")
        else:
            _LOGGER.debug("Using cached data for 7Timer")

    async def async_request_seventimer(self, product="astro", method="get") -> dict:
        """Make a request against the 7timer API."""

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(
                timeout=ClientTimeout(total=DEFAULT_TIMEOUT),
            )

        # BASE_URL_SEVENTIMER = "https://www.7timer.info/bin/api.pl?lon=XX.XX&lat=YY.YY&product=astro&output=json"
        # STIMER_OUTPUT = "json"
        url = (
            str(f"{BASE_URL_SEVENTIMER}")
            + "?lon="
            + str("%.1f" % round(self._longitude, 2))
            + "&lat="
            + str("%.1f" % round(self._latitude, 2))
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

                if self.dump_json:
                    json_string = json.dumps(data)
                    with open(product + ".json", "w") as outfile:
                        outfile.write(json_string)

                return data
        except asyncio.TimeoutError as tex:
            raise RequestError(f"Request to endpoint timed out: {tex}") from None
        except ClientError as err:
            raise RequestError(f"Error requesting data: {err}") from None

        finally:
            if not use_running_session:
                await session.close()

    async def retrieve_data_metno(self):
        """Retrieves current data from met"""

        if ((datetime.now() - self._weather_data_metno_timestamp).total_seconds()) > DEFAULT_CACHE_TIMEOUT:
            self._weather_data_metno_timestamp = datetime.now()
            _LOGGER.debug("Updating data from Met.no")

            dataseries = None

            # Testing
            if self.test_mode:
                with open("met.json") as json_file:
                    dataseries = json.load(json_file).get("properties", {}).get("timeseries", [])
            else:
                json_data_metno = await self.async_request_met("met", "get")

                dataseries = json_data_metno.get("properties", {}).get("timeseries", [])

            self._weather_data_metno = dataseries
            self._weather_data_metno_init = dataseries[0].get("time", None)
        else:
            _LOGGER.debug("Using cached data for Met.no")

    async def async_request_met(self, product="met", method="get") -> dict:
        """Make a request against the 7timer API."""

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(
                timeout=ClientTimeout(total=DEFAULT_TIMEOUT),
            )

        # BASE_URL_MET = "https://api.met.no/weatherapi/locationforecast/2.0/complete?altitude=XX&lat=XX.XX&lon=XX.XX"
        url = (
            str(f"{BASE_URL_MET}")
            + "?lon="
            + str("%.1f" % round(self._longitude, 2))
            + "&lat="
            + str("%.1f" % round(self._latitude, 2))
            + "&altitude="
            + str(self._elevation)
        )
        try:
            _LOGGER.debug(f"Query url: {url}")
            async with session.request(method, url) as resp:
                resp.raise_for_status()
                # plain = str(await resp.text()).replace("\n", " ")
                # data = json.loads(plain)
                data = await resp.json()

                if self.dump_json:
                    json_string = json.dumps(data)
                    with open(product + ".json", "w") as outfile:
                        outfile.write(json_string)

                return data
        except asyncio.TimeoutError as tex:
            raise RequestError(f"Request to endpoint timed out: {tex}") from None
        except ClientError as err:
            raise RequestError(f"Error requesting data: {err}") from None

        finally:
            if not use_running_session:
                await session.close()
