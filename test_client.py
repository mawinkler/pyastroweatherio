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


async def main() -> None:
    """Create the aiohttp session and run the example."""
    logging.basicConfig(level=logging.DEBUG)

    # astroweather = AstroWeather()
    astroweather = AstroWeather(latitude=48.313, longitude=11.985)

    start = time.time()

    try:
        _LOGGER.info("GETTING FORECAST DATA:")

        data = await astroweather.get_forecast(hours_to_show=72)
        for row in data:
            print(row.init)
            _LOGGER.info(
                "\n"
                + "PRODUCT: "
                + str(row.product)
                + "\n"
                + "INIT: "
                + str(row.init)
                + "\n"
                + "TIMEPOINT: "
                + str(row.timepoint)
                + "\n"
                + "GEOLOCATION: LAT="
                + str(row.latitude)
                + ", LONG="
                + str(row.longitude)
                + "\n"
                + "TIMESTAMP: "
                + str(row.timestamp)
                + "\n"
                + "CLOUDCOVER: "
                + str(row.cloudcover)
                + "\n"
                + "CLOUDCOVER PLAIN: "
                + str(row.cloudcover_plain)
                + "\n"
                + "SEEING: "
                + str(row.seeing)
                + "\n"
                + "SEEING PLAIN: "
                + str(row.seeing_plain)
                + "\n"
                + "TRANSPARENCY: "
                + str(row.transparency)
                + "\n"
                + "TRANSPARENCY PLAIN: "
                + str(row.transparency_plain)
                + "\n"
                + "LIFTED INDEX: "
                + str(row.lifted_index)
                + "\n"
                + "LIFTED INDEX PLAIN: "
                + str(row.lifted_index_plain)
                + "\n"
                + "RH2M: "
                + str(row.rh2m)
                + "\n"
                + "RH2M PLAIN: "
                + str(row.rh2m_plain)
                + "\n"
                + "WIND10M DIRECTION: "
                + str(row.wind10m_direction)
                + "\n"
                + "WIND10M SPEED: "
                + str(row.wind10m_speed)
                + "\n"
                + "WIND10M SPEED PLAIN: "
                + str(row.wind10m_speed_plain)
                + "\n"
                + "TEMP2M: "
                + str(row.temp2m)
                + "\n"
                + "PREC TYPE: "
                + str(row.prec_type)
                + "\n"
                + "FORECAST THIS NIGHT: "
                + str(row.forecast0)
                + "\n"
                + "FORECAST THIS NIGHT: "
                + str(row.forecast0_plain)
                + "\n"
                + "FORECAST TOMORROW NIGHT: "
                + str(row.forecast1)
                + "\n"
                + "FORECAST TOMORROW NIGHT: "
                + str(row.forecast1_plain)
                + "\n"
                + "DEEP SKY VIEW: "
                + str(row.deep_sky_view)
                + "\n"
                + "VIEW CONDITION: "
                + str(row.view_condition)
                + "\n"
                + "VIEW CONDITION PLAIN: "
                + str(row.view_condition_plain)
                + "\n",
            )

    except AstroWeatherError as err:
        _LOGGER.info(err)

    end = time.time()

    _LOGGER.info("Execution time: %s seconds", end - start)


asyncio.run(main())
