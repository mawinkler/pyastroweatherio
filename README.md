# pyAstroWeatherIO

Wrapper for the 7Timer AstroWeather REST API. Designed to work with Home Assistant and the custom [AstroWeather](https://github.com/mawinkler/astroweather) integration.

This module communicates with the API endpoint of 7Timer ([documentation](http://www.7timer.info/doc.php)). It retrieves current weather data for astronomical observations:

Observation | Range | Meaning
----------- | ----- | -------
**Cloud Cover** | 1 to 9 | 1 = <6% to 9 = >94%
**Lifted Index** | -10 to 15 | -10 = <-7 to 15 = >11
**Seeing** | 1 to 8 | 1 = <0.5" to 8 = >2.5"
**Transparency** | 1 to 8 | 1 = <0.3 to 8 = >1
**2m Temperature** | -76°C to 60°C | -76°C to 60°C
**2m Relative Humidity** | 0 to 100 | 0% to 100%
**10m Wind Direction** | N, NE, E, SE, S, SW, W, NW |
**10m Wind Speed** | 1 to 8 | < 0.3m/s to 32.6m/s
**Precipitation Type** | snow, rain, frzr (freezing rain), icep (ice pellets), none |
**Precipitation Amount** | 0 to 9 | < 0.25mm/hr to >75mm/hr
**Weather Type** | clearday, clearnight |Total cloud cover less than 20%
|| pcloudyday, pcloudynight | Total cloud cover between 20%-60%
|| mcloudyday, mcloudynight | Total cloud cover between 60%-80%
|| cloudyday, cloudynight | Total cloud cover over 80%
|| humidday, humidnight | Relative humidity over 90% with total cloud cover less than 60%
|| lightrainday, lightrainnight | Precipitation rate less than 4mm/hr with total cloud cover more than 80%
|| oshowerday, oshowernight | Precipitation rate less than 4mm/hr with total cloud cover between 60%-80%
|| ishowerday, ishowernight | Precipitation rate less than 4mm/hr with total cloud cover less than 60%
|| lightsnowday, lightsnownight | Precipitation rate less than 4mm/hr
|| rainday, rainnight | Precipitation rate over 4mm/hr
|| snowday, snownight | Precipitation rate over 4mm/hr
|| rainsnowday, rainsnownight | Precipitation type to be ice pellets or freezing rain

For astronimical observations, the lower the values are the better it is (besides 2m temperature).

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
pip3 install . --user
```
