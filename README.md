# pyAstroWeatherIO

Wrapper for the ***MET Norway Weather*** and ***Open-Meteo*** RESTful APIs. Designed to work with Home Assistant and the custom [AstroWeather](https://github.com/mawinkler/astroweather) integration.

In addition to the weather data, some calculations for the astronomical twilight and Moon setting, rising and phase are implemented. They indicate the darkness you can expect the upcoming night.

A new addition is an experimental mode that attempts to approximate the calculation of the lifted index, seeing atmospheric transparency, and ground fog density.

## Functions

The module exposes the following function:

```python
astroweather = AstroWeather(
    session,
    latitude,
    longitude,
    elevation,
    timezone_info,
    cloudcover_weight,
    cloudcover_high_weakening,
    cloudcover_medium_weakening,
    cloudcover_low_weakening,
    fog_weight,
    seeing_weight,
    transparency_weight,
    calm_weight,
    uptonight_path,
    experimental_features,
    forecast_model="icon_seamless",
)

astroweather.get_location_data

astroweather.get_hourly_forecast
```

This will return a handle to the AstroWeather class and open the connection.

## Setup

```sh
pip3 install .
```

## Build

```sh
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python3 setup.py sdist
twine upload dist/*
```

## Test

```sh
python -m unittest -v tests/client.py
```
