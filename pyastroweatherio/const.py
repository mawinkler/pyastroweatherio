"""Constant Definitions for AstroWeather."""

BASE_URL_SEVENTIMER = "https://www.7timer.info/bin/api.pl"
BASE_URL_MET = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
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

WIND10M_DIRECTON = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# CONDITION = ["excellent", "good", "fair", "poor", "bad"]
# CONDITION = ["↑", "↗", "→", "↘", "↓"]
# CONDITION = ["😁", "😀", "😐", "😕", "😞"]
CONDITION = ["█", "▆", "▄", "▂", "▁"]

FORECAST_TYPE_DAILY = "daily"
FORECAST_TYPE_HOURLY = "hourly"

FORECAST_TYPES = [
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
]
