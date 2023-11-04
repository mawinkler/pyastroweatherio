""" The test for the API """
import asyncio
import pprint
import logging
import time
import os
from datetime import datetime, timedelta
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
    logging.basicConfig(level=logging.INFO)
    
    f = open("test_dsd.csv", "w")

    f.write(
        "Datetime;Sun next Rising;Sun next Rising Astronomical;Sun next Setting;Sun next Setting Astronomical;Moon next Rising;Moon next Setting;Sun Altitude;Moon Altitude;DSD Moon rises;DSD Moon sets;DSD Moon always up;DSD Moon always down;NDA;DSD\n"
    )

    ds_string = "11/03/2023 00:00:00"
    dt = datetime.strptime(ds_string, "%m/%d/%Y %H:%M:%S")
    de_string = "11/05/2023 00:00:00"
    de = datetime.strptime(de_string, "%m/%d/%Y %H:%M:%S")

    start = time.time()

    while dt < de:
        astroweather = AstroWeather(
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
            timezone_info=timezone_info,
            cloudcover_weight=3,
            seeing_weight=2,
            transparency_weight=1,
            uptonight_path=".",
            test_datetime=dt,
        )

        try:
            data = await astroweather.get_location_data()
            for row in data:
                print(
                    f"{esc(COLOR_RED)}Date & Time: {esc(COLOR_GREEN)}{str(utc_to_local(dt))}{esc(COLOR_BLUE)}"
                    + " - "
                    + "SS "
                    + str(datetime.strftime(utc_to_local(row.sun_next_setting), "%d.%m.%Y %H:%M:%S"))
                    + "; "
                    + "SR "
                    + str(datetime.strftime(utc_to_local(row.sun_next_rising), "%d.%m.%Y %H:%M:%S"))
                    + "; "
                    + "SSA "
                    + str(datetime.strftime(utc_to_local(row.sun_next_setting_astro), "%d.%m.%Y %H:%M:%S"))
                    + "; "
                    + "SRA "
                    + str(datetime.strftime(utc_to_local(row.sun_next_rising_astro), "%d.%m.%Y %H:%M:%S"))
                    + "; "
                    + "MR "
                    + str(datetime.strftime(utc_to_local(row.moon_next_rising), "%d.%m.%Y %H:%M:%S"))
                    + "; "
                    + "MS "
                    + str(datetime.strftime(utc_to_local(row.moon_next_setting), "%d.%m.%Y %H:%M:%S"))
                    + "; "
                )

                f.write(
                    str(datetime.strftime(utc_to_local(dt), "%d.%m.%Y %H:%M:%S"))
                    + ";"
                    + str(datetime.strftime(utc_to_local(row.sun_next_rising), "%d.%m.%Y %H:%M:%S"))
                    + ";"
                    + str(datetime.strftime(utc_to_local(row.sun_next_rising_astro), "%d.%m.%Y %H:%M:%S"))
                    + ";"
                    + str(datetime.strftime(utc_to_local(row.sun_next_setting), "%d.%m.%Y %H:%M:%S"))
                    + ";"
                    + str(datetime.strftime(utc_to_local(row.sun_next_setting_astro), "%d.%m.%Y %H:%M:%S"))
                    + ";"
                    + str(datetime.strftime(utc_to_local(row.moon_next_rising), "%d.%m.%Y %H:%M:%S"))
                    + ";"
                    + str(datetime.strftime(utc_to_local(row.moon_next_setting), "%d.%m.%Y %H:%M:%S"))
                    + ";"
                    + str(row.sun_altitude).replace(".", ",")
                    + ";"
                    + str(row.moon_altitude).replace(".", ",")
                    + ";"
                    + str(row.deep_sky_darkness_moon_rises)
                    + ";"
                    + str(row.deep_sky_darkness_moon_sets)
                    + ";"
                    + str(row.deep_sky_darkness_moon_always_up)
                    + ";"
                    + str(row.deep_sky_darkness_moon_always_down)
                    + ";"
                    + convert_to_hhmm(row.night_duration_astronomical)
                    + ";"
                    + convert_to_hhmm(row.deep_sky_darkness)
                    + "\n"
                )
        except AstroWeatherError as err:
            print(err)

        dt = dt + timedelta(minutes=15)

    f.close()

    end = time.time()

    print(f"Execution time: %s seconds", end - start)


asyncio.run(main())
