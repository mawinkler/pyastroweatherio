import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry
from pprint import pprint as pp

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 48.31,
    "longitude": 11.98,
    "hourly": [
        "temperature_2m",
        "lifted_index",
        "cape",
        "boundary_layer_height",
        "wind_speed_80m",
        "visibility",
        "surface_pressure",
    ],
    # "models": ["metno_seamless", "icon_seamless", "gfs_seamless", "ecmwf_ifs025"],
    "models": ["gfs_seamless"],
    "timezone": "Europe/Berlin",
}
responses = openmeteo.weather_api(url, params=params)

# Process 1 location and 4 models
for response in responses:
    print(f"\nCoordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")
    print(f"Model Nº: {response.Model()}")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_lifted_index = hourly.Variables(1).ValuesAsNumpy()
    hourly_cape = hourly.Variables(2).ValuesAsNumpy()
    hourly_boundary_layer_height = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_speed_80m = hourly.Variables(4).ValuesAsNumpy()
    hourly_visibility = hourly.Variables(5).ValuesAsNumpy()
    hourly_surface_pressure = hourly.Variables(6).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        ).tz_convert("Europe/Berlin")
    }

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["lifted_index"] = hourly_lifted_index
    hourly_data["cape"] = hourly_cape
    hourly_data["boundary_layer_height"] = hourly_boundary_layer_height
    hourly_data["wind_speed_80m"] = hourly_wind_speed_80m
    hourly_data["visibility"] = hourly_visibility
    hourly_data["surface_pressure"] = hourly_surface_pressure

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    print("\nHourly data\n", hourly_dataframe)
    for index, row in hourly_dataframe.iterrows():
        print(index, row["date"], row["lifted_index"], row["boundary_layer_height"], row["cape"], row["visibility"])
