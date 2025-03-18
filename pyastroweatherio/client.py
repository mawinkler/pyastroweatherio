"""Define a client to interact with 7Timer."""

import asyncio
import json
import logging
import math
import os.path
import socket
from datetime import UTC, datetime, timedelta, timezone
from json.decoder import JSONDecodeError
from pprint import pprint as pp
from typing import Any, Dict, List, Optional

import aiofiles

# from aiohttp.client import ClientError, ClientResponseError, ClientSession
import numpy as np  # from retry_requests import retry

# import openmeteo_requests
# import requests_cache
import pandas as pd
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client import ClientResponseError, ClientSession
from aiohttp.client_exceptions import ClientError
from typeguard import typechecked

from pyastroweatherio.const import (
    BASE_URL_MET,
    BASE_URL_SEVENTIMER,
    BASE_URL_OPENMETEO,
    DEFAULT_CACHE_TIMEOUT,
    DEFAULT_CONDITION_CALM_WEIGHT,
    DEFAULT_CONDITION_CLOUDCOVER_HIGH_WEAKENING,
    DEFAULT_CONDITION_CLOUDCOVER_LOW_WEAKENING,
    DEFAULT_CONDITION_CLOUDCOVER_MEDIUM_WEAKENING,
    DEFAULT_CONDITION_CLOUDCOVER_WEIGHT,
    DEFAULT_CONDITION_FOG_WEIGHT,
    DEFAULT_CONDITION_SEEING_WEIGHT,
    DEFAULT_CONDITION_TRANSPARENCY_WEIGHT,
    DEFAULT_ELEVATION,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_TIMEOUT,
    DEFAULT_TIMEZONE,
    FORECAST_TYPE_HOURLY,
    HEADERS,
    LIFTED_INDEX_7TIMER_MAPPING,
    MAG_DEGRATION_MAX,
    SEEING,
    SEEING_MAX,
    TRANSPARENCY,
    WIND10M_MAX,
)
from pyastroweatherio.dataclasses import (
    ConditionData,
    ConditionDataModel,
    ForecastData,
    ForecastDataModel,
    GeoLocationData,
    GeoLocationDataModel,
    LocationData,
    LocationDataModel,
    NightlyConditionsData,
    NightlyConditionsDataModel,
    TimeData,
    TimeDataModel,
    UpTonightBodiesData,
    UpTonightBodiesDataModel,
    UpTonightCometsData,
    UpTonightCometsDataModel,
    UpTonightDSOData,
    UpTonightDSODataModel,
)
from pyastroweatherio.errors import OpenMeteoConnectionError, OpenMeteoError
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
        fog_weight=DEFAULT_CONDITION_FOG_WEIGHT,
        seeing_weight=DEFAULT_CONDITION_SEEING_WEIGHT,
        transparency_weight=DEFAULT_CONDITION_TRANSPARENCY_WEIGHT,
        calm_weight=DEFAULT_CONDITION_CALM_WEIGHT,
        uptonight_path="/conf/www",
        test_datetime=None,
        experimental_features=False,
        forecast_model=None,
    ):
        self._session: ClientSession = session
        self._location_data = self._get_location(
            latitude,
            longitude,
            elevation,
            timezone_info,
        )
        self._weather_data_uptonight = {}
        self._weather_data_uptonight_bodies = {}
        self._weather_data_uptonight_comets = {}
        self._weather_data_timestamp = datetime.now() - timedelta(seconds=(DEFAULT_CACHE_TIMEOUT + 1))
        self._cloudcover_weight = cloudcover_weight
        self._cloudcover_high_weakening = cloudcover_high_weakening
        self._cloudcover_medium_weakening = cloudcover_medium_weakening
        self._cloudcover_low_weakening = cloudcover_low_weakening
        self._fog_weight = fog_weight
        self._seeing_weight = seeing_weight
        self._transparency_weight = transparency_weight
        self._calm_weight = calm_weight
        self._uptonight_path = uptonight_path
        self._test_datetime = test_datetime
        self._experimental_features = experimental_features
        self._forecast_model = forecast_model
        # Open-Meteo
        # DWD Germany: icon_seamless
        # Met.no: metno_seamless
        # NOAA U.S.: gfs_seamless
        # ECMWF: ecmwf_ifs025

        # Weather data
        self._weather_df = None

        # Forecast data
        self._forecast_data = None

        # Astro Routines
        self._astro_routines = AstronomicalRoutines(
            self._location_data,
            self._test_datetime,
        )

        self._atmosphere = AtmosphericRoutines()

        # Testing
        self._test_mode = False
        if self._test_datetime is not None:
            self._test_mode = True

    # #########################################################################
    # Public functions
    # #########################################################################
    @typechecked
    async def get_location_data(
        self,
    ) -> List[LocationData]:
        """Returns station Weather Forecast."""

        return await self._get_location_data()

    @typechecked
    async def get_hourly_forecast(self) -> List[ForecastData]:
        """Returns hourly Weather Forecast."""

        return await self._get_forecast_data(FORECAST_TYPE_HOURLY, 72)

    @typechecked
    async def get_deepsky_forecast(self) -> List[NightlyConditionsData]:
        """Returns Deep Sky Forecast."""

        return await self._get_deepsky_forecast()

    # #########################################################################
    # Private functions
    # #########################################################################
    async def _calculate_dew_point(self, df):
        tasks = [
            self._atmosphere.calculate_dew_point(
                temp2m=row["air_temperature"],
                rh2m=row["relative_humidity"],
            )
            for _, row in df.iterrows()
        ]
        results = await asyncio.gather(*tasks)
        return results

    async def _calculate_seeing(self, df):
        tasks = [
            self._atmosphere.calculate_seeing(
                temperature=row["air_temperature"],
                humidity=row["relative_humidity"],
                dew_point_temperature=row["dew_point_temperature"],
                wind_speed=row["wind_speed"],
                cloud_cover=row["cloud_area_fraction"],
                altitude=self._location_data.elevation,
                air_pressure_at_sea_level=row["air_pressure_at_sea_level"],
            )
            for _, row in df.iterrows()
        ]
        results = await asyncio.gather(*tasks)
        return results

    async def _calculate_transparency(self, df):
        tasks = [
            self._atmosphere.magnitude_degradation(
                temperature=row["air_temperature"],
                humidity=row["relative_humidity"],
                dew_point_temperature=row["dew_point_temperature"],
                wind_speed=row["wind_speed"],
                cloud_cover=row["cloud_area_fraction"],
                altitude=self._location_data.elevation,
                air_pressure_at_sea_level=row["air_pressure_at_sea_level"],
            )
            for _, row in df.iterrows()
        ]
        results = await asyncio.gather(*tasks)
        return results

    async def _calculate_lifted_index(self, df):
        tasks = [
            self._atmosphere.calculate_lifted_index(
                temperature=row["air_temperature"],
                dew_point_temperature=row["dew_point_temperature"],
                altitude=self._location_data.elevation,
                air_pressure_at_sea_level=row["air_pressure_at_sea_level"],
            )
            for _, row in df.iterrows()
        ]
        results = await asyncio.gather(*tasks)
        return results

    async def _retrive_data(self) -> None:
        """Retrieves current data from all data sources."""

        if ((datetime.now() - self._weather_data_timestamp).total_seconds()) > DEFAULT_CACHE_TIMEOUT:
            self._weather_data_timestamp = datetime.now()

            weather_df_metno = await self._retrieve_data_metno()
            if weather_df_metno is None:
                _LOGGER.warning("Could not retrieve Met.no data. Using existing data.")
                return None
            weather_df_seventimer = await self._retrieve_data_seventimer()
            await self._retrieve_data_uptonight()

            if self._forecast_model is not None:
                weather_df_openmeteo = await self._retrieve_data_openmeteo()

                # Merge the dataframes of metno, seventimer, and openmeteo
                self._weather_df = weather_df_metno.merge(weather_df_seventimer, on="time", how="left").merge(
                    weather_df_openmeteo, on="time", how="left"
                )

                # Overwrite met.no forecast with open-meteo forcast
                self._weather_df["cloud_area_fraction"] = self._weather_df["openmeteo_cloud_cover"]
                self._weather_df["cloud_area_fraction_high"] = self._weather_df["openmeteo_cloud_cover_high"]
                self._weather_df["cloud_area_fraction_medium"] = self._weather_df["openmeteo_cloud_cover_mid"]
                self._weather_df["cloud_area_fraction_low"] = self._weather_df["openmeteo_cloud_cover_low"]
                self._weather_df["relative_humidity"] = self._weather_df["openmeteo_relative_humidity_2m"]
                self._weather_df["wind_speed"] = self._weather_df["openmeteo_wind_speed_10m"]
                self._weather_df["wind_from_direction"] = self._weather_df["openmeteo_wind_direction_10m"]
                self._weather_df["air_temperature"] = self._weather_df["openmeteo_temperature_2m"]
                self._weather_df["dew_point_temperature"] = self._weather_df["openmeteo_dew_point_2m"]
                self._weather_df["precipitation_amount"] = self._weather_df["openmeteo_precipitation"]
                self._weather_df = self._weather_df.drop(
                    [
                        "openmeteo_cloud_cover",
                        "openmeteo_cloud_cover_high",
                        "openmeteo_cloud_cover_mid",
                        "openmeteo_cloud_cover_low",
                        "openmeteo_relative_humidity_2m",
                        "openmeteo_wind_speed_10m",
                        "openmeteo_wind_direction_10m",
                        "openmeteo_temperature_2m",
                        "openmeteo_dew_point_2m",
                        "openmeteo_precipitation",
                    ],
                    axis=1,
                )
            else:
                # Merge the dataframes of metno and seventimer
                self._weather_df = weather_df_metno.merge(weather_df_seventimer, on="time", how="left")

            # Clean up rows with missing values
            self._weather_df = self._weather_df.dropna(subset=["air_temperature"])
            self._weather_df = self._weather_df.dropna(subset=["next_6h_symbol_code"])
            self._weather_df = self._weather_df.dropna(subset=["precipitation_amount"])

            self._weather_df["time_diff"] = self._weather_df["time"].diff()
            threshold = pd.Timedelta(hours=1)
            cutoff_index = self._weather_df[self._weather_df["time_diff"] > threshold].index.min()
            if pd.notna(cutoff_index):  # Check if there's a cutoff
                self._weather_df = self._weather_df.loc[: cutoff_index - 1]
            self._weather_df = self._weather_df.drop(columns=["time_diff"])

            # Check if we got dew point temperatures. If not calculate them.
            has_nan_or_none = self._weather_df["dew_point_temperature"].isnull().any()
            if has_nan_or_none:
                _LOGGER.warning(
                    f"Column 'dew_point_temperature' has NaN or None: {has_nan_or_none}. Calculating dew points."
                )
                self._weather_df["dew_point_temperature"] = await self._calculate_dew_point(self._weather_df)

            # Should we try to calculate seeing, transparency, and lifted_index?
            if self._experimental_features:
                # Calculate atmosphere
                self._weather_df["seeing"] = await self._calculate_seeing(self._weather_df)
                self._weather_df["transparency"] = await self._calculate_transparency(self._weather_df)
                self._weather_df["lifted_index"] = await self._calculate_lifted_index(self._weather_df)
            else:
                # 7Timer delivers three hourly data only, so we fill the missing data here
                self._weather_df["seeing"] = self._weather_df["seeing"].ffill()
                self._weather_df["transparency"] = self._weather_df["transparency"].ffill()
                self._weather_df["lifted_index"] = self._weather_df["lifted_index"].ffill()
                self._weather_df["seeing"] = self._weather_df["seeing"].bfill()
                self._weather_df["transparency"] = self._weather_df["transparency"].bfill()
                self._weather_df["lifted_index"] = self._weather_df["lifted_index"].bfill()

            self._test_weather_df()
        else:
            _LOGGER.debug("Using cached data")

    @typechecked
    def _get_location(
        self,
        latitude,
        longitude,
        elevation,
        timezone_info,
    ) -> GeoLocationData | None:
        """Returns a validated GeoLocation data object"""

        geolocation = GeoLocationDataModel(
            {
                "latitude": latitude,
                "longitude": longitude,
                "elevation": elevation,
                "timezone_info": timezone_info,
            }
        )

        try:
            return GeoLocationData(data=geolocation)
        except TypeError as ve:
            _LOGGER.error(f"Failed to parse geo location data: {geolocation}")
            _LOGGER.error(ve)
            return None

    @typechecked
    async def _get_condition(
        self,
        time,
    ) -> ConditionData | None:
        """Returns a validated Weather Conditions data object"""

        # Return row from dataframe
        timestamp = time.replace(tzinfo=None).strftime("%Y-%m-%d %H:00:00+00:00")
        row = self._weather_df.loc[self._weather_df["time"] == timestamp].iloc[0]

        cloudcover = float(row["cloud_area_fraction"])
        cloud_area_fraction = float(row["cloud_area_fraction"])
        cloudcover_high = float(row["cloud_area_fraction_high"])
        cloudcover_medium = float(row["cloud_area_fraction_medium"])
        cloudcover_low = float(row["cloud_area_fraction_low"])
        fog = float(row["fog_area_fraction"])
        rh2m = float(row["relative_humidity"])
        wind_speed = float(row["wind_speed"])
        wind_from_direction = float(row["wind_from_direction"])
        temp2m = float(row["air_temperature"])
        dewpoint2m = float(row["dew_point_temperature"])
        weather = str(row["next_1h_symbol_code"])
        weather6 = str(row["next_6h_symbol_code"])
        precipitation_amount = float(row["next_1h_precipitation_amount"])
        precipitation_amount6 = float(row["next_6h_precipitation_amount"])
        seeing = float(row["seeing"])
        transparency = float(row["transparency"])
        lifted_index = float(row["lifted_index"])

        if self._experimental_features:
            # Calculate Fog Density
            fog2m = await self._atmosphere.calculate_fog_density(temp2m, rh2m, dewpoint2m, wind_speed) * 100
        else:
            fog2m = fog

        condition = ConditionDataModel(
            {
                "cloudcover": cloudcover,
                "cloud_area_fraction": cloud_area_fraction,
                "cloud_area_fraction_high": cloudcover_high,
                "cloud_area_fraction_low": cloudcover_low,
                "cloud_area_fraction_medium": cloudcover_medium,
                "fog_area_fraction": max(fog, fog2m),
                "fog2m": fog2m,
                "seeing": seeing,
                "transparency": transparency,
                "lifted_index": lifted_index,
                "condition_percentage": await self._calc_condition_percentage(
                    cloudcover_high=cloudcover_high,
                    cloudcover_medium=cloudcover_medium,
                    cloudcover_low=cloudcover_low,
                    fog=fog,
                    fog2m=fog2m,
                    seeing=seeing,
                    transparency=transparency,
                    wind_speed=wind_speed,
                    precipitation_amount=precipitation_amount,
                ),
                "rh2m": rh2m,
                "wind_speed": wind_speed,
                "wind_from_direction": wind_from_direction,
                "temp2m": temp2m,
                "dewpoint2m": dewpoint2m,
                "weather": weather,
                "weather6": weather6,
                "precipitation_amount": precipitation_amount,
                "precipitation_amount6": precipitation_amount6,
            }
        )

        try:
            return ConditionData(data=condition)
        except TypeError as ve:
            _LOGGER.error(f"Failed to parse condition data: {condition}")
            _LOGGER.error(ve)
            return None

    @typechecked
    async def _calc_condition_percentage(
        self,
        cloudcover_high,
        cloudcover_medium,
        cloudcover_low,
        fog,
        fog2m,
        seeing,
        transparency,
        wind_speed,
        precipitation_amount,
    ) -> int:
        """Return condition based on cloud cover, fog, seeing, transparency, wind speed, and precipitation."""

        # Seeing is something in between 0 and 2.5 arcsecs
        seeing = seeing * 100 / SEEING_MAX  # arcsecs up to 2.5
        # transparency = int(transparency * 40)  # mag degration up to 2.5
        transparency = transparency * 100 / MAG_DEGRATION_MAX  # mag degration up to MAG_DEGRATION_MAX
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
                + self._fog_weight * max(fog, fog2m)  # Use whatever is higher
                + self._seeing_weight * seeing
                + self._transparency_weight * transparency
                + self._calm_weight * wind_speed_value
            )
            / (
                self._cloudcover_weight
                + self._fog_weight
                + self._seeing_weight
                + self._transparency_weight
                + self._calm_weight
            )
            - precipitation_amount * 100
        )

        # _LOGGER.debug(
        #     f"Cloudcover: {max(cloudcover)}, Fog: {fog}, Seeing: {seeing}, Transparency: {transparency}, Wind speed: {wind_speed_value}"
        # )

        # Ensure condition is within the valid range [0, 1]
        condition = max(0, min(100, condition))

        return int(condition)

    @typechecked
    def _test_data(self, data, keys) -> bool:
        """Test that specific values in a dictionary are not None"""

        if not all(data[key] is not None for key in keys):
            return False
        if not all(data[key] != "NaN" for key in keys):
            return False
        return True

    def _test_weather_df(self) -> None:
        # Check main dataframe for any NaN values
        nan_locations = self._weather_df.isna()

        # Find column names and index positions of NaNs
        result = [
            (index, col)
            for col in nan_locations.columns
            for index in nan_locations.index
            if nan_locations.at[index, col]
        ]

        # Print results
        if result:
            _LOGGER.warning("NaN in main dataframe found at:")
            for index, col in result:
                _LOGGER.warning(f"Column: {col}, Index: {index}")
        else:
            _LOGGER.debug("No NaN values found in main dataframe.")

    # #########################################################################
    # Data for AstroWeather
    # #########################################################################
    @typechecked
    async def _get_location_data(self) -> List[LocationData]:
        """Returns a validated LocationData data object"""

        items = []

        await self._retrive_data()

        now = datetime.now(UTC).replace(tzinfo=None)

        if self._test_datetime is not None:
            await self._astro_routines.need_update()
        else:
            await self._astro_routines.need_update(forecast_time=now)

        forecast_time = now.replace(minute=0, second=0, microsecond=0)
        if self._test_datetime is not None:
            forecast_time = self._test_datetime.replace(minute=0, second=0, microsecond=0)
        _LOGGER.debug("Forecast time: %s", str(forecast_time))

        if len(self._weather_df) == 0:
            _LOGGER.error("Weather data not available")
            return []

        data_index = int((self._weather_df["time"] == now.strftime("%Y-%m-%d %H:00:00+00:00")).idxmax())
        _LOGGER.debug("Data index: %s", str(data_index))

        time_data = TimeDataModel(
            {
                "forecast_time": forecast_time.replace(microsecond=0, tzinfo=timezone.utc),
            }
        )

        try:
            time_data = TimeData(data=time_data)
        except TypeError as ve:
            _LOGGER.error(f"Failed to parse location data model data: {time_data}")
            _LOGGER.error(ve)

        item = LocationDataModel(
            {
                # Time data
                "time_data": time_data,
                # Time shift to UTC
                "time_shift": await self._astro_routines.time_shift(),
                # Remaining forecast data point in met.no data
                "forecast_length": (len(self._weather_df) - data_index),
                # Location
                "location_data": self._location_data,
                # Astronomical routines
                "sun_data": await self._astro_routines.sun_data(),
                "moon_data": await self._astro_routines.moon_data(),
                "darkness_data": await self._astro_routines.darkness_data(),
                "night_duration_astronomical": await self._astro_routines.night_duration_astronomical(),
                "deepsky_forecast": await self._get_deepsky_forecast(),
                "condition_data": await self._get_condition(now),
                # Uptonight objects
                "uptonight": await self._get_deepsky_objects(),
                "uptonight_bodies": await self._get_bodies(),
                "uptonight_comets": await self._get_comets(),
            }
        )

        try:
            items.append(LocationData(data=item))
        except TypeError as ve:
            _LOGGER.error(f"Failed to parse location data model data: {item}")
            _LOGGER.error(ve)

        return items

    @typechecked
    async def _get_forecast_data(self, forecast_type, hours_to_show) -> List[ForecastData]:
        """Return Forecast data for the Station."""

        items = []

        await self._retrive_data()

        now = datetime.now(UTC).replace(tzinfo=None)

        # Create items
        cnt = 0

        forecast_time = now.replace(minute=0, second=0, microsecond=0).replace(microsecond=0, tzinfo=timezone.utc)
        if self._test_datetime is not None:
            forecast_time = self._test_datetime.replace(minute=0, second=0, microsecond=0).replace(
                microsecond=0, tzinfo=timezone.utc
            )
        _LOGGER.debug("Forecast time: %s", str(forecast_time))

        utc_to_local_diff = self._astro_routines.utc_to_local_diff()
        _LOGGER.debug("UTC to local diff: %s", str(utc_to_local_diff))

        if len(self._weather_df) == 0:
            _LOGGER.error("Weather data not available")
            return []

        data_index = int((self._weather_df["time"] == now.strftime("%Y-%m-%d %H:00:00+00:00")).idxmax())
        _LOGGER.debug("Data index: %s", str(data_index))

        for index, row in self._weather_df.iterrows():
            forecast_time = row["time"].replace(microsecond=0, tzinfo=timezone.utc)

            td = TimeDataModel(
                {
                    "forecast_time": forecast_time,  # timestamp
                }
            )

            try:
                time_data = TimeData(data=td)
            except TypeError as ve:
                _LOGGER.error(f"Failed to parse location data model data: {time_data}")
                _LOGGER.error(ve)

            item = ForecastDataModel(
                {
                    "time_data": time_data,  # Time data
                    "hour": row["time"].hour,  # forecast_time.hour % 24,
                    "condition_data": await self._get_condition(row["time"]),
                }
            )

            try:
                items.append(ForecastData(data=item))
            except TypeError as ve:
                _LOGGER.error(f"Failed to parse forecast data: {item}")
                _LOGGER.error(ve)

            cnt += 1
            if cnt >= hours_to_show:
                break

        self._forecast_data = items

        _LOGGER.debug("Forceast Length: %s", str(len(items)))

        return items

    @typechecked
    async def _get_deepsky_forecast(self) -> List[NightlyConditionsData]:
        """Return Deepsky Forecast data."""

        items = []

        if self._forecast_data is None:
            await self._get_forecast_data(FORECAST_TYPE_HOURLY, 72)

        utc_to_local_diff = self._astro_routines.utc_to_local_diff()
        _LOGGER.debug("UTC to local diff: %s", str(utc_to_local_diff))

        # Create forecast
        forecast_dayname = ""
        start_forecast_hour = 0
        start_weather = ""
        interval_points = []
        now = datetime.now(UTC).replace(tzinfo=None)

        if self._test_datetime is not None:
            await self._astro_routines.need_update()
        else:
            await self._astro_routines.need_update(forecast_time=now)

        sun_next_setting = await self._astro_routines.sun_next_setting()
        sun_next_rising = await self._astro_routines.sun_next_rising()
        night_duration_astronomical = await self._astro_routines.night_duration_astronomical()

        start_indexes = []
        # Find start index for two nights and store the indexes
        for index, details_forecast in enumerate(self._forecast_data):
            if details_forecast.forecast_time.hour % 24 == sun_next_rising.hour and len(start_indexes) == 0:
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

                # Calculate Condition
                if len(interval_points) <= int(math.floor(night_duration_astronomical / 3600)):
                    interval_points.append(
                        await self._calc_condition_percentage(
                            cloudcover_high=details_forecast.cloud_area_fraction_high_percentage,
                            cloudcover_medium=details_forecast.cloud_area_fraction_medium_percentage,
                            cloudcover_low=details_forecast.cloud_area_fraction_low_percentage,
                            fog=details_forecast.fog_area_fraction_percentage,
                            fog2m=details_forecast.fog2m_area_fraction_percentage,
                            seeing=details_forecast.seeing,
                            transparency=details_forecast.transparency,
                            wind_speed=details_forecast.wind10m_speed,
                            precipitation_amount=details_forecast.precipitation_amount,
                        )
                    )

                if details_forecast.forecast_time.hour == sun_next_rising.hour or index >= (forecast_data_len - 1):
                    item = NightlyConditionsDataModel(
                        {
                            "dayname": forecast_dayname,
                            "hour": start_forecast_hour,
                            "nightly_conditions": interval_points,
                            "weather": start_weather,
                            "precipitation_amount6": start_precipitation_amount6,
                        }
                    )

                    try:
                        item = NightlyConditionsData(data=item)
                    except TypeError as ve:
                        _LOGGER.error(f"Failed to parse nightly conditions model data: {item}")
                        _LOGGER.error(ve)

                    items.append(item)

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

    # #########################################################################
    # UpTonight
    # #########################################################################
    @typechecked
    async def _retrieve_data_uptonight(self) -> None:
        """Retrieves current data from uptonight"""

        _LOGGER.debug("Updating data from uptonight")

        dataseries_dso = None
        dataseries_bodies = None
        dataseries_comets = None

        if os.path.exists(self._uptonight_path):
            if os.path.isfile(self._uptonight_path + "/uptonight-report.json"):
                # _LOGGER.debug(f"Uptonight report found")
                async with aiofiles.open(self._uptonight_path + "/uptonight-report.json", mode="r") as json_file:
                    contents = await json_file.read()
                dataseries_dso = json.loads(contents)
                _LOGGER.debug("Uptonight DSO imported")
            else:
                _LOGGER.debug(f"File uptonight-report.json not found in {self._uptonight_path}")

            if os.path.isfile(self._uptonight_path + "/uptonight-bodies-report.json"):
                # _LOGGER.debug(f"Uptonight report found")
                async with aiofiles.open(self._uptonight_path + "/uptonight-bodies-report.json", mode="r") as json_file:
                    contents = await json_file.read()
                dataseries_bodies = json.loads(contents)
                _LOGGER.debug("Uptonight Bodies imported")
            else:
                _LOGGER.debug(f"File uptonight-bodies-report.json not found in {self._uptonight_path}")

            if os.path.isfile(self._uptonight_path + "/uptonight-comets-report.json"):
                # _LOGGER.debug(f"Uptonight report found")
                async with aiofiles.open(self._uptonight_path + "/uptonight-comets-report.json", mode="r") as json_file:
                    contents = await json_file.read()
                dataseries_comets = json.loads(contents)
                _LOGGER.debug("Uptonight Comets imported")
            else:
                _LOGGER.debug(f"File uptonight-comets-report.json not found in {self._uptonight_path}")
        else:
            _LOGGER.debug(
                f"Path for UpTonight data not found. Current path: {self._uptonight_path}/uptonight-report.json"
            )

        self._weather_data_uptonight = dataseries_dso
        self._weather_data_uptonight_bodies = dataseries_bodies
        self._weather_data_uptonight_comets = dataseries_comets

    @typechecked
    async def _get_deepsky_objects(self) -> List[UpTonightDSOData]:
        """Return Deepsky Objects for today."""

        items = []

        # Create list of deep sky objects
        if self._weather_data_uptonight is not None:
            dso_id = self._weather_data_uptonight.get("id", {})
            dso_target_name = self._weather_data_uptonight.get("target name", {})
            dso_type = self._weather_data_uptonight.get("type", {})
            dso_constellation = self._weather_data_uptonight.get("constellation", {})
            dso_size = self._weather_data_uptonight.get("size", {})
            dso_visual_magnitude = self._weather_data_uptonight.get("mag", {})
            dso_meridian_transit = self._weather_data_uptonight.get("meridian transit", {})
            dso_meridian_antitransit = self._weather_data_uptonight.get("meridian antitransit", {})
            dso_foto = self._weather_data_uptonight.get("foto", {})

            for row in range(len(dso_target_name)):
                dso_meridian_transit_local = dso_meridian_transit.get(str(row), "")
                if dso_meridian_transit_local != "":
                    dso_meridian_transit_utc = (
                        datetime.strptime(dso_meridian_transit_local, "%m/%d/%Y %H:%M:%S")
                        - timedelta(seconds=await self._astro_routines.time_shift())
                    ).replace(tzinfo=UTC)
                else:
                    dso_meridian_transit_utc = ""

                dso_meridian_antitransit_local = dso_meridian_antitransit.get(str(row), "")
                if dso_meridian_antitransit_local != "":
                    dso_meridian_antitransit_utc = (
                        datetime.strptime(dso_meridian_antitransit_local, "%m/%d/%Y %H:%M:%S")
                        - timedelta(seconds=await self._astro_routines.time_shift())
                    ).replace(tzinfo=UTC)
                else:
                    dso_meridian_antitransit_utc = ""

                item = UpTonightDSODataModel(
                    {
                        "id": dso_id.get(str(row), ""),
                        "target_name": dso_target_name.get(str(row), ""),
                        "type": dso_type.get(str(row), ""),
                        "constellation": dso_constellation.get(str(row), ""),
                        "size": dso_size.get(str(row), 0),
                        "visual_magnitude": dso_visual_magnitude.get(str(row), 0),
                        "meridian_transit": dso_meridian_transit_utc,
                        "meridian_antitransit": dso_meridian_antitransit_utc,
                        "foto": dso_foto.get(str(row), 0),
                    }
                )
                try:
                    items.append(UpTonightDSOData(data=item))
                except TypeError as ve:
                    _LOGGER.error(f"Failed to parse deep sky object data: {item}")
                    _LOGGER.error(ve)

        return items

    @typechecked
    async def _get_bodies(self) -> List[UpTonightBodiesData]:
        """Return Bodies for today."""

        items = []

        # Create list of bodies
        if self._weather_data_uptonight_bodies is not None:
            body_target_name = self._weather_data_uptonight_bodies.get("target name", {})
            body_max_altitude = self._weather_data_uptonight_bodies.get("max altitude", {})
            body_azimuth = self._weather_data_uptonight_bodies.get("azimuth", {})
            body_max_altitude_time = self._weather_data_uptonight_bodies.get("max altitude time", {})
            body_visual_magnitude = self._weather_data_uptonight_bodies.get("visual magnitude", {})
            body_meridian_transit = self._weather_data_uptonight_bodies.get("meridian transit", {})
            body_foto = self._weather_data_uptonight_bodies.get("foto", {})

            for row in range(len(body_target_name)):
                # UpTonight delivers the time in local time zone. here we need it in UTC
                body_max_altitude_time_local = body_max_altitude_time.get(str(row), "")
                if body_max_altitude_time_local != "":
                    body_max_altitude_time_utc = (
                        datetime.strptime(body_max_altitude_time_local, "%m/%d/%Y %H:%M:%S")
                        - timedelta(seconds=await self._astro_routines.time_shift())
                    ).replace(tzinfo=UTC)
                else:
                    body_max_altitude_time_utc = ""

                body_meridian_transit_local = body_meridian_transit.get(str(row), "")
                if body_meridian_transit_local != "":
                    body_meridian_transit_utc = (
                        datetime.strptime(body_meridian_transit_local, "%m/%d/%Y %H:%M:%S")
                        - timedelta(seconds=await self._astro_routines.time_shift())
                    ).replace(tzinfo=UTC)
                else:
                    body_meridian_transit_utc = ""

                item = UpTonightBodiesDataModel(
                    {
                        "target_name": body_target_name.get(str(row), ""),
                        "max_altitude": body_max_altitude.get(str(row), 0),
                        "azimuth": body_azimuth.get(str(row), 0),
                        "max_altitude_time": body_max_altitude_time_utc,
                        "visual_magnitude": body_visual_magnitude.get(str(row), 0),
                        "meridian_transit": body_meridian_transit_utc,
                        "foto": body_foto.get(str(row), 0),
                    }
                )
                try:
                    items.append(UpTonightBodiesData(data=item))
                except TypeError as ve:
                    _LOGGER.error(f"Failed to parse bodies data: {item}")
                    _LOGGER.error(ve)

        return items

    @typechecked
    async def _get_comets(self) -> List[UpTonightCometsData]:
        """Return Comets for today."""

        items = []

        # Create list of comets
        if self._weather_data_uptonight_comets is not None:
            comet_target_name = self._weather_data_uptonight_comets.get("target name", {})
            distance_au_earth = self._weather_data_uptonight_comets.get("distance earth au", {})
            distance_au_sun = self._weather_data_uptonight_comets.get("distance sun au", {})
            absolute_magnitude = self._weather_data_uptonight_comets.get("absolute magnitude", {})
            visual_magnitude = self._weather_data_uptonight_comets.get("visual magnitude", {})
            altitude = self._weather_data_uptonight_comets.get("altitude", {})
            azimuth = self._weather_data_uptonight_comets.get("azimuth", {})
            rise_time = self._weather_data_uptonight_comets.get("rise time", {})
            set_time = self._weather_data_uptonight_comets.get("set time", {})

            for row in range(len(comet_target_name)):
                # UpTonight delivers the time in local time zone. here we need it in UTC
                rise_time_local = rise_time.get(str(row), "")
                if rise_time_local != "":
                    rise_time_local_utc = (
                        datetime.strptime(rise_time_local, "%m/%d/%Y %H:%M:%S")
                        - timedelta(seconds=await self._astro_routines.time_shift())
                    ).replace(tzinfo=UTC)
                else:
                    rise_time_local_utc = ""

                set_time_local = set_time.get(str(row), "")
                if set_time_local != "":
                    set_time_local_utc = (
                        datetime.strptime(set_time_local, "%m/%d/%Y %H:%M:%S")
                        - timedelta(seconds=await self._astro_routines.time_shift())
                    ).replace(tzinfo=UTC)
                else:
                    set_time_local_utc = ""

                item = UpTonightCometsDataModel(
                    {
                        "designation": comet_target_name.get(str(row), ""),
                        "distance_au_earth": distance_au_earth.get(str(row), 0),
                        "distance_au_sun": distance_au_sun.get(str(row), 0),
                        "absolute_magnitude": absolute_magnitude.get(str(row), 0),
                        "visual_magnitude": visual_magnitude.get(str(row), 0),
                        "altitude": altitude.get(str(row), 0),
                        "azimuth": azimuth.get(str(row), 0),
                        "rise_time": rise_time_local_utc,
                        "set_time": set_time_local_utc,
                    }
                )
                try:
                    items.append(UpTonightCometsData(data=item))
                except TypeError as ve:
                    _LOGGER.error(f"Failed to parse comets data: {item}")
                    _LOGGER.error(ve)

        return items

    # #########################################################################
    # 7Timer
    # #########################################################################
    async def _retrieve_data_seventimer(self) -> None:
        """Retrieves current data from 7timer."""

        _LOGGER.debug("Updating data from 7Timer")

        astro_dataseries = {}

        # Testing
        if not self._experimental_features:
            if self._test_mode:
                if os.path.isfile("debug/astro.json"):
                    _LOGGER.debug("Reading 7Timer from file")
                    with open("debug/astro.json") as json_file:
                        astro_dataseries_json = json.load(json_file)
                        astro_dataseries = astro_dataseries_json.get("dataseries", {})
                        json_data_astro = {"init": astro_dataseries_json.get("init")}
                else:
                    json_data_astro = await self._async_request_seventimer()
                    astro_dataseries = json_data_astro.get("dataseries", {})
            else:
                json_data_astro = await self._async_request_seventimer()
                astro_dataseries = json_data_astro.get("dataseries", {})

        if astro_dataseries != {} and not self._experimental_features:
            cnv = ConversionFunctions()
            seventimer_init = await cnv.anchor_timestamp(json_data_astro.get("init"))

            # Flattening the data into a list of records
            records = []
            for entry in astro_dataseries:
                time = (seventimer_init + timedelta(hours=entry["timepoint"])).replace(
                    microsecond=0, tzinfo=timezone.utc
                )
                instant_details = {}
                instant_details["seeing"] = SEEING[max(0, min(7, int(entry["seeing"] - 1)))]
                instant_details["transparency"] = TRANSPARENCY[max(0, min(7, int(entry["transparency"] - 1)))]
                instant_details["lifted_index"] = LIFTED_INDEX_7TIMER_MAPPING[entry["lifted_index"]]

                # Adding all details to a single record
                record = {
                    "time": time,
                    **instant_details,
                }
                records.append(record)

            # Convert to DataFrame
            weather_df_seventimer = pd.DataFrame(records)
        else:
            # Fake 7timer weather data if service is broken
            # This eliminates consideration of seeing, transparency, and lifted_index
            # and switches automatically to experimental functions.
            records = []
            now = datetime.now(UTC)

            for index in range(0, 20):
                time = (now + timedelta(hours=index * 3)).replace(
                    minute=0, second=0, microsecond=0, tzinfo=timezone.utc
                )
                instant_details = {}
                instant_details["seeing"] = _NOT_AVAILABLE
                instant_details["transparency"] = _NOT_AVAILABLE
                instant_details["lifted_index"] = _NOT_AVAILABLE

                # Adding all details to a single record
                record = {
                    "time": time,
                    **instant_details,
                }
                records.append(record)

            # Convert to DataFrame
            weather_df_seventimer = pd.DataFrame(records)

        return weather_df_seventimer

    @typechecked
    async def _async_request_seventimer(self) -> Dict:
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
            + str("%.1f" % round(self._location_data.longitude, 2))
            + "&lat="
            + str("%.1f" % round(self._location_data.latitude, 2))
            + "&product=astro"
            + "&output=json"
        )
        try:
            _LOGGER.debug(f"Query url: {url}")
            async with session.request("get", url, headers=HEADERS, ssl=False) as resp:
                resp.raise_for_status()
                plain = str(await resp.text()).replace("\n", " ")
                data = json.loads(plain)

                if self._test_mode:
                    json_string = json.dumps(data)
                    with open("debug/astro.json", "w") as outfile:
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

    # #########################################################################
    # Met.no
    # #########################################################################
    async def _retrieve_data_metno(self) -> None:
        """Retrieves current data from met."""

        _LOGGER.debug("Updating data from Met.no")

        dataseries = None

        # Testing
        if self._test_mode:
            if os.path.isfile("debug/met.json"):
                _LOGGER.debug("Reading Met.no data from file")
                with open("debug/met.json") as json_file:
                    dataseries = json.load(json_file).get("properties", {}).get("timeseries")
            else:
                json_data_metno = await self._async_request_met()
                dataseries = json_data_metno.get("properties", {}).get("timeseries")
        else:
            json_data_metno = await self._async_request_met()
            dataseries = json_data_metno.get("properties", {}).get("timeseries")

        # Flattening the data into a list of records
        records = []
        if dataseries is not None:
            for entry in dataseries:
                time = datetime.strptime(entry["time"], "%Y-%m-%dT%H:%M:%SZ").replace(
                    microsecond=0, tzinfo=timezone.utc
                )
                instant_details = entry["data"]["instant"]["details"]
                next_1h_symbol_code = entry["data"].get("next_1_hours", {}).get("summary", {}).get("symbol_code", None)
                next_6h_symbol_code = entry["data"].get("next_6_hours", {}).get("summary", {}).get("symbol_code", None)
                next_1h_precipitation_amount = (
                    entry["data"].get("next_1_hours", {}).get("details", {}).get("precipitation_amount", None)
                )
                next_6h_precipitation_amount = (
                    entry["data"].get("next_6_hours", {}).get("details", {}).get("precipitation_amount", None)
                )

                # Adding all details to a single record
                record = {
                    "time": time,
                    **instant_details,
                    "next_1h_symbol_code": next_1h_symbol_code,
                    "next_6h_symbol_code": next_6h_symbol_code,
                    "next_1h_precipitation_amount": next_1h_precipitation_amount,
                    "next_6h_precipitation_amount": next_6h_precipitation_amount,
                }
                records.append(record)

            # Convert to DataFrame
            weather_df_metno = pd.DataFrame(records)

            return weather_df_metno
        else:
            return None

    @typechecked
    async def _async_request_met(self) -> Dict:
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
            + str("%.1f" % round(self._location_data.longitude, 2))
            + "&lat="
            + str("%.1f" % round(self._location_data.latitude, 2))
            + "&altitude="
            + str(int(self._location_data.elevation))
        )

        try:
            _LOGGER.debug(f"Query url: {url}")
            async with session.request("get", url, headers=HEADERS) as resp:
                resp.raise_for_status()
                # plain = str(await resp.text()).replace("\n", " ")
                # data = json.loads(plain)
                data = await resp.json()

                if self._test_mode:
                    json_string = json.dumps(data)
                    with open("debug/met.json", "w") as outfile:
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

    # #########################################################################
    # Openmeteo
    # #########################################################################
    async def _retrieve_data_openmeteo(self) -> None:
        """Retrieves current data from openmeteo."""

        _LOGGER.debug("Updating data from Open-Meteo")

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        params = {
            "latitude": self._location_data.latitude,
            "longitude": self._location_data.longitude,
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "dew_point_2m",
                "precipitation",
                "cloud_cover",
                "cloud_cover_low",
                "cloud_cover_mid",
                "cloud_cover_high",
                "wind_speed_10m",
                "wind_direction_10m",
            ],
            "timezone": "UTC",
            # "temperature_unit": "C",
            "precipitation_unit": "mm",
            "wind_speed_unit": "ms",
            "models": self._forecast_model,
        }

        try:
            _LOGGER.debug(f"Query url: {BASE_URL_OPENMETEO}")

            # async with asyncio.timeout(self.request_timeout):
            response = await session.get(BASE_URL_OPENMETEO, params=params)
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to the Open-Meteo API"
            raise OpenMeteoConnectionError(msg) from exception
        except (
            ClientError,
            ClientResponseError,
            socket.gaierror,
        ) as exception:
            msg = "Error occurred while communicating with Open-Meteo API"
            raise OpenMeteoConnectionError(msg) from exception
        finally:
            if not use_running_session:
                await session.close()

        content_type = response.headers.get("Content-Type", "")

        # Did we get a 4xx or 5xx?
        if (response.status // 100) in [4, 5]:
            if "application/json" in content_type:
                data = await response.json()
                response.close()
                if data.get("error") is True and (reason := data.get("reason")):
                    raise OpenMeteoError(reason)
                raise OpenMeteoError(response.status, data)
            contents = await response.read()
            response.close()
            raise OpenMeteoError(response.status, {"message": contents.decode("utf8")})

        text = await response.text()
        if "application/json" not in content_type:
            msg = "Unexpected response from the Open-Meteo API"
            raise OpenMeteoError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        # Process hourly data
        data = await response.json()
        if self._test_mode:
            json_string = json.dumps(data)
            with open("debug/openmeteo.json", "w") as outfile:
                outfile.write(json_string)

        response.close()
        hourly = data.get("hourly")

        hourly_data = {
            "time": np.array(hourly.get("time")),
            "openmeteo_temperature_2m": np.array(hourly.get("temperature_2m")),
            "openmeteo_relative_humidity_2m": np.array(hourly.get("relative_humidity_2m")),
            "openmeteo_dew_point_2m": np.array(hourly.get("dew_point_2m")),
            "openmeteo_precipitation": np.array(hourly.get("precipitation")),
            "openmeteo_cloud_cover": np.array(hourly.get("cloud_cover")),
            "openmeteo_cloud_cover_low": np.array(hourly.get("cloud_cover_low")),
            "openmeteo_cloud_cover_mid": np.array(hourly.get("cloud_cover_mid")),
            "openmeteo_cloud_cover_high": np.array(hourly.get("cloud_cover_high")),
            "openmeteo_wind_speed_10m": np.array(hourly.get("wind_speed_10m")),
            "openmeteo_wind_direction_10m": np.array(hourly.get("wind_direction_10m")),
        }

        weather_df_openmeteo = pd.DataFrame(data=hourly_data)
        weather_df_openmeteo["time"] = pd.to_datetime(weather_df_openmeteo["time"])
        weather_df_openmeteo["time"] = weather_df_openmeteo["time"].dt.tz_localize("UTC")

        return weather_df_openmeteo
