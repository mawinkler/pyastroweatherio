# pyAstroWeatherIO

Wrapper for the ***7Timer*** and ***MET Norway Weather*** REST API. Designed to work with Home Assistant and the custom [AstroWeather](https://github.com/mawinkler/astroweather) integration.

This module communicates with the API endpoint of ***7Timer*** ([documentation](http://www.7timer.info/doc.php)) and ***MET Norway Weather*** ([documentation](https://api.met.no/weatherapi/locationforecast/2.0/documentation)). It retrieves current weather data for astronomical observations:

In addition to the weather data, some calculations for the astronomical twilight and Moon setting, rising and phase are implemented. They indicate the darkness you can expect the upcoming night.

## Functions

The module exposes the following function:

### AstroWeather(latitude, longitude, elevation)

This will return a handle to the AstroWeather class and open the connection.

**latitude**

(float)(Required) The geographic coordinate that specifies the norh-south position of the location of interest in angle.

**longitude**

(float)(Required) The geographic coordinate that specifies the east-west position of the location of interest in angle.

**elevation**

(int)(Required) The elevation above Earth's sea level of the geographic location in m.

**cloudcover_weight**

(int)(Optional) Cloud coverage weight for condition calculation, default=3

**seeing_weight**

(int)(Optional) Seeing weight for condition calculation, default=2

**transparency_weight**

(int)(Optional) Seeing weight for condition calculation, default=1

## Setup

```sh
pip3 install .
```
