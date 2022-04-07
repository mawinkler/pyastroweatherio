""" The test for the API """
import asyncio
import pprint
import logging
import time
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

    astroweather = AstroWeather(latitude=48.313, longitude=11.985, elevation=460)

    start = time.time()

    try:
        data = await astroweather.get_deepsky_forecast()
        for row in data:
            print(
                f"{esc(COLOR_BLUE)}--------------------------------------------------------"
                + f"---------------------------------------------------------------{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Init: {esc(COLOR_GREEN)}{str(row.init)}\t"
                + f"{esc(COLOR_RED)}Hour of day:{esc(COLOR_GREEN)}{str(row.hour)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Nightly conditions: {esc(COLOR_GREEN)}{str(row.nightly_conditions)}\t"
                + f"{esc(COLOR_RED)}Weather: {esc(COLOR_GREEN)}{str(row.weather)}{esc('0')}"
            )

        data = await astroweather.get_location_data()
        for row in data:
            print(
                f"{esc(COLOR_BLUE)}--------------------------------------------------------"
                + f"---------------------------------------------------------------{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Init: {esc(COLOR_GREEN)}{str(row.init)}\t"
                + f"{esc(COLOR_RED)}Timepoint: {esc(COLOR_GREEN)}{str(row.timepoint)}\t\t\t"
                + f"{esc(COLOR_RED)}Timestamp: {esc(COLOR_GREEN)}{str(row.timestamp)}\t\t\t"
                + f"{esc(COLOR_RED)}Forecast Length: {esc(COLOR_GREEN)}{str(row.forecast_length)}\t\t\t{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Latitude: {esc(COLOR_GREEN)}{str(row.latitude)}\t\t"
                + f"{esc(COLOR_RED)}Longitude: {esc(COLOR_GREEN)}{str(row.longitude)}\t\t"
                + f"{esc(COLOR_RED)}Elevation: {esc(COLOR_GREEN)}{str(row.elevation)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}View Condition: {esc(COLOR_GREEN)}{str(row.condition_percentage)}\t\t"
                + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.condition_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Cloudcover: {esc(COLOR_GREEN)}{str(row.cloudcover_percentage)}\t\t\t"
                + f"{esc(COLOR_RED)}Cloudless: {esc(COLOR_GREEN)}{str(row.cloudless_percentage)}\t\t\t"
                + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.cloudcover_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Seeing: {esc(COLOR_GREEN)}{str(row.seeing_percentage)}\t\t\t"
                + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.seeing_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Transparency: {esc(COLOR_GREEN)}{str(row.transparency_percentage)}\t\t"
                + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.transparency_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Lifted Index: {esc(COLOR_GREEN)}{str(row.lifted_index)}\t\t\t"
                + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.lifted_index_plain)}{esc('0')}"
            )
            # + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.rh2m_plain)}{esc('0')}"
            print(
                f"{esc(COLOR_RED)}Rel. Humidity: {esc(COLOR_GREEN)}{str(row.rh2m)}\t\t{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Wind Direction: {esc(COLOR_GREEN)}{str(row.wind10m_direction)}\t\t"
                + f"{esc(COLOR_RED)}Speed: {esc(COLOR_GREEN)}{str(row.wind10m_speed)}\t\t\t"
                + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.wind10m_speed_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Temperature: {esc(COLOR_GREEN)}{str(row.temp2m)}\t\t\t"
                + f"{esc(COLOR_RED)}Prec Type: {esc(COLOR_GREEN)}{str(row.prec_type)}\t\t\t"
                + f"{esc(COLOR_RED)}Deep Sky View: {esc(COLOR_GREEN)}{str(row.deep_sky_view)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}View Condition: {esc(COLOR_GREEN)}{str(row.condition_percentage)}\t\t"
                + f"{esc(COLOR_RED)}Plain: {esc(COLOR_GREEN)}{str(row.condition_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Moon Phase: {esc(COLOR_GREEN)}{str(row.moon_phase)}\t\t"
                + f"{esc(COLOR_RED)}Weather: {esc(COLOR_GREEN)}{str(row.weather)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Sun next Rising: {esc(COLOR_GREEN)}{str(row.sun_next_rising)}\t\t\t\t"
                + f"{esc(COLOR_RED)}Astro: {esc(COLOR_GREEN)}{str(row.sun_next_rising_astro)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Sun next Setting: {esc(COLOR_GREEN)}{str(row.sun_next_setting)}\t\t\t\t"
                + f"{esc(COLOR_RED)}Astro: {esc(COLOR_GREEN)}{str(row.sun_next_setting_astro)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Moon next Rising: {esc(COLOR_GREEN)}{str(row.moon_next_rising)}\t\t\t\t"
                + f"{esc(COLOR_RED)}Moon next Setting: {esc(COLOR_GREEN)}{str(row.moon_next_setting)}\t\t"
            )
            print(
                f"{esc(COLOR_RED)}Forecast Today: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today)}\t\t"
                + f"{esc(COLOR_RED)}Forecast Today Dayname: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today_dayname)}\t\t"
                + f"{esc(COLOR_RED)}Forecast Today: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Description: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_today_desc)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Forecast Tomorrow: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow)}\t\t"
                + f"{esc(COLOR_RED)}Forecast Tomorrow Dayname: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow_dayname)}\t\t"
                + f"{esc(COLOR_RED)}Forecast Tomorrow: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow_plain)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Description: {esc(COLOR_GREEN)}{str(row.deepsky_forecast_tomorrow_desc)}{esc('0')}"
            )

        data = await astroweather.get_daily_forecast()
        print(f"Forecast Length: {str(len(data))}")
        for row in data:
            print(
                f"{esc(COLOR_BLUE)}--------------------------------------------------------"
                + f"---------------------------------------------------------------{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Init: {esc(COLOR_GREEN)}{str(row.init)}\t"
                + f"{esc(COLOR_RED)}Timepoint: {esc(COLOR_GREEN)}{str(row.timepoint)}\t\t\t"
                + f"{esc(COLOR_RED)}Timestamp: {esc(COLOR_GREEN)}{str(row.timestamp)}\t\t"
                + f"{esc(COLOR_RED)}Hour of Day: {esc(COLOR_GREEN)}{str(row.hour)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Cloudcover: {esc(COLOR_GREEN)}{str(row.cloudcover_percentage)}\t\t\t"
                + f"{esc(COLOR_RED)}Cloudless: {esc(COLOR_GREEN)}{str(row.cloudless_percentage)}\t\t\t"
                + f"{esc(COLOR_RED)}Seeing: {esc(COLOR_GREEN)}{str(row.seeing_percentage)}\t\t\t"
                + f"{esc(COLOR_RED)}Transparency: {esc(COLOR_GREEN)}{str(row.transparency_percentage)}\t\t\t"
                + f"{esc(COLOR_RED)}Liftet Index: {esc(COLOR_GREEN)}{str(row.lifted_index)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Wind Direction: {esc(COLOR_GREEN)}{str(row.wind10m_direction)}\t\t"
                + f"{esc(COLOR_RED)}Speed: {esc(COLOR_GREEN)}{str(row.wind10m_speed)}\t\t\t"
                + f"{esc(COLOR_RED)}Rel Humidity: {esc(COLOR_GREEN)}{str(row.rh2m)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}Temperature: {esc(COLOR_GREEN)}{str(row.temp2m)}\t\t\t"
                + f"{esc(COLOR_RED)}Prec Type: {esc(COLOR_GREEN)}{str(row.prec_type)}{esc('0')}"
            )
            print(
                f"{esc(COLOR_RED)}View Condition: {esc(COLOR_GREEN)}{str(row.condition_percentage)}\t\t"
                + f"{esc(COLOR_RED)}Weather: {esc(COLOR_GREEN)}{str(row.weather)}{esc('0')}"
            )

    except AstroWeatherError as err:
        print(err)

    end = time.time()

    print(f"Execution time: %s seconds", end - start)


asyncio.run(main())
