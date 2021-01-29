# pyAstroWeatherIO

Wrapper for the 7Timer AstroWeather REST API. Designed to work with Home Assistant.

This module communicates with the API endpoint of 7Timer ([documentation](http://www.7timer.info/doc.php)). It retrieves current weather data for astronomical observations:

* **Cloud Cover** - 1 to 10.
* **Lifted Index** - -10 to 15.
* **2m Temperature** - -76 to 60C.
* **2m Relative Humidity** - 0 to 100.
* **10m Wind Direction** - N, NE, E, SE, S, SW, W, NW.
* **10m Wind Speed** - 1 to 8.
* **Precipitation Type** - snow, rain, frzr (freezing rain), icep (ice pellets), none.
* **Precipitation Amount** - 0 to 9.

For astronimical observations, the lower the values are the better it is (besides 2m temperature).

## Functions

The module exposes the following functions:

### AstroWeather()

this will return the current forecast data from now to in 72

## Setup

```sh
pip3 install . --user
```
