""" The test for the API """
import asyncio
import pprint
import logging
import time
import os
from datetime import datetime
import pytz

from pyastroweatherio import (
    AstroWeather,
    AstroWeatherError,
)

_LOGGER = logging.getLogger(__name__)


pp = pprint.PrettyPrinter()
COLOR_BLACK = "1;30"
COLOR_RED = "1;31"
COLOR_GREEN = "1;32"
COLOR_BROWN = "1;33"
COLOR_BLUE = "1;34"
COLOR_PURPLE = "1;35"
COLOR_CYAN = "1;36"

# Backyard
latitude = float(os.environ["BACKYARD_LATITUDE"])
longitude = float(os.environ["BACKYARD_LONGITUDE"])
elevation = int(os.environ["BACKYARD_ELEVATION"])
timezone_info = os.environ["BACKYARD_TIMEZONE"]

# Peißenberg
# latitude=48.811
# longitude=11.017
# elevation=977
# timezone_info = "Europe/Berlin"

# Anchorage
# latitude=61.212
# longitude=-149.737
# elevation=115
# timezone_info = "America/Anchorage"

# Miami
# latitude=25.76322
# longitude=-80.19856
# elevation=0
# timezone_info = "America/Cancun"

# London
# latitude=51.5072
# longitude=0.1276
# elevation=11
# timezone_info = "Europe/London"

# Sydney
# latitude=-33.869
# longitude=151.198
# elevation=3
# timezone_info = "Australia/Sydney"


def esc(code):
    return f"\033[{code}m"


def utc_to_local(utc_dt):
    """Localizes the datetime"""
    local_tz = pytz.timezone(timezone_info)
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)


def convert_to_hhmm(sec):
    sec = sec % (24 * 3600)
    hour = sec // 3600
    sec %= 3600
    min = sec // 60
    sec %= 60
    #    return "%02d:%02d:%02d" % (hour, min, sec)
    return "%02d:%02d" % (hour, min)


async def main() -> None:
    """Create the aiohttp session and run the example."""
    logging.basicConfig(level=logging.DEBUG)

    print(
        f"{esc(COLOR_BLUE)}--------------------------------------------------------"
        + f"---------------------------------------------------------------{esc('0')}"
    )
    print(f"{esc(COLOR_RED)}Date & Time: {esc(COLOR_GREEN)}{str(datetime.now())}, ")
    print(
        f"{esc(COLOR_BLUE)}--------------------------------------------------------"
        + f"---------------------------------------------------------------{esc('0')}"
    )

    astroweather = AstroWeather(
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        timezone_info=timezone_info,
        cloudcover_weight=3,
        seeing_weight=2,
        transparency_weight=1,
        uptonight_path=".",
    )

    start = time.time()

    test_hourly_forecast = True
    test_deepsky_forecast = True
    test_location_data = True
    try:
        if test_hourly_forecast:
            data = await astroweather.get_hourly_forecast()

            f = open("debug/test_client_hourly_forecast.csv", "w")

            f.write(
                "Init;Timepoint;Timestamp;Hour of Day;Cloudcover;Cloudless;Seeing;Transparency;Liftet Index;Cloud Area Fraction;Cloud Area Fraction High;Cloud Area Fraction Low;Cloud Area Fraction Medium;View Condition;Wind Direction;Speed;Temperature;Rel Humidity;Dew Point;Weather;Weather 6;Precipitation amount\n"
            )

            for row in data:
                print(
                    f"{esc(COLOR_BLUE)}--------------------------------------------------------"
                    + f"---------------------------------------------------------------{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Seventimer Init: {esc(COLOR_GREEN)}{str(row.seventimer_init)}, "
                    + f"{esc(COLOR_RED)}Seventimer Timepoint: {esc(COLOR_GREEN)}{str(row.seventimer_timepoint)}, "
                    + f"{esc(COLOR_RED)}Forecast Time: {esc(COLOR_GREEN)}{str(row.forecast_time)}, "
                    + f"{esc(COLOR_RED)}Hour of Day: {esc(COLOR_GREEN)}{str(row.hour)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Cloudcover: {esc(COLOR_GREEN)}{str(row.cloudcover_percentage)}, "
                    + f"{esc(COLOR_RED)}Cloudless: {esc(COLOR_GREEN)}{str(row.cloudless_percentage)}, "
                    + f"{esc(COLOR_RED)}Seeing: {esc(COLOR_GREEN)}{str(row.seeing_percentage)}, "
                    + f"{esc(COLOR_RED)}Transparency: {esc(COLOR_GREEN)}{str(row.transparency_percentage)}, "
                    + f"{esc(COLOR_RED)}Liftet Index: {esc(COLOR_GREEN)}{str(row.lifted_index)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Cloud Area Fraction: {esc(COLOR_GREEN)}{str(row.cloud_area_fraction_percentage)}, "
                    + f"{esc(COLOR_RED)}Cloud Area Fraction High: {esc(COLOR_GREEN)}{str(row.cloud_area_fraction_high_percentage)}, "
                    + f"{esc(COLOR_RED)}Cloud Area Fraction Low: {esc(COLOR_GREEN)}{str(row.cloud_area_fraction_low_percentage)}, "
                    + f"{esc(COLOR_RED)}Cloud Area Fraction Medium: {esc(COLOR_GREEN)}{str(row.cloud_area_fraction_medium_percentage)}{esc('0')}"
                )
                print(f"{esc(COLOR_RED)}View Condition: {esc(COLOR_GREEN)}{str(row.condition_percentage)}{esc('0')}")
                print(
                    f"{esc(COLOR_RED)}Wind Direction: {esc(COLOR_GREEN)}{str(row.wind10m_direction)}, "
                    + f"{esc(COLOR_RED)}Speed: {esc(COLOR_GREEN)}{str(row.wind10m_speed)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Temperature: {esc(COLOR_GREEN)}{str(row.temp2m)}, "
                    + f"{esc(COLOR_RED)}Rel Humidity: {esc(COLOR_GREEN)}{str(row.rh2m)}, "
                    + f"{esc(COLOR_RED)}Dew Point: {esc(COLOR_GREEN)}{str(row.dewpoint2m)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Weather: {esc(COLOR_GREEN)}{str(row.weather)}, "
                    + f"{esc(COLOR_RED)}Weather 6: {esc(COLOR_GREEN)}{str(row.weather6)}, "
                    + f"{esc(COLOR_RED)}Precipitation amount: {esc(COLOR_GREEN)}{str(row.precipitation_amount)}{esc('0')}"
                )

                f.write(
                    str(row.seventimer_init)
                    + ";"
                    + str(row.seventimer_timepoint)
                    + ";"
                    + str(row.forecast_time)
                    + ";"
                    + str(row.hour)
                    + ";"
                    + str(row.cloudcover_percentage)
                    + ";"
                    + str(row.cloudless_percentage)
                    + ";"
                    + str(row.seeing)
                    + ";"
                    + str(row.transparency)
                    + ";"
                    + str(row.lifted_index)
                    + ";"
                    + str(row.cloud_area_fraction_percentage)
                    + ";"
                    + str(row.cloud_area_fraction_high_percentage)
                    + ";"
                    + str(row.cloud_area_fraction_low_percentage)
                    + ";"
                    + str(row.cloud_area_fraction_medium_percentage)
                    + ";"
                    + str(row.condition_percentage)
                    + ";"
                    + str(row.wind10m_direction)
                    + ";"
                    + str(row.wind10m_speed)
                    + ";"
                    + str(row.temp2m)
                    + ";"
                    + str(row.rh2m)
                    + ";"
                    + str(row.dewpoint2m)
                    + ";"
                    + str(row.weather)
                    + ";"
                    + str(row.weather6)
                    + ";"
                    + str(row.precipitation_amount)
                    + "\n"
                )

            f.close()

        if test_deepsky_forecast:
            data = await astroweather.get_deepsky_forecast()

            f = open("debug/test_client_deepsky_forecast.csv", "w")

            f.write("Init;Hour of Day;Nightly conditions;Weather\n")

            for row in data:
                print(
                    f"{esc(COLOR_BLUE)}--------------------------------------------------------"
                    + f"---------------------------------------------------------------{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Seventimer Init: {esc(COLOR_GREEN)}{str(row.seventimer_init)}, "
                    + f"{esc(COLOR_RED)}Hour of day: {esc(COLOR_GREEN)}{str(row.hour)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Nightly conditions: {esc(COLOR_GREEN)}{str(row.nightly_conditions)}, "
                    + f"{esc(COLOR_RED)}Weather: {esc(COLOR_GREEN)}{str(row.weather)}{esc('0')}"
                )

                f.write(
                    str(row.seventimer_init)
                    + ";"
                    + str(row.hour)
                    + ";"
                    + str(row.nightly_conditions)
                    + ";"
                    + str(row.weather)
                    + "\n"
                )

            f.close()

        if test_location_data:
            data = await astroweather.get_location_data()
            for row in data:
                print(
                    f"{esc(COLOR_BLUE)}--------------------------------------------------------"
                    + f"---------------------------------------------------------------{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Seventimer Init: {esc(COLOR_GREEN)}{str(row.seventimer_init)}, "
                    + f"{esc(COLOR_RED)}Seventimer Timepoint: {esc(COLOR_GREEN)}{str(row.seventimer_timepoint)}, "
                    + f"{esc(COLOR_RED)}Forecast Time: {esc(COLOR_GREEN)}{str(row.forecast_time)}, "
                    + f"{esc(COLOR_RED)}Forecast Length: {esc(COLOR_GREEN)}{str(row.forecast_length)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Latitude: {esc(COLOR_GREEN)}{str(row.latitude)}, "
                    + f"{esc(COLOR_RED)}Longitude: {esc(COLOR_GREEN)}{str(row.longitude)}, "
                    + f"{esc(COLOR_RED)}Elevation: {esc(COLOR_GREEN)}{str(row.elevation)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}View Condition: {esc(COLOR_GREEN)}{str(row.condition_percentage)}, "
                    + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.condition_plain)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Cloudcover: {esc(COLOR_GREEN)}{str(row.cloudcover_percentage)}, "
                    + f"{esc(COLOR_RED)}Cloudless: {esc(COLOR_GREEN)}{str(row.cloudless_percentage)}, "
                    + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.cloudcover_plain)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Cloud Area Fraction: {esc(COLOR_GREEN)}{str(row.cloud_area_fraction_percentage)}, "
                    + f"{esc(COLOR_RED)}Cloud Area Fraction High: {esc(COLOR_GREEN)}{str(row.cloud_area_fraction_high_percentage)}, "
                    + f"{esc(COLOR_RED)}Cloud Area Fraction Low: {esc(COLOR_GREEN)}{str(row.cloud_area_fraction_low_percentage)}, "
                    + f"{esc(COLOR_RED)}Cloud Area Fraction Medium: {esc(COLOR_GREEN)}{str(row.cloud_area_fraction_medium_percentage)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Seeing: {esc(COLOR_GREEN)}{str(row.seeing_percentage)}, "
                    + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.seeing_plain)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Transparency: {esc(COLOR_GREEN)}{str(row.transparency_percentage)}, "
                    + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.transparency_plain)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Lifted Index: {esc(COLOR_GREEN)}{str(row.lifted_index)}, "
                    + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.lifted_index_plain)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Wind Direction: {esc(COLOR_GREEN)}{str(row.wind10m_direction)}, "
                    + f"{esc(COLOR_RED)}Speed: {esc(COLOR_GREEN)}{str(row.wind10m_speed)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Temperature: {esc(COLOR_GREEN)}{str(row.temp2m)}, "
                    + f"{esc(COLOR_RED)}Rel Humidity: {esc(COLOR_GREEN)}{str(row.rh2m)}, "
                    + f"{esc(COLOR_RED)}Dew Point: {esc(COLOR_GREEN)}{str(row.dewpoint2m)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}View Condition: {esc(COLOR_GREEN)}{str(row.condition_percentage)}, "
                    + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.condition_plain)}, "
                    + f"{esc(COLOR_RED)}Weather: {esc(COLOR_GREEN)}{str(row.weather)}, "
                    + f"{esc(COLOR_RED)}Deep Sky View: {esc(COLOR_GREEN)}{str(row.deep_sky_view)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Moon Phase: {esc(COLOR_GREEN)}{str(row.moon_phase)}, "
                    + f"{esc(COLOR_RED)}Moon Altitude: {esc(COLOR_GREEN)}{str(row.moon_altitude)}, "
                    + f"{esc(COLOR_RED)}Moon Azimuth: {esc(COLOR_GREEN)}{str(row.moon_azimuth)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Sun Altitude: {esc(COLOR_GREEN)}{str(row.sun_altitude)}, "
                    + f"{esc(COLOR_RED)}Sun Azimuth: {esc(COLOR_GREEN)}{str(row.sun_azimuth)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Sun next Rising: {esc(COLOR_GREEN)}{str(row.sun_next_rising)}, "
                    + f"{esc(COLOR_RED)}Nautical: {esc(COLOR_GREEN)}{str(row.sun_next_rising_nautical)}, "
                    + f"{esc(COLOR_RED)}Astronomical: {esc(COLOR_GREEN)}{str(row.sun_next_rising_astro)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Sun next Setting: {esc(COLOR_GREEN)}{str(row.sun_next_setting)}, "
                    + f"{esc(COLOR_RED)}Nautical: {esc(COLOR_GREEN)}{str(row.sun_next_setting_nautical)}, "
                    + f"{esc(COLOR_RED)}Astronomical: {esc(COLOR_GREEN)}{str(row.sun_next_setting_astro)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Moon next Rising: {esc(COLOR_GREEN)}{str(row.moon_next_rising)}, "
                    + f"{esc(COLOR_RED)}Moon next Setting: {esc(COLOR_GREEN)}{str(row.moon_next_setting)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Moon next new Moon: {esc(COLOR_GREEN)}{str(row.moon_next_new_moon)}, "
                    + f"{esc(COLOR_RED)}Moon next full Moon: {esc(COLOR_GREEN)}{str(row.moon_next_full_moon)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Forecast Today: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today)}, "
                    + f"{esc(COLOR_RED)}Forecast Today Dayname: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today_dayname)}, "
                    + f"{esc(COLOR_RED)}Forecast Today: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today_plain)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Forecast Tomorrow: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow)}, "
                    + f"{esc(COLOR_RED)}Forecast Tomorrow Dayname: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow_dayname)}, "
                    + f"{esc(COLOR_RED)}Forecast Tomorrow: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow_plain)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}DSD Moon rises: {esc(COLOR_GREEN)}{str(row.deep_sky_darkness_moon_rises)}, "
                    + f"{esc(COLOR_RED)}DSD Moon sets: {esc(COLOR_GREEN)}{str(row.deep_sky_darkness_moon_sets)}, "
                    + f"{esc(COLOR_RED)}DSD Moon always down: {esc(COLOR_GREEN)}{str(row.deep_sky_darkness_moon_always_down)}, "
                    + f"{esc(COLOR_RED)}DSD Moon always up: {esc(COLOR_GREEN)}{str(row.deep_sky_darkness_moon_always_up)}{esc('0')}"
                )
                print(
                    f"{esc(COLOR_RED)}Night Duration Astronomical: {esc(COLOR_GREEN)}{str(round(row.night_duration_astronomical / 3600, 2))}, "
                    + f"{esc(COLOR_RED)}DSD: {esc(COLOR_GREEN)}{str(round(row.deep_sky_darkness / 3600,2))}{esc('0')}"
                )
                print(f"{esc(COLOR_RED)}Uptonight: {esc(COLOR_GREEN)}{row.uptonight}{esc('0')}")

    except AstroWeatherError as err:
        print(err)

    end = time.time()

    print(f"Execution time: %s seconds", end - start)


asyncio.run(main())
