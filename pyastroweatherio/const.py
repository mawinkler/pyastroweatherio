"""Constant Definitions for AstroWeather."""

BASE_URL = "http://www.7timer.info/bin/api.pl"
STIMER_PRODUCT = "astro"
STIMER_OUTPUT = "json"

DEFAULT_TIMEOUT = 10

DEEP_SKY_THRESHOLD = 2
HOME_LATITUDE = 0.0
HOME_LONGITUDE = 0.0

CLOUDCOVER_PLAIN = [
    "0%-6%",
    "6%-19%",
    "19%-31%",
    "31%-44%",
    "44%-56%",
    "56%-69%",
    "69%-81%",
    "81%-94%",
    "94%-100%",
]

SEEING_PLAIN = [
    '<0.5"',
    '0.5"-0.75"',
    '0.75"-1"',
    '1"-1.25"',
    '1.25"-1.5"',
    '1.5"-2"',
    '2"-2.5"',
    '>2.5"',
]

TRANSPARENCY_PLAIN = [
    "<0.3mag",
    "0.3-0.4mag",
    "0.4-0.5mag",
    "0.5-0.6mag",
    "0.6-0.7mag",
    "0.7-0.85mag",
    "0.85-1mag",
    ">1mag",
]

LIFTED_INDEX_PLAIN = [
    "Below -7°",
    "-7° to -5°",
    "-5° to -3°",
    "-3° to 0°",
    "0° to 4°",
    "4° to 8°",
    "8° to 11°",
    "Over 11°",
]

RH2M_PLAIN = [
    "0%-5%",
    "5%-10%",
    "10%-15%",
    "15%-20%",
    "20%-25%",
    "25%-30%",
    "30%-35%",
    "35%-40%",
    "40%-45%",
    "45%-50%",
    "50%-55%",
    "55%-60%",
    "60%-65%",
    "65%-70%",
    "70%-75%",
    "75%-80%",
    "80%-85%",
    "85%-90%",
    "90%-95%",
    "95%-99%",
    "100%",
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

CONDITION = ["excellent", "good", "fair", "poor", "bad"]
