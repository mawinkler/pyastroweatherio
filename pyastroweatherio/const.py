"""Constant Definitions for AstroWeather."""

BASE_URL = "http://www.7timer.info/bin/api.pl"
STIMER_OUTPUT = "json"

DEFAULT_TIMEOUT = 10
DEFAULT_CACHE_TIMEOUT = 300
DEFAULT_ELEVATION = 0
ASTRONOMICAL_TWILIGHT = -18

DEEP_SKY_THRESHOLD = 75
HOME_LATITUDE = 0.0
HOME_LONGITUDE = 0.0

CLOUDCOVER_PLAIN = [
    "0-6",
    "6-19",
    "19-31",
    "31-44",
    "44-56",
    "56-69",
    "69-81",
    "81-94",
    "94-100",
]

SEEING_PLAIN = [
    "<0.5",
    "0.5-0.75",
    "0.75-1",
    "1-1.25",
    "1.25-1.5",
    "1.5-2",
    "2-2.5",
    ">2.5",
]

TRANSPARENCY_PLAIN = [
    "<0.3",
    "0.3-0.4",
    "0.4-0.5",
    "0.5-0.6",
    "0.6-0.7",
    "0.7-0.85",
    "0.85-1",
    ">1",
]

LIFTED_INDEX_PLAIN = [
    "Below -7, very unstable",
    "-7 to -5, very unstable",
    "-5 to -3, unstable",
    "-3 to 0, slightly unstable",
    "0 to 4, stable",
    "4 to 8, stable",
    "8 to 11, very stable",
    "Over 11, very stable",
]

RH2M_PLAIN = [
    "0-5",
    "5-10",
    "10-15",
    "15-20",
    "20-25",
    "25-30",
    "30-35",
    "35-40",
    "40-45",
    "45-50",
    "50-55",
    "55-60",
    "60-65",
    "65-70",
    "70-75",
    "75-80",
    "80-85",
    "85-90",
    "90-95",
    "95-99",
    "100",
]

WIND10M_SPEED_PLAIN = [
    "calm",
    "light",
    "moderate",
    "fresh",
    "strong",
    "gale",
    "storm",
    "hurricane",
]

MAP_WEATHER_TYPE = {
    "clearday": "Total cloud cover less than 20%",
    "clearnight": "Total cloud cover less than 20%",
    "pcloudyday": "Total cloud cover between 20%-60%",
    "pcloudynight": "Total cloud cover between 20%-60%",
    "mcloudyday": "Total cloud cover between 60%-80%",
    "mcloudynight": "Total cloud cover between 60%-80%",
    "cloudyday": "Total cloud cover over 80%",
    "cloudynight": "Total cloud cover over 80%",
    "humidday": "Relative humidity over 90% with total cloud cover less than 60%",
    "humidnight": "Relative humidity over 90% with total cloud cover less than 60%",
    "lightrainday": "Precipitation rate less than 4mm/hr with total cloud cover more than 80%",
    "lightrainnight": "Precipitation rate less than 4mm/hr with total cloud cover more than 80%",
    "oshowerday": "Precipitation rate less than 4mm/hr with total cloud cover between 60%-80%",
    "oshowernight": "Precipitation rate less than 4mm/hr with total cloud cover between 60%-80%",
    "ishowerday": "Precipitation rate less than 4mm/hr with total cloud cover less than 60%",
    "ishowernight": "Precipitation rate less than 4mm/hr with total cloud cover less than 60%",
    "lightsnowday": "Precipitation rate less than 4mm/hr",
    "lightsnownight": "Precipitation rate less than 4mm/hr",
    "rainday": "Precipitation rate over 4mm/hr",
    "rainnight": "Precipitation rate over 4mm/hr",
    "snowday": "Precipitation rate over 4mm/hr",
    "snownight": "Precipitation rate over 4mm/hr",
    "rainsnowday": "Precipitation type to be ice pellets or freezing rain",
    "rainsnownight": "Precipitation type to be ice pellets or freezing rain",
}

CONDITION = ["excellent", "good", "fair", "poor", "bad"]

FORECAST_TYPE_DAILY = "daily"
FORECAST_TYPE_HOURLY = "hourly"

FORECAST_TYPES = [
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
]
