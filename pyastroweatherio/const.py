"""Constant Definitions for AstroWeather."""

# #####################################################
# Requests
# #####################################################
BASE_URL_SEVENTIMER = "https://www.7timer.info/bin/api.pl"
BASE_URL_MET = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
HEADERS = {"User-Agent": "AstroWeather github.com/mawinkler/astroweather"}

# #####################################################
# Defaults
# #####################################################
DEFAULT_TIMEOUT = 10
DEFAULT_CACHE_TIMEOUT = 1770
DEFAULT_TIMEZONE = "Etc/UTC"
DEFAULT_LATITUDE = 0.0
DEFAULT_LONGITUDE = 0.0
DEFAULT_ELEVATION = 0

# #####################################################
# Twilight and dusk
# #####################################################
CIVIL_TWILIGHT = 0
CIVIL_DUSK_DAWN = -6
NAUTICAL_TWILIGHT = -6
NAUTICAL_DUSK_DAWN = -12
ASTRONOMICAL_TWILIGHT = -12
ASTRONOMICAL_DUSK_DAWN = -18

# #####################################################
# Cloudcover
# #####################################################
# CLOUDCOVER_PLAIN = [
#     "0 to 6%",
#     "6 to 19%",
#     "19 to 31%",
#     "31 to 44%",
#     "44 to 56%",
#     "56 to 69%",
#     "69 to 81%",
#     "81 to 94%",
#     "94 to 100%",
# ]

# #####################################################
# Seeing
# #####################################################
SEEING = [0.25, 0.625, 0.875, 1.125, 1.375, 1.75, 2.25, 2.5]
# SEEING_PLAIN = [
#     'Below 0.5"',
#     '0.5 to 0.75"',
#     '0.75 to 1"',
#     '1 to 1.25"',
#     '1.25 to 1.5"',
#     '1.5 to 2"',
#     '2 to 2.5"',
#     'Over 2.5"',
# ]
SEEING_MAX = 2.5

# #####################################################
# Transparency
# #####################################################
TRANSPARENCY = [0.15, 0.35, 0.45, 0.55, 0.65, 0.775, 0.925, 1]
MAG_DEGRATION_MAX = 1
# TRANSPARENCY_PLAIN = [
#     "Below 0.3 mag",
#     "0.3 to 0.4 mag",
#     "0.4 to 0.5 mag",
#     "0.5 to 0.6 mag",
#     "0.6 to 0.7 mag",
#     "0.7 to 0.85 mag",
#     "0.85 to 1 mag",
#     "Over 1 mag",
# ]

# #####################################################
# Lifted Index
# #####################################################
# Negative Values (Unstable Atmosphere):
# LI < -6: Strongly unstable atmosphere, potential for severe thunderstorms and severe weather outbreaks.
# LI ≈ -4 to -6: Moderately unstable atmosphere, potential for thunderstorms and severe weather.
# LI ≈ -2 to -4: Slightly unstable atmosphere, some potential for thunderstorms.
# Near Zero Values:
# LI ≈ 0: Neutral stability, some potential for thunderstorms, weak to moderate vertical motion.
# Positive Values (Stable Atmosphere):
# LI ≈ +1 to +3: Slightly stable atmosphere, limited potential for thunderstorms, weak vertical motion.
# LI ≈ +4 to +6: Moderately stable atmosphere, very limited potential for thunderstorms, very weak vertical motion.
# LI > +6: Strongly stable atmosphere, very limited potential for thunderstorms, very weak to no vertical motion.
LIFTED_INDEX_VALUE = [1, 2, 3, 4, 5, 6, 7, 8]
LIFTED_INDEX_RANGE = [(-20, -6.99), (-7, -4.99), (-5, -2.99), (-3, -0.01), (0, 3.99), (4, 7.99), (8, 10.99), (11, 20)]
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

# #####################################################
# Wind
# #####################################################
# 0 --- Calm            less than 1 mph (0 m/s)      Smoke rises vertically
# 1 --- Light air       1 - 3 mph     0.5-1.5 m/s    Smoke drifts with air, weather vanes inactive
# 2 --- Light breeze    4 - 7 mph     2-3 m/s        Weather vanes active, wind felt on face, leaves rustle
# 3 --- Gentle breeze   8 - 12 mph    3.5-5 m/s      Leaves & small twigs move, light flags extend
# 4 --- Moderate breeze 13 - 18 mph   5.5-8 m/s      Small branches sway, dust & loose paper blows about
# 5 --- Fresh breeze    19 - 24 mph   8.5-10.5 m/s   Small trees sway, waves break on inland waters
# 6 --- Strong breeze   25 - 31 mph   11-13.5 m/s    Large branches sway, umbrellas difficult to use
# 7 --- Moderate gale   32 - 38 mph   14-16.5 m/s    Whole trees sway, difficult to walk against wind
# Too windy
# 8 --- Fresh gale      39 - 46 mph   17-20 m/s      Twigs broken off trees, walking against wind very difficult
# 9 --- Strong gale     47 - 54 mph   20.5-23.5 m/s  Slight damage to buildings, shingles blown off roof
# 10 -- Whole gale      55 - 63 mph   24-27.5 m/s    Trees uprooted, considerable damage to buildings
# 11 -- Storm           64 - 73 mph   28-31.5 m/s    Widespread damage, very rare occurrence
# 12 -- Hurricane       over 73 mph   over 32 m/s    Violent destruction
WIND10M_DIRECTON = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
WIND10M_VALUE = [1, 2, 3, 4, 5, 6, 7, 8]
WIND10M_RANGE = [(0, 0.49), (0.5, 1.99), (2, 3.49), (3.5, 5.49), (5.5, 8.49), (8.5, 10.99), (11, 13.99), (14, 100)]
WIND10M_PLAIN = [
    "Calm",
    "Light air",
    "Light breeze",
    "Gentle breeze",
    "Moderate breeze",
    "Fresh breeze",
    "Strong breeze",
    "Moderate gale",
]
WIND10M_MAX = 16.5

# #####################################################
# Condition
# #####################################################
DEFAULT_CONDITION_CLOUDCOVER_WEIGHT = 3
DEFAULT_CONDITION_CLOUDCOVER_HIGH_WEAKENING = 1
DEFAULT_CONDITION_CLOUDCOVER_MEDIUM_WEAKENING = 1
DEFAULT_CONDITION_CLOUDCOVER_LOW_WEAKENING = 1
DEFAULT_CONDITION_SEEING_WEIGHT = 2
DEFAULT_CONDITION_TRANSPARENCY_WEIGHT = 1
DEFAULT_CONDITION_CALM_WEIGHT = 2
CONDITION_PLAIN = ["excellent", "good", "fair", "poor", "bad"]
CONDITION = ["█", "▆", "▄", "▂", "▁"]
DEEP_SKY_THRESHOLD = 75

# #####################################################
# Forecast
# #####################################################
FORECAST_TYPE_DAILY = "daily"
FORECAST_TYPE_HOURLY = "hourly"
FORECAST_TYPES = [
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
]
