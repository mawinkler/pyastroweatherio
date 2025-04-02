#!/usr/bin/env python3
"""The test for the API"""

from unittest import TestCase

import asyncio
import logging
import os
import time
from datetime import datetime
from tabulate import tabulate

import pytz

from pyastroweatherio import (
    AstroWeather,
    AstroWeatherError,
)

_LOGGER = logging.getLogger(__name__)

COLOR_BLACK = "1;30"
COLOR_RED = "1;31"
COLOR_GREEN = "1;32"
COLOR_BROWN = "1;33"
COLOR_BLUE = "1;34"
COLOR_PURPLE = "1;35"
COLOR_CYAN = "1;36"

# # ITV
# latitude = 50.429
# longitude = 9.181
# elevation = 357
# timezone_info = "Europe/Berlin"

# # Peißenberg
# latitude = 48.811
# longitude = 11.017
# elevation = 977
# timezone_info = "Europe/Berlin"

LOCATIONS = [
    {
        # Backyard
        "latitude": float(os.environ["BACKYARD_LATITUDE"]),
        "longitude": float(os.environ["BACKYARD_LONGITUDE"]),
        "elevation": int(os.environ["BACKYARD_ELEVATION"]),
        "timezone_info": os.environ["BACKYARD_TIMEZONE"],
    },
    # {
    #     # Santiago
    #     "latitude": -33.46,
    #     "longitude": -70.65,
    #     "elevation": 556,
    #     "timezone_info": "America/Santiago",
    # },
    # {
    #     # Anchorage
    #     "latitude": 61.212,
    #     "longitude": -149.737,
    #     "elevation": 115,
    #     "timezone_info": "America/Anchorage",
    # },
    # {
    #     # Hacienda Los Andes
    #     "latitude": -30.29528,
    #     "longitude": -70.71262,
    #     "elevation": 1000,
    #     "timezone_info": "Chile/Continental",
    # },
    # {
    #     # London
    #     "latitude": 51.5072,
    #     "longitude": 0.1276,
    #     "elevation": 11,
    #     "timezone_info": "Europe/London",
    # },
    # {
    #     # Sydney
    #     "latitude": -33.869,
    #     "longitude": 151.198,
    #     "elevation": 3,
    #     "timezone_info": "Australia/Sydney",
    # },
    # {
    #     # Helsinki
    #     "latitude": 65.064717,
    #     "longitude": 25.553043,
    #     "elevation": 12,
    #     "timezone_info": "Europe/Helsinki",
    # },
    {
        # North
        "latitude": 85,
        "longitude": 11,
        "elevation": 12,
        "timezone_info": "Europe/Helsinki",
    },
    {
        # South
        "latitude": -85,
        "longitude": 11,
        "elevation": 12,
        "timezone_info": "Europe/Berlin",
    },
]


def esc(code):
    return f"\033[{code}m"


class AstroWeatherIOTestCase(TestCase):
    def setup(self):
        return None

    def test_hourly_forecast(self):
        asyncio.run(self.hourly_forecast(idx=0))

    def test_deepsky_forecast(self):
        asyncio.run(self.deepsky_forecast(idx=0))

    def test_location_data(self):
        asyncio.run(self.location_data(idx=0))

    async def hourly_forecast(self, idx) -> None:
        """Create the aiohttp session and run the example."""
        logging.basicConfig(level=logging.DEBUG)

        print(
            f"\n{esc(COLOR_BLUE)}--------------------------------------------------------"
            + f"---------------------------------------------------------------{esc('0')}"
        )
        print(f"{esc(COLOR_RED)}Date & Time: {esc(COLOR_GREEN)}{str(datetime.now())}, ")
        print(
            f"{esc(COLOR_BLUE)}--------------------------------------------------------"
            + f"---------------------------------------------------------------{esc('0')}"
        )

        astroweather = AstroWeather(
            latitude=LOCATIONS[idx]["latitude"],
            longitude=LOCATIONS[idx]["longitude"],
            elevation=LOCATIONS[idx]["elevation"],
            timezone_info=LOCATIONS[idx]["timezone_info"],
            cloudcover_weight=3,
            cloudcover_high_weakening=0.5,
            cloudcover_medium_weakening=0.75,
            cloudcover_low_weakening=0.75,
            fog_weight=3,
            seeing_weight=2,
            transparency_weight=1,
            calm_weight=2,
            uptonight_path=".",
            # test_datetime=datetime.strptime("2024-11-19T07:00:00Z", "%Y-%m-%dT%H:%M:%SZ"),
            experimental_features=True,
            forecast_model="icon_seamless",
        )

        start = time.time()

        try:
            data = await astroweather.get_hourly_forecast()

            headers = [
                "forecast_time",
                "cloudcover",
                "cloudless",
                "clouds",
                "high",
                "medium",
                "low",
                "fog",
                "fog2m",
                "precipitation",
                "wind_direction",
                "wind_speed",
                "calm",
                "temp2m",
                "rh2m",
                "dewpoint2m",
                "condition",
                "seeing",
                "transparency",
                "lifted_index",
                "weather",
                "weather6",
            ]
            rows = [
                [
                    obj.forecast_time,
                    obj.cloudcover_percentage,
                    obj.cloudless_percentage,
                    obj.cloud_area_fraction_percentage,
                    obj.cloud_area_fraction_high_percentage,
                    obj.cloud_area_fraction_medium_percentage,
                    obj.cloud_area_fraction_low_percentage,
                    obj.fog_area_fraction_percentage,
                    obj.fog2m_area_fraction_percentage,
                    obj.precipitation_amount,
                    obj.wind10m_direction,
                    obj.wind10m_speed,
                    obj.calm_percentage,
                    obj.temp2m,
                    obj.rh2m,
                    obj.dewpoint2m,
                    obj.condition_percentage,
                    obj.seeing_percentage,
                    obj.transparency_percentage,
                    obj.lifted_index,
                    obj.weather,
                    obj.weather6,
                ]
                for obj in data
            ]
            print(f"{esc(COLOR_BLUE)}" + f"{tabulate(rows, headers=headers)}" + f"{esc('0')}\n")

        except AstroWeatherError as err:
            print(err)

        end = time.time()

        print(f"Execution time: {end - start} seconds")

        return None

    async def deepsky_forecast(self, idx) -> None:
        """Create the aiohttp session and run the example."""
        logging.basicConfig(level=logging.DEBUG)

        print(
            f"\n{esc(COLOR_BLUE)}--------------------------------------------------------"
            + f"---------------------------------------------------------------{esc('0')}"
        )
        print(f"{esc(COLOR_RED)}Date & Time: {esc(COLOR_GREEN)}{str(datetime.now())}, ")
        print(
            f"{esc(COLOR_BLUE)}--------------------------------------------------------"
            + f"---------------------------------------------------------------{esc('0')}"
        )

        astroweather = AstroWeather(
            latitude=LOCATIONS[idx]["latitude"],
            longitude=LOCATIONS[idx]["longitude"],
            elevation=LOCATIONS[idx]["elevation"],
            timezone_info=LOCATIONS[idx]["timezone_info"],
            cloudcover_weight=3,
            cloudcover_high_weakening=0.5,
            cloudcover_medium_weakening=0.75,
            cloudcover_low_weakening=0.75,
            fog_weight=3,
            seeing_weight=2,
            transparency_weight=1,
            calm_weight=2,
            uptonight_path=".",
            # test_datetime=datetime.strptime("2024-11-19T07:00:00Z", "%Y-%m-%dT%H:%M:%SZ"),
            experimental_features=True,
            forecast_model="icon_seamless",
        )

        start = time.time()

        try:
            data = await astroweather.get_deepsky_forecast()

            headers = [
                "hour",
                "nightly_conditions",
                "weather",
                "precipitation_amount6",
            ]
            rows = [
                [
                    obj.hour,
                    obj.nightly_conditions,
                    obj.weather,
                    obj.precipitation_amount6,
                ]
                for obj in data
            ]
            print(f"{esc(COLOR_BLUE)}" + f"{tabulate(rows, headers=headers)}" + f"{esc('0')}\n")

        except AstroWeatherError as err:
            print(err)

        end = time.time()

        print(f"Execution time: {end - start} seconds")

        return None

    async def location_data(self, idx) -> None:
        """Create the aiohttp session and run the example."""
        logging.basicConfig(level=logging.DEBUG)

        print(
            f"\n{esc(COLOR_BLUE)}--------------------------------------------------------"
            + f"---------------------------------------------------------------{esc('0')}"
        )
        print(f"{esc(COLOR_RED)}Date & Time: {esc(COLOR_GREEN)}{str(datetime.now())}, ")
        print(
            f"{esc(COLOR_BLUE)}--------------------------------------------------------"
            + f"---------------------------------------------------------------{esc('0')}"
        )

        astroweather = AstroWeather(
            latitude=LOCATIONS[idx]["latitude"],
            longitude=LOCATIONS[idx]["longitude"],
            elevation=LOCATIONS[idx]["elevation"],
            timezone_info=LOCATIONS[idx]["timezone_info"],
            cloudcover_weight=3,
            cloudcover_high_weakening=0.5,
            cloudcover_medium_weakening=0.75,
            cloudcover_low_weakening=0.75,
            fog_weight=3,
            seeing_weight=2,
            transparency_weight=1,
            calm_weight=2,
            uptonight_path=".",
            # test_datetime=datetime.strptime("2024-11-19T07:00:00Z", "%Y-%m-%dT%H:%M:%SZ"),
            experimental_features=True,
            forecast_model="icon_seamless",
        )

        start = time.time()

        try:
            data = await astroweather.get_location_data()

            print("Location:")
            headers = [
                "forecast_time",
                "forecast_length",
                "time_shift",
                "latitude",
                "longitude",
                "elevation",
            ]
            rows = [
                [
                    obj.forecast_time.strftime("%Y-%m-%d %H:%M"),
                    obj.forecast_length,
                    obj.time_shift,
                    obj.latitude,
                    obj.longitude,
                    obj.elevation,
                ]
                for obj in data
            ]
            print(f"{esc(COLOR_BLUE)}" + f"{tabulate(rows, headers=headers)}" + f"{esc('0')}\n")

            print("Clouds:")
            headers = [
                "condition",
                "condition_plain",
                "cloudcover",
                "cloudless",
                "clouds",
                "high",
                "medium",
                "low",
                "fog",
                "fog2m",
            ]
            rows = [
                [
                    obj.condition_percentage,
                    obj.condition_plain,
                    obj.cloudcover_percentage,
                    obj.cloudless_percentage,
                    obj.cloud_area_fraction_percentage,
                    obj.cloud_area_fraction_high_percentage,
                    obj.cloud_area_fraction_medium_percentage,
                    obj.cloud_area_fraction_low_percentage,
                    obj.fog_area_fraction_percentage,
                    obj.fog2m_area_fraction_percentage,
                ]
                for obj in data
            ]
            print(f"{esc(COLOR_BLUE)}" + f"{tabulate(rows, headers=headers)}" + f"{esc('0')}\n")

            print("Atmosphere:")
            headers = [
                "seeing",
                "transparency",
                "lifted_index",
                "lifted_index_plain",
                "wind",
                "temp",
                "rh",
                "dewpoint",
                "weather",
            ]
            rows = [
                [
                    (obj.seeing, obj.seeing_percentage),
                    (obj.transparency, obj.transparency_percentage),
                    obj.lifted_index,
                    obj.lifted_index_plain,
                    (obj.wind10m_speed_plain, obj.wind10m_direction, obj.wind10m_speed),
                    obj.temp2m,
                    obj.rh2m,
                    obj.dewpoint2m,
                    obj.weather,
                ]
                for obj in data
            ]
            print(f"{esc(COLOR_BLUE)}" + f"{tabulate(rows, headers=headers)}" + f"{esc('0')}\n")

            print("During the night:")
            headers = [
                "view",
                "1",
                "1_dayname",
                "1_desc",
                "1_plain",
                "2",
                "2_dayname",
                "2_desc",
                "2_plain",
                "moon_rises",
                "moon_sets",
                "moon_down",
                "moon_up",
                "duration",
                "darkness",
            ]
            rows = [
                [
                    obj.deep_sky_view,
                    obj.deepsky_forecast_today,
                    obj.deepsky_forecast_today_dayname,
                    obj.deepsky_forecast_today_desc,
                    obj.deepsky_forecast_today_plain,
                    obj.deepsky_forecast_tomorrow,
                    obj.deepsky_forecast_tomorrow_dayname,
                    obj.deepsky_forecast_tomorrow_desc,
                    obj.deepsky_forecast_tomorrow_plain,
                    obj.deep_sky_darkness_moon_rises,
                    obj.deep_sky_darkness_moon_sets,
                    obj.deep_sky_darkness_moon_always_down,
                    obj.deep_sky_darkness_moon_always_up,
                    str(round(obj.night_duration_astronomical / 3600, 2)),
                    str(round(obj.deep_sky_darkness / 3600, 2)),
                ]
                for obj in data
            ]
            print(f"{esc(COLOR_BLUE)}" + f"{tabulate(rows, headers=headers)}" + f"{esc('0')}\n")

            print("Sun:")
            headers = [
                "altitude",
                "azimuth",
                "next_rising",
                "next_rising_nautical",
                "next_rising_astro",
                "next_setting",
                "next_setting_nautical",
                "next_setting_astro",
                "constellation",
            ]
            rows = [
                [
                    obj.sun_altitude,
                    obj.sun_azimuth,
                    obj.sun_next_rising.strftime("%Y-%m-%d %H:%M"),
                    obj.sun_next_rising_nautical.strftime("%Y-%m-%d %H:%M"),
                    obj.sun_next_rising_astro.strftime("%Y-%m-%d %H:%M"),
                    obj.sun_next_setting.strftime("%Y-%m-%d %H:%M"),
                    obj.sun_next_setting_nautical.strftime("%Y-%m-%d %H:%M"),
                    obj.sun_next_setting_astro.strftime("%Y-%m-%d %H:%M"),
                    obj.sun_constellation,
                ]
                for obj in data
            ]
            print(f"{esc(COLOR_BLUE)}" + f"{tabulate(rows, headers=headers)}" + f"{esc('0')}\n")

            print("Moon:")
            headers = [
                "altitude",
                "azimuth",
                "phase",
                "icon",
                "next_rising",
                "next_setting",
                "next_new_moon",
                "next_full_moon",
                "distance_km",
                "angular_size",
                "relative_distance",
                "relative_size",
                "constellation",
                "next_dark_night",
            ]
            rows = [
                [
                    obj.moon_altitude,
                    obj.moon_azimuth,
                    obj.moon_phase,
                    obj.moon_icon,
                    obj.moon_next_rising.strftime("%Y-%m-%d %H:%M"),
                    obj.moon_next_setting.strftime("%Y-%m-%d %H:%M"),
                    obj.moon_next_new_moon.strftime("%Y-%m-%d %H:%M"),
                    obj.moon_next_full_moon.strftime("%Y-%m-%d %H:%M"),
                    obj.moon_distance_km,
                    obj.moon_angular_size,
                    obj.moon_relative_distance,
                    obj.moon_relative_size,
                    obj.moon_constellation,
                    obj.moon_next_dark_night.strftime("%Y-%m-%d %H:%M"),
                ]
                for obj in data
            ]
            print(f"{esc(COLOR_BLUE)}" + f"{tabulate(rows, headers=headers)}" + f"{esc('0')}\n")

            print("UpTonight:")
            headers = [
                "dsos",
                "name",
                "bodies",
                "name",
                "comets",
                "designation",
            ]
            rows = [
                [
                    obj.uptonight,
                    obj.uptonight_list[0].target_name,
                    obj.uptonight_bodies,
                    obj.uptonight_bodies_list[0].target_name,
                    obj.uptonight_comets,
                    obj.uptonight_comets_list[0].designation,
                ]
                for obj in data
            ]
            print(f"{esc(COLOR_BLUE)}" + f"{tabulate(rows, headers=headers)}" + f"{esc('0')}\n")

        except AstroWeatherError as err:
            print(err)

        end = time.time()

        print(f"Execution time: {end - start} seconds")

        return None
