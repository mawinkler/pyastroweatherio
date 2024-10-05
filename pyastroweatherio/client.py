"""Define a client to interact with 7Timer."""

import asyncio
from datetime import UTC, datetime, timedelta
import json
from json.decoder import JSONDecodeError
import logging
import math
import os.path
from typing import Optional

import aiofiles
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from pyastroweatherio.const import (
    BASE_URL_MET,
    BASE_URL_SEVENTIMER,
    DEFAULT_CACHE_TIMEOUT,
    DEFAULT_CONDITION_CALM_WEIGHT,
    DEFAULT_CONDITION_CLOUDCOVER_HIGH_WEAKENING,
    DEFAULT_CONDITION_CLOUDCOVER_LOW_WEAKENING,
    DEFAULT_CONDITION_CLOUDCOVER_MEDIUM_WEAKENING,
    DEFAULT_CONDITION_CLOUDCOVER_WEIGHT,
    DEFAULT_CONDITION_SEEING_WEIGHT,
    DEFAULT_CONDITION_TRANSPARENCY_WEIGHT,
    DEFAULT_ELEVATION,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_TIMEOUT,
    DEFAULT_TIMEZONE,
    FORECAST_TYPE_HOURLY,
    HEADERS,
    MAG_DEGRATION_MAX,
    SEEING,
    SEEING_MAX,
    TRANSPARENCY,
    WIND10M_MAX,
)
from pyastroweatherio.dataclasses import (
    DSOUpTonight,
    BODIESUpTonight,
    COMETSUpTonight,
    ForecastData,
    LocationData,
    NightlyConditionsData,
)
from pyastroweatherio.errors import RequestError
from pyastroweatherio.helper_functions import (
    AstronomicalRoutines,
    AtmosphericRoutines,
    ConversionFunctions,
)

_LOGGER = logging.getLogger(__name__)
_NOT_AVAILABLE = -9999


class AstroWeather:
    """AstroWeather Communication Client."""

    def __init__(
        self,
        session: Optional[ClientSession] = None,
        latitude=DEFAULT_LATITUDE,
        longitude=DEFAULT_LONGITUDE,
        elevation=DEFAULT_ELEVATION,
        timezone_info=DEFAULT_TIMEZONE,
        cloudcover_weight=DEFAULT_CONDITION_CLOUDCOVER_WEIGHT,
        cloudcover_high_weakening=DEFAULT_CONDITION_CLOUDCOVER_HIGH_WEAKENING,
        cloudcover_medium_weakening=DEFAULT_CONDITION_CLOUDCOVER_MEDIUM_WEAKENING,
        cloudcover_low_weakening=DEFAULT_CONDITION_CLOUDCOVER_LOW_WEAKENING,
        seeing_weight=DEFAULT_CONDITION_SEEING_WEIGHT,
        transparency_weight=DEFAULT_CONDITION_TRANSPARENCY_WEIGHT,
        calm_weight=DEFAULT_CONDITION_CALM_WEIGHT,
        uptonight_path="/conf/www",
        test_datetime=None,
        experimental_features=False,
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
        self._weather_data_uptonight = {}
        self._weather_data_uptonight_bodies = {}
        self._weather_data_uptonight_comets = {}
        self._weather_data_seventimer_timestamp = datetime.now() - timedelta(
            seconds=(DEFAULT_CACHE_TIMEOUT + 1)
        )
        self._weather_data_metno_timestamp = datetime.now() - timedelta(
            seconds=(DEFAULT_CACHE_TIMEOUT + 1)
        )
        self._data_uptonight_timestamp = datetime.now() - timedelta(
            seconds=(DEFAULT_CACHE_TIMEOUT + 1)
        )
        self._cloudcover_weight = cloudcover_weight
        self._cloudcover_high_weakening = cloudcover_high_weakening
        self._cloudcover_medium_weakening = cloudcover_medium_weakening
        self._cloudcover_low_weakening = cloudcover_low_weakening
        self._seeing_weight = seeing_weight
        self._transparency_weight = transparency_weight
        self._calm_weight = calm_weight
        self._uptonight_path = uptonight_path
        self._test_datetime = test_datetime
        self._experimental_features = experimental_features

        self._forecast_data = None

        self.req = session

        # Astro Routines
        self._astro_routines = AstronomicalRoutines(
            self._latitude,
            self._longitude,
            self._elevation,
            self._timezone_info,
            self._test_datetime,
        )

        self._atmosphere = AtmosphericRoutines()

        # Testing
        self._test_mode = False
        if self._test_datetime is not None:
            self._test_mode = True

    # Public functions
    async def get_location_data(
        self,
    ) -> None:
        """Returns station Weather Forecast."""

        return await self._get_location_data()

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

        await self.retrieve_data_metno()
        await self.retrieve_data_seventimer()
        now = datetime.now(UTC).replace(tzinfo=None)

        if self._test_datetime is not None:
            await self._astro_routines.need_update()
        else:
            await self._astro_routines.need_update(forecast_time=now)

        forecast_time = now.replace(minute=0, second=0, microsecond=0)
        if self._test_datetime is not None:
            forecast_time = self._test_datetime.replace(
                minute=0, second=0, microsecond=0
            )
        _LOGGER.debug("Forecast time: %s", str(forecast_time))

        if len(self._weather_data_metno) == 0:
            _LOGGER.error("Met.no data not available")
            return []

        # Met.no
        metno_index = 0
        seventimer_index = 0

        # Met.no: Search for start index
        for metno_index, datapoint in enumerate(self._weather_data_metno):
            if forecast_time == datetime.strptime(
                datapoint.get("time"), "%Y-%m-%dT%H:%M:%SZ"
            ):
                break
        if metno_index > len(self._weather_data_metno):
            _LOGGER.error("Met.no start index not found")
            return []
        _LOGGER.debug("Met.no start index: %s", str(metno_index))

        details_metno = (
            self._weather_data_metno[metno_index]
            .get("data", {})
            .get("instant", {})
            .get("details", {})
        )
        details_metno_next_1_hours = (
            self._weather_data_metno[metno_index]
            .get("data", {})
            .get("next_1_hours", {})
        )
        details_metno_next_6_hours = (
            self._weather_data_metno[metno_index]
            .get("data", {})
            .get("next_6_hours", {})
        )

        # Break condition
        if details_metno_next_1_hours is None:
            # No more hourly data
            _LOGGER.debug(
                "No more hourly data at %s",
                self._weather_data_metno[metno_index].get("time", {}),
            )
            return None
        if details_metno_next_6_hours is None:
            # No more 6-hourly data
            _LOGGER.debug(
                "No more 6-hourly data at %s",
                self._weather_data_metno[metno_index].get("time", {}),
            )
            return None

        # 7Timer: Search for start index
        seventimer_init = await cnv.anchor_timestamp(self._weather_data_seventimer_init)
        for row7 in self._weather_data_seventimer:
            if seventimer_init + timedelta(hours=row7["timepoint"]) > now:
                break
            seventimer_index += 1
        if seventimer_index < len(self._weather_data_seventimer):
            _LOGGER.debug("7Timer start index: %s", str(seventimer_index))
            details_seventimer = self._weather_data_seventimer[seventimer_index]
        else:
            details_seventimer = {
                "timepoint": 0,
                "seeing": _NOT_AVAILABLE,
                "transparency": _NOT_AVAILABLE,
                "lifted_index": _NOT_AVAILABLE,
            }

        seeing = 0
        if details_seventimer["seeing"] == _NOT_AVAILABLE:
            seeing = await self._atmosphere.calculate_seeing(
                temperature=details_metno.get("air_temperature"),
                humidity=details_metno.get("relative_humidity"),
                dew_point_temperature=details_metno.get("dew_point_temperature"),
                wind_speed=details_metno.get("wind_speed"),
                cloud_cover=details_metno.get("cloud_area_fraction"),
                altitude=self._elevation,
                air_pressure_at_sea_level=details_metno.get(
                    "air_pressure_at_sea_level"
                ),
            )
        else:
            seeing = SEEING[max(0, min(7, int(details_seventimer["seeing"] - 1)))]

        transparency = 0
        if details_seventimer["transparency"] == _NOT_AVAILABLE:
            transparency = await self._atmosphere.magnitude_degradation(
                temperature=details_metno.get("air_temperature"),
                humidity=details_metno.get("relative_humidity"),
                dew_point_temperature=details_metno.get("dew_point_temperature"),
                wind_speed=details_metno.get("wind_speed"),
                cloud_cover=details_metno.get("cloud_area_fraction"),
                altitude=self._elevation,
                air_pressure_at_sea_level=details_metno.get(
                    "air_pressure_at_sea_level"
                ),
            )
        else:
            transparency = TRANSPARENCY[
                max(0, min(7, int(details_seventimer["transparency"] - 1)))
            ]

        lifted_index = 0
        if details_seventimer["lifted_index"] == _NOT_AVAILABLE:
            lifted_index = await self._atmosphere.calculate_lifted_index(
                temperature=details_metno.get("air_temperature"),
                dew_point_temperature=details_metno.get("dew_point_temperature"),
                altitude=self._elevation,
                air_pressure_at_sea_level=details_metno.get(
                    "air_pressure_at_sea_level"
                ),
            )
        else:
            lifted_index = details_seventimer["lifted_index"]

        item = {
            # seventimer_init is "init" of 7timer astro data
            "seventimer_init": seventimer_init,  # init
            # seventimer_timepoint is "timepoint" of 7timer astro data and defines the data for init + timepoint
            "seventimer_timepoint": details_seventimer["timepoint"],  # timepoint
            # Forecast_time is the actual datetime for the forecast data onwards in UTC
            # Corresponds to "time" in met data
            "forecast_time": forecast_time,  # timestamp
            # Time shift to UTC
            "time_shift": await self._astro_routines.time_shift(),
            # Remaining forecast data point in met.no data
            "forecast_length": (len(self._weather_data_metno) - metno_index),
            # Location
            "latitude": self._latitude,
            "longitude": self._longitude,
            "elevation": self._elevation,
            #
            "seeing": seeing,
            "transparency": transparency,
            "lifted_index": lifted_index,
            # Astronomical routines
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
            "moon_next_full_moon": await self._astro_routines.moon_next_full_moon(),
            "moon_altitude": await self._astro_routines.moon_altitude(),
            "moon_azimuth": await self._astro_routines.moon_azimuth(),
            "night_duration_astronomical": await self._astro_routines.night_duration_astronomical(),
            "deep_sky_darkness_moon_rises": await self._astro_routines.deep_sky_darkness_moon_rises(),
            "deep_sky_darkness_moon_sets": await self._astro_routines.deep_sky_darkness_moon_sets(),
            "deep_sky_darkness_moon_always_up": await self._astro_routines.deep_sky_darkness_moon_always_up(),
            "deep_sky_darkness_moon_always_down": await self._astro_routines.deep_sky_darkness_moon_always_down(),
            "deep_sky_darkness": await self._astro_routines.deep_sky_darkness(),
            "deepsky_forecast": await self._get_deepsky_forecast(),
            # Met.no
            "cloudcover": details_metno.get("cloud_area_fraction"),
            "cloud_area_fraction": details_metno.get("cloud_area_fraction"),
            "cloud_area_fraction_high": details_metno.get("cloud_area_fraction_high"),
            "cloud_area_fraction_low": details_metno.get("cloud_area_fraction_low"),
            "cloud_area_fraction_medium": details_metno.get(
                "cloud_area_fraction_medium"
            ),
            "fog_area_fraction": details_metno.get("fog_area_fraction"),
            "rh2m": details_metno.get("relative_humidity"),
            "wind_speed": details_metno.get("wind_speed"),
            "wind_from_direction": details_metno.get("wind_from_direction"),
            "temp2m": details_metno.get("air_temperature"),
            "dewpoint2m": details_metno.get("dew_point_temperature"),
            "weather": details_metno_next_1_hours.get("summary", {}).get("symbol_code"),
            "weather6": details_metno_next_6_hours.get("summary", {}).get(
                "symbol_code"
            ),
            "precipitation_amount": details_metno_next_1_hours.get("details", {}).get(
                "precipitation_amount"
            ),
            "precipitation_amount6": details_metno_next_6_hours.get("details", {}).get(
                "precipitation_amount"
            ),
            # Condition
            "condition_percentage": await self._calc_condition_percentage(
                details_metno.get("cloud_area_fraction_high"),
                details_metno.get("cloud_area_fraction_medium"),
                details_metno.get("cloud_area_fraction_low"),
                seeing,
                transparency,
                details_metno.get("wind_speed"),
                details_metno_next_1_hours.get("details", {}).get(
                    "precipitation_amount"
                ),
            ),
            # Uptonight objects
            "uptonight": await self._get_deepsky_objects(),
            "uptonight_bodies": await self._get_bodies(),
            "uptonight_comets": await self._get_comets(),
        }

        items.append(LocationData(item))

        return items

    async def _get_forecast_data(self, forecast_type, hours_to_show) -> None:
        """Return Forecast data for the Station."""

        cnv = ConversionFunctions()
        items = []

        await self.retrieve_data_metno()
        await self.retrieve_data_seventimer()
        now = datetime.now(UTC).replace(tzinfo=None)

        # Create items
        cnt = 0

        forecast_time = now.replace(minute=0, second=0, microsecond=0)
        if self._test_datetime is not None:
            forecast_time = self._test_datetime.replace(
                minute=0, second=0, microsecond=0
            )
        _LOGGER.debug("Forecast time: %s", str(forecast_time))

        # 7Timer: Search for start index
        seventimer_init = await cnv.anchor_timestamp(self._weather_data_seventimer_init)

        # Anchor timestamp
        init_ts = await cnv.anchor_timestamp(self._weather_data_seventimer_init)

        utc_to_local_diff = self._astro_routines.utc_to_local_diff()
        _LOGGER.debug("UTC to local diff: %s", str(utc_to_local_diff))
        # _LOGGER.debug("Forecast length 7timer: %s", str(len(self._weather_data_seventimer)))

        if len(self._weather_data_metno) == 0:
            _LOGGER.error("Met.no data not available")
            return []

        last_forecast_time = forecast_time
        for metno_index, datapoint in enumerate(self._weather_data_metno):
            if forecast_time > datetime.strptime(
                datapoint.get("time"), "%Y-%m-%dT%H:%M:%SZ"
            ):
                continue

            if datetime.strptime(
                datapoint.get("time"), "%Y-%m-%dT%H:%M:%SZ"
            ) - last_forecast_time > timedelta(hours=1):
                break

            last_forecast_time = datetime.strptime(
                datapoint.get("time"), "%Y-%m-%dT%H:%M:%SZ"
            )
            details_metno = datapoint.get("data", {}).get("instant", {}).get("details")

            if details_metno.get("cloud_area_fraction") is None:
                _LOGGER.error("Missing Met.no data")
                break

            details_seventimer = self._get_data_seventimer_timer(
                seventimer_init,
                datetime.strptime(datapoint.get("time"), "%Y-%m-%dT%H:%M:%SZ"),
            )
            details_metno_next_1_hours = (
                self._weather_data_metno[metno_index]
                .get("data", {})
                .get("next_1_hours")
            )
            details_metno_next_6_hours = (
                self._weather_data_metno[metno_index]
                .get("data", {})
                .get("next_6_hours")
            )

            # Break condition
            if details_metno_next_1_hours is None:
                # No more hourly data
                _LOGGER.debug(
                    "No more hourly data at %s",
                    self._weather_data_metno[metno_index].get("time", {}),
                )
                break
            if details_metno_next_6_hours is None:
                # No more 6-hourly data
                _LOGGER.debug(
                    "No more 6-hourly data at %s",
                    self._weather_data_metno[metno_index].get("time", {}),
                )
                break

            item = {
                "seventimer_init": init_ts,
                "seventimer_timepoint": details_seventimer["timepoint"],
                "forecast_time": datetime.strptime(
                    datapoint.get("time"), "%Y-%m-%dT%H:%M:%SZ"
                ),
                "hour": datetime.strptime(
                    datapoint.get("time"), "%Y-%m-%dT%H:%M:%SZ"
                ).hour,  # forecast_time.hour % 24,
            }

            seeing = 0
            if details_seventimer["seeing"] == _NOT_AVAILABLE:
                seeing = await self._atmosphere.calculate_seeing(
                    temperature=details_metno.get("air_temperature"),
                    humidity=details_metno.get("relative_humidity"),
                    dew_point_temperature=details_metno.get("dew_point_temperature"),
                    wind_speed=details_metno.get("wind_speed"),
                    cloud_cover=details_metno.get("cloud_area_fraction"),
                    altitude=self._elevation,
                    air_pressure_at_sea_level=details_metno.get(
                        "air_pressure_at_sea_level"
                    ),
                )
            else:
                seeing = SEEING[max(0, min(7, int(details_seventimer["seeing"] - 1)))]

            transparency = 0
            if details_seventimer["transparency"] == _NOT_AVAILABLE:
                transparency = await self._atmosphere.magnitude_degradation(
                    temperature=details_metno.get("air_temperature"),
                    humidity=details_metno.get("relative_humidity"),
                    dew_point_temperature=details_metno.get("dew_point_temperature"),
                    wind_speed=details_metno.get("wind_speed"),
                    cloud_cover=details_metno.get("cloud_area_fraction"),
                    altitude=self._elevation,
                    air_pressure_at_sea_level=details_metno.get(
                        "air_pressure_at_sea_level"
                    ),
                )
            else:
                transparency = TRANSPARENCY[
                    max(0, min(7, int(details_seventimer["transparency"] - 1)))
                ]

            lifted_index = 0
            if details_seventimer["lifted_index"] == _NOT_AVAILABLE:
                lifted_index = await self._atmosphere.calculate_lifted_index(
                    temperature=details_metno.get("air_temperature"),
                    dew_point_temperature=details_metno.get("dew_point_temperature"),
                    altitude=self._elevation,
                    air_pressure_at_sea_level=details_metno.get(
                        "air_pressure_at_sea_level"
                    ),
                )
            else:
                lifted_index = details_seventimer["lifted_index"]

            item["cloudcover"] = details_metno.get("cloud_area_fraction")
            item["cloud_area_fraction"] = details_metno.get("cloud_area_fraction")
            item["cloud_area_fraction_high"] = details_metno.get(
                "cloud_area_fraction_high"
            )
            item["cloud_area_fraction_medium"] = details_metno.get(
                "cloud_area_fraction_medium"
            )
            item["cloud_area_fraction_low"] = details_metno.get(
                "cloud_area_fraction_low"
            )
            item["fog_area_fraction"] = details_metno.get("fog_area_fraction")
            item["rh2m"] = details_metno.get("relative_humidity")
            item["wind_speed"] = details_metno.get("wind_speed")
            item["seeing"] = seeing
            item["transparency"] = transparency
            item["lifted_index"] = lifted_index
            item["precipitation_amount"] = details_metno_next_1_hours.get(
                "details", {}
            ).get("precipitation_amount")
            item["condition_percentage"] = await self._calc_condition_percentage(
                item["cloud_area_fraction_high"],
                item["cloud_area_fraction_medium"],
                item["cloud_area_fraction_low"],
                seeing,
                transparency,
                item["wind_speed"],
                details_metno_next_1_hours.get("details", {}).get(
                    "precipitation_amount"
                ),
            )
            item["wind_from_direction"] = details_metno.get("wind_from_direction")
            item["temp2m"] = details_metno.get("air_temperature")
            item["dewpoint2m"] = details_metno.get("dew_point_temperature")
            item["weather"] = details_metno_next_1_hours.get("summary", {}).get(
                "symbol_code"
            )
            item["weather6"] = details_metno_next_6_hours.get("summary", {}).get(
                "symbol_code"
            )
            item["precipitation_amount6"] = details_metno_next_6_hours.get(
                "details", {}
            ).get("precipitation_amount")

            items.append(ForecastData(item))

            item["seventimer_timepoint"] = item["seventimer_timepoint"] + 1
            item["forecast_time"] = item["forecast_time"] + timedelta(hours=1)
            item["hour"] = item["hour"] + 1

            cnt += 1
            if cnt >= hours_to_show:
                break

        self._forecast_data = items

        _LOGGER.debug("Forceast Length: %s", str(len(items)))
        return items

    async def _get_deepsky_forecast(self):
        """Return Deepsky Forecast data."""

        cnv = ConversionFunctions()
        items = []

        if self._forecast_data == None:
            await self._get_forecast_data(FORECAST_TYPE_HOURLY, 72)

        # Anchor timestamp
        init_ts = await cnv.anchor_timestamp(self._weather_data_seventimer_init)

        utc_to_local_diff = self._astro_routines.utc_to_local_diff()
        _LOGGER.debug("UTC to local diff: %s", str(utc_to_local_diff))

        if self._forecast_data is None:
            _LOGGER.error("Met.no forecast data not available")
            return []

        # Create forecast
        forecast_dayname = ""
        start_forecast_hour = 0
        start_weather = ""
        interval_points = []

        sun_next_setting = await self._astro_routines.sun_next_setting()
        sun_next_rising = await self._astro_routines.sun_next_rising()
        night_duration_astronomical = (
            await self._astro_routines.night_duration_astronomical()
        )

        start_indexes = []
        # Find start index for two nights and store the indexes
        # _LOGGER.debug("Forecast data length: %s", str(len(self._forecast_data)))
        for index, details_forecast in enumerate(self._forecast_data):
            if (
                details_forecast.forecast_time.hour % 24 == sun_next_rising.hour
                and len(start_indexes) == 0
            ):
                start_indexes.append(0)
            if details_forecast.forecast_time.hour % 24 == sun_next_setting.hour:
                start_indexes.append(index)

        forecast_data_len = len(self._forecast_data)
        for day in range(0, len(start_indexes)):
            start_forecast_hour = 0
            start_weather = ""
            interval_points = []
            start_index = start_indexes[day]
            for index in range(
                start_index,
                start_index + int(math.floor(night_duration_astronomical / 3600) + 2),
            ):
                if index >= forecast_data_len:
                    _LOGGER.debug("No more forecast data")
                    break
                details_forecast = self._forecast_data[index]

                if len(interval_points) == 0:
                    forecast_dayname = details_forecast.forecast_time.strftime("%A")
                    start_forecast_hour = details_forecast.forecast_time.hour
                    start_weather = details_forecast.weather6
                    start_precipitation_amount6 = details_forecast.precipitation_amount6

                # _LOGGER.debug(
                #     "Idex: %d, Hour of day: %d, cloud_area_fraction: %s %s %s, seeing: %s, transparency: %s, wind_speed: %s, condition: %s",
                #     index,
                #     details_forecast.forecast_time.hour,
                #     str(details_forecast.cloud_area_fraction_high_percentage),
                #     str(details_forecast.cloud_area_fraction_medium_percentage),
                #     str(details_forecast.cloud_area_fraction_low_percentage),
                #     str(details_forecast.seeing),
                #     str(details_forecast.transparency),
                #     str(details_forecast.wind10m_speed),
                #     await self._calc_condition_percentage(
                #         details_forecast.cloud_area_fraction_high_percentage,
                #         details_forecast.cloud_area_fraction_medium_percentage,
                #         details_forecast.cloud_area_fraction_low_percentage,
                #         details_forecast.seeing,
                #         details_forecast.transparency,
                #         details_forecast.wind10m_speed,
                #     ),
                # )

                # Calculate Condition
                if len(interval_points) <= int(
                    math.floor(night_duration_astronomical / 3600)
                ):
                    interval_points.append(
                        await self._calc_condition_percentage(
                            details_forecast.cloud_area_fraction_high_percentage,
                            details_forecast.cloud_area_fraction_medium_percentage,
                            details_forecast.cloud_area_fraction_low_percentage,
                            details_forecast.seeing,
                            details_forecast.transparency,
                            details_forecast.wind10m_speed,
                            details_forecast.precipitation_amount,
                        )
                    )

                if (
                    details_forecast.forecast_time.hour == sun_next_rising.hour
                    or index >= (forecast_data_len - 1)
                ):
                    item = {
                        "seventimer_init": init_ts,
                        "dayname": forecast_dayname,
                        "hour": start_forecast_hour,
                        "nightly_conditions": interval_points,
                        "weather": start_weather,
                        "precipitation_amount6": start_precipitation_amount6,
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

                    # Test for end of astronomical night. Will get true if we're already at night.
                    if details_forecast.forecast_time.hour % 24 == sun_next_rising.hour:
                        break
            start_index += 24

        return items

    async def _calc_condition_percentage(
        self,
        cloudcover_high,
        cloudcover_medium,
        cloudcover_low,
        seeing,
        transparency,
        wind_speed,
        precipitation_amount,
    ):
        """Return condition based on cloud cover, seeing, transparency, and wind speed."""

        if not all(
            v is not None
            for v in [
                cloudcover_high,
                cloudcover_medium,
                cloudcover_low,
                seeing,
                transparency,
                wind_speed,
                precipitation_amount,
            ]
        ):
            return None

        # Seeing is something in between 0 and 2.5 arcsecs
        seeing = seeing * 100 / SEEING_MAX  # arcsecs up to 2.5
        # transparency = int(transparency * 40)  # mag degration up to 2.5
        transparency = (
            transparency * 100 / MAG_DEGRATION_MAX
        )  # mag degration up to MAG_DEGRATION_MAX
        # Wind speed is something in between 0 and 16.5 m/s
        if wind_speed > WIND10M_MAX:
            wind_speed = WIND10M_MAX
        wind_speed_value = int(wind_speed * (100 / WIND10M_MAX))  # m/s up to 16.5

        cloudcover = []
        cloudcover.append(cloudcover_high * self._cloudcover_high_weakening)
        cloudcover.append(cloudcover_medium * self._cloudcover_medium_weakening)
        cloudcover.append(cloudcover_low * self._cloudcover_low_weakening)

        condition = int(
            100
            - (
                self._cloudcover_weight * max(cloudcover)
                + self._seeing_weight * seeing
                + self._transparency_weight * transparency
                + self._calm_weight * wind_speed_value
            )
            / (
                self._cloudcover_weight
                + self._seeing_weight
                + self._transparency_weight
                + self._calm_weight
            )
            - precipitation_amount * 100
        )

        # _LOGGER.debug(
        #     "Cloudcover: %s %s, Seeing: %s %s, Transparency: %s %s, Calmness: %s %s, Conditions: %s",
        #     str(max(cloudcover)),
        #     str(self._cloudcover_weight),
        #     str(seeing),
        #     str(self._seeing_weight),
        #     str(transparency),
        #     str(self._transparency_weight),
        #     str(wind_speed_value),
        #     str(self._calm_weight),
        #     condition,
        # )

        # Ensure condition is within the valid range [0, 1]
        condition = max(0, min(100, condition))

        return condition

    async def _get_deepsky_objects(self):
        """Return Deepsky Objects for today."""

        items = []

        await self.retrieve_data_uptonight()

        # Create list of deep sky objects
        if self._weather_data_uptonight is not None:
            dso_id = self._weather_data_uptonight.get("id", {})
            dso_target_name = self._weather_data_uptonight.get("target name", {})
            dso_type = self._weather_data_uptonight.get("type", {})
            dso_constellation = self._weather_data_uptonight.get("constellation", {})
            dso_size = self._weather_data_uptonight.get("size", {})
            dso_visual_magnitude = self._weather_data_uptonight.get("mag", {})
            dso_meridian_transit = self._weather_data_uptonight.get(
                "meridian transit", {}
            )
            dso_meridian_antitransit = self._weather_data_uptonight.get(
                "meridian antitransit", {}
            )
            dso_foto = self._weather_data_uptonight.get("foto", {})

            for row in range(len(dso_target_name)):
                dso_meridian_transit_local = dso_meridian_transit.get(str(row), "")
                if dso_meridian_transit_local != "":
                    dso_meridian_transit_utc = (
                        datetime.strptime(
                            dso_meridian_transit_local, "%m/%d/%Y %H:%M:%S"
                        )
                        - timedelta(seconds=await self._astro_routines.time_shift())
                    ).replace(tzinfo=UTC)
                else:
                    dso_meridian_transit_utc = ""

                dso_meridian_antitransit_local = dso_meridian_antitransit.get(
                    str(row), ""
                )
                if dso_meridian_antitransit_local != "":
                    dso_meridian_antitransit_utc = (
                        datetime.strptime(
                            dso_meridian_antitransit_local, "%m/%d/%Y %H:%M:%S"
                        )
                        - timedelta(seconds=await self._astro_routines.time_shift())
                    ).replace(tzinfo=UTC)
                else:
                    dso_meridian_antitransit_utc = ""

                item = {
                    "id": dso_id.get(str(row), ""),
                    "target_name": dso_target_name.get(str(row), ""),
                    "type": dso_type.get(str(row), ""),
                    "constellation": dso_constellation.get(str(row), ""),
                    "size": dso_size.get(str(row), ""),
                    "visual_magnitude": dso_visual_magnitude.get(str(row), ""),
                    "meridian_transit": dso_meridian_transit_utc,
                    "meridian_antitransit": dso_meridian_antitransit_utc,
                    "foto": dso_foto.get(str(row), ""),
                }
                items.append(DSOUpTonight(item))

            return items
        return None

    async def _get_bodies(self):
        """Return Bodies for today."""

        items = []

        await self.retrieve_data_uptonight()

        # Create list of bodies
        if self._weather_data_uptonight_bodies is not None:
            body_target_name = self._weather_data_uptonight_bodies.get(
                "target name", {}
            )
            body_max_altitude = self._weather_data_uptonight_bodies.get(
                "max altitude", {}
            )
            body_azimuth = self._weather_data_uptonight_bodies.get("azimuth", {})
            body_max_altitude_time = self._weather_data_uptonight_bodies.get(
                "max altitude time", {}
            )
            body_visual_magnitude = self._weather_data_uptonight_bodies.get(
                "visual magnitude", {}
            )
            body_meridian_transit = self._weather_data_uptonight_bodies.get(
                "meridian transit", {}
            )
            body_foto = self._weather_data_uptonight_bodies.get("foto", {})

            for row in range(len(body_target_name)):
                # UpTonight delivers the time in local time zone. here we need it in UTC
                body_max_altitude_time_local = body_max_altitude_time.get(str(row), "")
                body_max_altitude_time_utc = (
                    datetime.strptime(body_max_altitude_time_local, "%m/%d/%Y %H:%M:%S")
                    - timedelta(seconds=await self._astro_routines.time_shift())
                ).replace(tzinfo=UTC)

                body_meridian_transit_local = body_meridian_transit.get(str(row), "")
                if body_meridian_transit_local != "":
                    body_meridian_transit_utc = (
                        datetime.strptime(
                            body_meridian_transit_local, "%m/%d/%Y %H:%M:%S"
                        )
                        - timedelta(seconds=await self._astro_routines.time_shift())
                    ).replace(tzinfo=UTC)
                else:
                    body_meridian_transit_utc = ""

                item = {
                    "target_name": body_target_name.get(str(row), ""),
                    "max_altitude": body_max_altitude.get(str(row), ""),
                    "azimuth": body_azimuth.get(str(row), ""),
                    "max_altitude_time": body_max_altitude_time_utc,
                    "visual_magnitude": body_visual_magnitude.get(str(row), ""),
                    "meridian_transit": body_meridian_transit_utc,
                    "foto": body_foto.get(str(row), ""),
                }
                items.append(BODIESUpTonight(item))

            return items
        return None

    async def _get_comets(self):
        """Return Comets for today."""

        items = []

        await self.retrieve_data_uptonight()

        # Create list of comets
        if self._weather_data_uptonight_comets is not None:
            comet_target_name = self._weather_data_uptonight_comets.get(
                "target name", {}
            )
            distance_au_earth = self._weather_data_uptonight_comets.get(
                "distance earth au", {}
            )
            distance_au_sun = self._weather_data_uptonight_comets.get(
                "distance sun au", {}
            )
            absolute_magnitude = self._weather_data_uptonight_comets.get(
                "absolute magnitude", {}
            )
            visual_magnitude = self._weather_data_uptonight_comets.get(
                "visual magnitude", {}
            )
            altitude = self._weather_data_uptonight_comets.get("altitude", {})
            azimuth = self._weather_data_uptonight_comets.get("azimuth", {})
            rise_time = self._weather_data_uptonight_comets.get("rise time", {})
            set_time = self._weather_data_uptonight_comets.get("set time", {})

            for row in range(len(comet_target_name)):
                # UpTonight delivers the time in local time zone. here we need it in UTC
                rise_time_local = rise_time.get(str(row), "")
                set_time_local = set_time.get(str(row), "")
                rise_time_local_utc = (
                    datetime.strptime(rise_time_local, "%m/%d/%Y %H:%M:%S")
                    - timedelta(seconds=await self._astro_routines.time_shift())
                ).replace(tzinfo=UTC)
                set_time_local_utc = (
                    datetime.strptime(set_time_local, "%m/%d/%Y %H:%M:%S")
                    - timedelta(seconds=await self._astro_routines.time_shift())
                ).replace(tzinfo=UTC)

                item = {
                    "designation": comet_target_name.get(str(row), ""),
                    "distance_au_earth": distance_au_earth.get(str(row), ""),
                    "distance_au_sun": distance_au_sun.get(str(row), ""),
                    "absolute_magnitude": absolute_magnitude.get(str(row), ""),
                    "visual_magnitude": visual_magnitude.get(str(row), ""),
                    "altitude": altitude.get(str(row), ""),
                    "azimuth": azimuth.get(str(row), ""),
                    # "ra": body_azimuth.get(str(row), ""),
                    # "dec": body_azimuth.get(str(row), ""),
                    "rise_time": rise_time_local_utc,
                    "set_time": set_time_local_utc,
                }
                items.append(COMETSUpTonight(item))

            return items
        return None

    async def retrieve_data_seventimer(self):
        """Retrieves current data from 7timer."""

        if (
            (datetime.now() - self._weather_data_seventimer_timestamp).total_seconds()
        ) > DEFAULT_CACHE_TIMEOUT:
            self._weather_data_seventimer_timestamp = datetime.now()
            _LOGGER.debug("Updating data from 7Timer")

            astro_dataseries = {}

            # Testing
            if not self._experimental_features:
                if self._test_mode:
                    if os.path.isfile("debug/astro.json"):
                        _LOGGER.debug("Reading 7Timer from file")
                        with open("debug/astro.json") as json_file:
                            astro_dataseries_json = json.load(json_file)
                            astro_dataseries = astro_dataseries_json.get(
                                "dataseries", {}
                            )
                            json_data_astro = {
                                "init": astro_dataseries_json.get("init")
                            }
                    else:
                        json_data_astro = await self.async_request_seventimer(
                            "astro", "get"
                        )
                        astro_dataseries = json_data_astro.get("dataseries", {})
                else:
                    json_data_astro = await self.async_request_seventimer(
                        "astro", "get"
                    )
                    astro_dataseries = json_data_astro.get("dataseries", {})

            if astro_dataseries != {} and not self._experimental_features:
                self._weather_data_seventimer = astro_dataseries
                self._weather_data_seventimer_init = json_data_astro.get("init")
            else:
                # Fake 7timer weather data if service is broken
                # This eliminates consideration of seeing, transparency, and lifted_index
                # and switches automatically to experimental functions.
                self._weather_data_seventimer = []
                for index in range(0, 20):
                    self._weather_data_seventimer.append(
                        {
                            "timepoint": index * 3,
                            "seeing": _NOT_AVAILABLE,
                            "transparency": _NOT_AVAILABLE,
                            "lifted_index": _NOT_AVAILABLE,
                        }
                    )
                self._weather_data_seventimer_init = (
                    datetime.now(UTC).replace(tzinfo=None).strftime("%Y%m%d%H")
                )
        else:
            _LOGGER.debug("Using cached data for 7Timer")

    async def async_request_seventimer(self, product="astro", method="get") -> dict:
        """Make a request against the 7timer API."""

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        # BASE_URL_SEVENTIMER = "https://www.7timer.info/bin/api.pl?lon=XX.XX&lat=YY.YY&product=astro&output=json"
        url = (
            str(f"{BASE_URL_SEVENTIMER}")
            + "?lon="
            + str("%.1f" % round(self._longitude, 2))
            + "&lat="
            + str("%.1f" % round(self._latitude, 2))
            + "&product="
            + str(product)
            + "&output=json"
        )
        try:
            _LOGGER.debug(f"Query url: {url}")
            async with session.request(method, url, headers=HEADERS, ssl=False) as resp:
                resp.raise_for_status()
                plain = str(await resp.text()).replace("\n", " ")
                data = json.loads(plain)

                if self._test_mode:
                    json_string = json.dumps(data)
                    with open("debug/" + product + ".json", "w") as outfile:
                        outfile.write(json_string)

                return data
        except JSONDecodeError as jsonerr:
            _LOGGER.error(f"JSON decode error, expecting value: {jsonerr}")
            return {}
        except asyncio.TimeoutError as tex:
            _LOGGER.error(f"Request to endpoint timed out: {tex}")
            return {}
        except ClientError as err:
            _LOGGER.error(f"Error requesting data: {err}")
            return {}

        finally:
            if not use_running_session:
                await session.close()

    def _get_data_seventimer_timer(self, anchor_timestamp, datetime):
        """Return 7Timer datapoint of interest."""

        seventimer_index = 0
        for index, row7 in enumerate(self._weather_data_seventimer):
            if anchor_timestamp + timedelta(hours=row7["timepoint"]) > datetime:
                seventimer_index = index - 1
                break
            # index += 1
        if seventimer_index >= len(self._weather_data_seventimer):
            return {
                "timepoint": row7["timepoint"],
                "seeing": _NOT_AVAILABLE,
                "transparency": _NOT_AVAILABLE,
                "lifted_index": _NOT_AVAILABLE,
            }
        else:
            return self._weather_data_seventimer[seventimer_index]

    async def retrieve_data_metno(self):
        """Retrieves current data from met."""

        if (
            (datetime.now() - self._weather_data_metno_timestamp).total_seconds()
        ) > DEFAULT_CACHE_TIMEOUT:
            self._weather_data_metno_timestamp = datetime.now()
            _LOGGER.debug("Updating data from Met.no")

            dataseries = None

            # Testing
            if self._test_mode:
                if os.path.isfile("debug/met.json"):
                    _LOGGER.debug("Reading Met.no data from file")
                    with open("debug/met.json") as json_file:
                        dataseries = (
                            json.load(json_file).get("properties", {}).get("timeseries")
                        )
                else:
                    json_data_metno = await self.async_request_met("met", "get")
                    dataseries = json_data_metno.get("properties", {}).get("timeseries")
            else:
                json_data_metno = await self.async_request_met("met", "get")
                dataseries = json_data_metno.get("properties", {}).get("timeseries")

            if dataseries is not None:
                if len(dataseries) > 0:
                    self._weather_data_metno = dataseries
                    self._weather_data_metno_init = dataseries[0].get("time")
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
            async with session.request(method, url, headers=HEADERS) as resp:
                resp.raise_for_status()
                # plain = str(await resp.text()).replace("\n", " ")
                # data = json.loads(plain)
                data = await resp.json()

                if self._test_mode:
                    json_string = json.dumps(data)
                    with open("debug/" + product + ".json", "w") as outfile:
                        outfile.write(json_string)

                return data
        except JSONDecodeError as jsonerr:
            _LOGGER.error(f"JSON decode error, expecting value: {jsonerr}")
            return {}
        except asyncio.TimeoutError as tex:
            _LOGGER.error(f"Request to endpoint timed out: {tex}")
            return {}
        except ClientError as err:
            _LOGGER.error(f"Error requesting data: {err}")
            return {}

        finally:
            if not use_running_session:
                await session.close()

    async def retrieve_data_uptonight(self):
        """Retrieves current data from uptonight"""

        if (
            (datetime.now() - self._data_uptonight_timestamp).total_seconds()
        ) > DEFAULT_CACHE_TIMEOUT:
            self._data_uptonight_timestamp = datetime.now()
            _LOGGER.debug("Updating data from uptonight")

            dataseries_dso = None
            dataseries_bodies = None
            dataseries_comets = None

            if os.path.exists(self._uptonight_path):
                if os.path.isfile(self._uptonight_path + "/uptonight-report.json"):
                    # _LOGGER.debug(f"Uptonight report found")
                    async with aiofiles.open(
                        self._uptonight_path + "/uptonight-report.json", mode="r"
                    ) as json_file:
                        contents = await json_file.read()
                    dataseries_dso = json.loads(contents)
                    _LOGGER.debug("Uptonight DSO imported")
                else:
                    _LOGGER.debug(
                        f"File uptonight-report.json not found in {self._uptonight_path}"
                    )

                if os.path.isfile(
                    self._uptonight_path + "/uptonight-bodies-report.json"
                ):
                    # _LOGGER.debug(f"Uptonight report found")
                    async with aiofiles.open(
                        self._uptonight_path + "/uptonight-bodies-report.json", mode="r"
                    ) as json_file:
                        contents = await json_file.read()
                    dataseries_bodies = json.loads(contents)
                    _LOGGER.debug("Uptonight Bodies imported")
                else:
                    _LOGGER.debug(
                        f"File uptonight-bodies-report.json not found in {self._uptonight_path}"
                    )

                if os.path.isfile(
                    self._uptonight_path + "/uptonight-comets-report.json"
                ):
                    # _LOGGER.debug(f"Uptonight report found")
                    async with aiofiles.open(
                        self._uptonight_path + "/uptonight-comets-report.json", mode="r"
                    ) as json_file:
                        contents = await json_file.read()
                    dataseries_comets = json.loads(contents)
                    _LOGGER.debug("Uptonight Comets imported")
                else:
                    _LOGGER.debug(
                        f"File uptonight-comets-report.json not found in {self._uptonight_path}"
                    )
            else:
                _LOGGER.debug(
                    f"Path for UpTonight data not found. Current path: {self._uptonight_path}/uptonight-report.json"
                )

            self._weather_data_uptonight = dataseries_dso
            self._weather_data_uptonight_bodies = dataseries_bodies
            self._weather_data_uptonight_comets = dataseries_comets
        else:
            _LOGGER.debug("Using cached data for uptonight")
