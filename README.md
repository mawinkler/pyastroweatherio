# pyAstroWeatherIO

Wrapper for the ***7Timer*** and ***MET Norway Weather*** REST API. Designed to work with Home Assistant and the custom [AstroWeather](https://github.com/mawinkler/astroweather) integration.

This module communicates with the API endpoint of ***7Timer*** ([documentation](http://www.7timer.info/doc.php)) and ***MET Norway Weather*** ([documentation](https://api.met.no/weatherapi/locationforecast/2.0/documentation)). It retrieves current weather data for astronomical observations:

In addition to the weather data, some calculations for the astronomical twilight and Moon setting, rising and phase are implemented. They indicate the darkness you can expect the upcoming night.

A new addition is an experimental mode that attempts to approximate the calculation of the lifted index, seeing and atmospheric transparency using only Met.no weather data.

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
        seeing_weight,
        transparency_weight,
        calm_weight,
        uptonight_path,
        experimental_features,
    )

astroweather.get_location_data

astroweather.get_hourly_forecast
```

This will return a handle to the AstroWeather class and open the connection.

## Setup

```sh
pip3 install .
```
