""" The test for the API """
import asyncio
import pprint
import logging
import time
from datetime import datetime
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


def esc(code):
    return f"\033[{code}m"


async def main() -> None:
    """Create the aiohttp session and run the example."""
    logging.basicConfig(level=logging.DEBUG)

        # latitude=48.313,
        # longitude=11.985,
        # elevation=460,

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
        latitude=48.313,
        longitude=11.985,
        elevation=0,
        timezone_info="Europe/Berlin",
        cloudcover_weight=3,
        seeing_weight=2,
        transparency_weight=1,
    )

    start = time.time()


    try:
        data = await astroweather.get_deepsky_forecast()
        for row in data:
            print(
                f"{esc(COLOR_BLUE)}--------------------------------------------------------"
                + f"---------------------------------------------------------------{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Init: {esc(COLOR_GREEN)}{str(row.init)}, "
                + f"{esc(COLOR_RED)}Hour of day: {esc(COLOR_GREEN)}{str(row.hour)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Nightly conditions: {esc(COLOR_GREEN)}{str(row.nightly_conditions)}, "
                + f"{esc(COLOR_RED)}Weather: {esc(COLOR_GREEN)}{str(row.weather)}{esc('0')}"
            )

        data = await astroweather.get_location_data()
        for row in data:
            print(
                f"{esc(COLOR_BLUE)}--------------------------------------------------------"
                + f"---------------------------------------------------------------{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Init: {esc(COLOR_GREEN)}{str(row.init)}, "
                + f"{esc(COLOR_RED)}Timepoint: {esc(COLOR_GREEN)}{str(row.timepoint)}, "
                + f"{esc(COLOR_RED)}Timestamp: {esc(COLOR_GREEN)}{str(row.timestamp)}, "
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
                + f"{esc(COLOR_RED)}Speed: {esc(COLOR_GREEN)}{str(row.wind10m_speed)}, "
                + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.wind10m_speed_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Temperature: {esc(COLOR_GREEN)}{str(row.temp2m)}, "
                + f"{esc(COLOR_RED)}Rel Humidity: {esc(COLOR_GREEN)}{str(row.rh2m)}, "
                + f"{esc(COLOR_RED)}Dew Point: {esc(COLOR_GREEN)}{str(row.dewpoint2m)}, "
                + f"{esc(COLOR_RED)}Prec Type: {esc(COLOR_GREEN)}{str(row.prec_type)}{esc('0')}"
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
                f"{esc(COLOR_RED)}Forecast Today: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today)}, "
                + f"{esc(COLOR_RED)}Forecast Today Dayname: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today_dayname)}, "
                + f"{esc(COLOR_RED)}Forecast Today: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Description: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today_desc)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Forecast Tomorrow: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow)}, "
                + f"{esc(COLOR_RED)}Forecast Tomorrow Dayname: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow_dayname)}, "
                + f"{esc(COLOR_RED)}Forecast Tomorrow: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Description: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow_desc)}{esc('0')}"
            )

        data = await astroweather.get_hourly_forecast()
        print(f"Forecast Length: {str(len(data))}")
        for row in data:
            print(
                f"{esc(COLOR_BLUE)}--------------------------------------------------------"
                + f"---------------------------------------------------------------{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Init: {esc(COLOR_GREEN)}{str(row.init)}, "
                + f"{esc(COLOR_RED)}Timepoint: {esc(COLOR_GREEN)}{str(row.timepoint)}, "
                + f"{esc(COLOR_RED)}Timestamp: {esc(COLOR_GREEN)}{str(row.timestamp)}, "
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
                f"{esc(COLOR_RED)}View Condition: {esc(COLOR_GREEN)}{str(row.condition_percentage)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Wind Direction: {esc(COLOR_GREEN)}{str(row.wind10m_direction)}, "
                + f"{esc(COLOR_RED)}Speed: {esc(COLOR_GREEN)}{str(row.wind10m_speed)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Temperature: {esc(COLOR_GREEN)}{str(row.temp2m)}, "
                + f"{esc(COLOR_RED)}Rel Humidity: {esc(COLOR_GREEN)}{str(row.rh2m)}, "
                + f"{esc(COLOR_RED)}Dew Point: {esc(COLOR_GREEN)}{str(row.dewpoint2m)}, "
                + f"{esc(COLOR_RED)}Prec Type: {esc(COLOR_GREEN)}{str(row.prec_type)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Weather: {esc(COLOR_GREEN)}{str(row.weather)}{esc('0')}"
            )

    except AstroWeatherError as err:
        print(err)

    end = time.time()

    print(f"Execution time: %s seconds", end - start)


asyncio.run(main())
