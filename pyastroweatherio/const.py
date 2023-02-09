"""Constant Definitions for AstroWeather."""

BASE_URL = "http://www.7timer.info/bin/api.pl"
STIMER_OUTPUT = "json"

DEFAULT_TIMEOUT = 10
DEFAULT_CACHE_TIMEOUT = 1770
DEFAULT_ELEVATION = 0
DEFAULT_TIMEZONE = "Etc/UTC"
DEFAULT_CONDITION_CLOUDCOVER_WEIGHT = 3
DEFAULT_CONDITION_SEEING_WEIGHT = 2
DEFAULT_CONDITION_TRANSPARENCY_WEIGHT = 1

CIVIL_TWILIGHT = 0
CIVIL_DUSK_DAWN = -6
NAUTICAL_TWILIGHT = -6
NAUTICAL_DUSK_DAWN = -12
ASTRONOMICAL_TWILIGHT = -12
ASTRONOMICAL_DUSK_DAWN = -18

MAGNUS_COEFFICIENT_A = 17.625
MAGNUS_COEFFICIENT_B = 243.04

DEEP_SKY_THRESHOLD = 75
HOME_LATITUDE = 0.0
HOME_LONGITUDE = 0.0

CLOUDCOVER_PLAIN = [
    "0 to 6%",
    "6 to 19%",
    "19 to 31%",
    "31 to 44%",
    "44 to 56%",
    "56 to 69%",
    "69 to 81%",
    "81 to 94%",
    "94 to 100%",
]

SEEING_PLAIN = [
    'Below 0.5"',
    '0.5 to 0.75"',
    '0.75 to 1"',
    '1 to 1.25"',
    '1.25 to 1.5"',
    '1.5 to 2"',
    '2 to 2.5"',
    'Over 2.5"',
]

TRANSPARENCY_PLAIN = [
    "Below 0.3 mag",
    "0.3 to 0.4 mag",
    "0.4 to 0.5 mag",
    "0.5 to 0.6 mag",
    "0.6 to 0.7 mag",
    "0.7 to 0.85 mag",
    "0.85 to 1 mag",
    "Over 1 mag",
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

WIND10M_SPEED_PLAIN = [
    "none",
    "calm",
    "light",
    "moderate",
    "fresh",
    "strong",
    "gale",
    "storm",
    "hurricane",
]

WIND10M_SPEED = [
    0,
    0.3,
    3.4,
    8.0,
    10.8,
    17.2,
    24.5,
    32.6,
    36.7,
    41.4,
    46.2,
    50.9,
    55.9,
    60.9,
]
# WIND10M_SPEED = [
#     "0.3m/s (calm)",
#     "0.3-3.4m/s (light)",
#     "3.4-8.0m/s (moderate)",
#     "8.0-10.8m/s (fresh)",
#     "10.8-17.2m/s (strong)",
#     "17.2-24.5m/s (gale)",
#     "24.5-32.6m/s (storm)",
#     "32.6-36.7m/s (hurricane)",
#     "36.7-41.4m/s (hurricane+)",
#     "41.4-46.2m/s (hurricane+)",
#     "46.2-50.9m/s (hurricane+)",
#     "50.9-55.9m/s (hurricane+)",
#     "Over 55.9m/s (hurricane+)",
# ]

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
    "tsday": "Lifted Index less than -5 with precipitation rate below 4mm/hr",
    "tsnight": "Lifted Index less than -5 with precipitation rate below 4mm/hr",
    "tsrainday": "Lifted Index less than -5 with precipitation rate over 4mm/hr",
    "tsrainnight": "Lifted Index less than -5 with precipitation rate over 4mm/hr",
}

CONDITION = ["excellent", "good", "fair", "poor", "bad"]

FORECAST_TYPE_DAILY = "daily"
FORECAST_TYPE_HOURLY = "hourly"

FORECAST_TYPES = [
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
]
