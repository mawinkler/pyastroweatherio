""" Communicates with 7Timer using REST. """
from pyastroweatherio.client import AstroWeather
from pyastroweatherio.errors import AstroWeatherError, RequestError, ResultError
from pyastroweatherio.const import (
    FORECAST_TYPES,
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
)
