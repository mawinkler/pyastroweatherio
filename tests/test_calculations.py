"""Unit tests for atmospheric calculations in AtmosphericRoutines."""

import asyncio
import unittest

from pyastroweatherio.helper_functions import AtmosphericRoutines


class TestAtmosphericCalculations(unittest.TestCase):
    """Tests for AtmosphericRoutines — no network access required."""

    def setUp(self):
        self.atm = AtmosphericRoutines()

        # Typical clear-night inputs
        self.clear = dict(
            temperature=15.0,
            humidity=50.0,
            dew_point_temperature=4.6,
            wind_speed=2.0,
            cloud_cover=0.0,
            altitude=500.0,
            air_pressure_at_sea_level=1013.25,
        )
        # Overcast / bad conditions
        self.overcast = dict(
            temperature=18.0,
            humidity=95.0,
            dew_point_temperature=17.1,
            wind_speed=8.0,
            cloud_cover=100.0,
            altitude=100.0,
            air_pressure_at_sea_level=1005.0,
        )

    # ---------------------------------------------------------------
    # _calculate_adjusted_pressure
    # ---------------------------------------------------------------
    def test_adjusted_pressure_at_sea_level(self):
        p = self.atm._calculate_adjusted_pressure(1013.25, 0)
        self.assertAlmostEqual(p, 1013.25, delta=0.01)

    def test_adjusted_pressure_decreases_with_altitude(self):
        p_low = self.atm._calculate_adjusted_pressure(1013.25, 500)
        p_high = self.atm._calculate_adjusted_pressure(1013.25, 3000)
        self.assertLess(p_high, p_low)

    # ---------------------------------------------------------------
    # _calculate_vapor_pressure
    # ---------------------------------------------------------------
    def test_vapor_pressure_increases_with_temperature(self):
        e_cold = self.atm._calculate_vapor_pressure(0.0)
        e_warm = self.atm._calculate_vapor_pressure(20.0)
        self.assertLess(e_cold, e_warm)

    def test_vapor_pressure_at_zero(self):
        # At 0°C, saturation vapor pressure ≈ 6.1 hPa
        e = self.atm._calculate_vapor_pressure(0.0)
        self.assertAlmostEqual(e, 6.1, delta=0.2)

    # ---------------------------------------------------------------
    # calculate_dew_point
    # ---------------------------------------------------------------
    def test_dew_point_at_saturation(self):
        # RH=100 → dew point equals air temperature
        result = asyncio.run(self.atm.calculate_dew_point(20.0, 100.0))
        self.assertAlmostEqual(result, 20.0, delta=0.05)

    def test_dew_point_typical(self):
        # 15°C / 50% RH → dew point ≈ 4.6°C
        result = asyncio.run(self.atm.calculate_dew_point(15.0, 50.0))
        self.assertAlmostEqual(result, 4.6, delta=0.5)

    def test_dew_point_below_temperature(self):
        result = asyncio.run(self.atm.calculate_dew_point(30.0, 20.0))
        self.assertLess(result, 30.0)

    # ---------------------------------------------------------------
    # calculate_lifted_index
    # ---------------------------------------------------------------
    def test_lifted_index_in_range(self):
        c = self.clear
        result = asyncio.run(self.atm.calculate_lifted_index(
            temperature=c["temperature"], altitude=c["altitude"],
            dew_point_temperature=c["dew_point_temperature"],
            air_pressure_at_sea_level=c["air_pressure_at_sea_level"],
        ))
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result, -7.0)
        self.assertLessEqual(result, 7.0)

    def test_lifted_index_returns_none_on_missing(self):
        result = asyncio.run(self.atm.calculate_lifted_index(
            temperature=None, altitude=500.0,
            dew_point_temperature=5.0, air_pressure_at_sea_level=1013.25,
        ))
        self.assertIsNone(result)

    # ---------------------------------------------------------------
    # calculate_seeing
    # ---------------------------------------------------------------
    def test_seeing_clear_in_range(self):
        c = self.clear
        result = asyncio.run(self.atm.calculate_seeing(
            temperature=c["temperature"], humidity=c["humidity"],
            dew_point_temperature=c["dew_point_temperature"],
            wind_speed=c["wind_speed"], cloud_cover=c["cloud_cover"],
            altitude=c["altitude"], air_pressure_at_sea_level=c["air_pressure_at_sea_level"],
        ))
        self.assertIsNotNone(result)
        self.assertGreater(result, 0.0)
        self.assertLessEqual(result, 4.0)

    def test_seeing_worse_overcast(self):
        c, o = self.clear, self.overcast
        r_clear = asyncio.run(self.atm.calculate_seeing(
            temperature=c["temperature"], humidity=c["humidity"],
            dew_point_temperature=c["dew_point_temperature"],
            wind_speed=c["wind_speed"], cloud_cover=c["cloud_cover"],
            altitude=c["altitude"], air_pressure_at_sea_level=c["air_pressure_at_sea_level"],
        ))
        r_overcast = asyncio.run(self.atm.calculate_seeing(
            temperature=o["temperature"], humidity=o["humidity"],
            dew_point_temperature=o["dew_point_temperature"],
            wind_speed=o["wind_speed"], cloud_cover=o["cloud_cover"],
            altitude=o["altitude"], air_pressure_at_sea_level=o["air_pressure_at_sea_level"],
        ))
        # Larger arcsec value = worse seeing
        self.assertGreater(r_overcast, r_clear)

    def test_seeing_returns_none_on_missing(self):
        result = asyncio.run(self.atm.calculate_seeing(
            temperature=None, humidity=50.0, dew_point_temperature=5.0,
            wind_speed=2.0, cloud_cover=0.0, altitude=500.0,
            air_pressure_at_sea_level=1013.25,
        ))
        self.assertIsNone(result)

    # ---------------------------------------------------------------
    # calculate_fog_density
    # ---------------------------------------------------------------
    def test_fog_density_clear_is_low(self):
        result = asyncio.run(self.atm.calculate_fog_density(15.0, 50.0, 4.6, 2.0))
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)
        self.assertLess(result, 0.3)

    def test_fog_density_saturated_is_high(self):
        result = asyncio.run(self.atm.calculate_fog_density(10.0, 99.0, 9.8, 0.5))
        self.assertGreater(result, 0.3)

    def test_fog_density_wind_disperses_fog(self):
        result_calm = asyncio.run(self.atm.calculate_fog_density(10.0, 99.0, 9.8, 0.0))
        result_windy = asyncio.run(self.atm.calculate_fog_density(10.0, 99.0, 9.8, 15.0))
        self.assertGreater(result_calm, result_windy)

    # ---------------------------------------------------------------
    # magnitude_degradation
    # ---------------------------------------------------------------
    def test_magnitude_degradation_clear_in_range(self):
        c = self.clear
        result = asyncio.run(self.atm.magnitude_degradation(
            temperature=c["temperature"], humidity=c["humidity"],
            cloud_cover=c["cloud_cover"], wind_speed=c["wind_speed"],
            altitude=c["altitude"], dew_point_temperature=c["dew_point_temperature"],
            air_pressure_at_sea_level=c["air_pressure_at_sea_level"],
        ))
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_magnitude_degradation_worse_overcast(self):
        c, o = self.clear, self.overcast
        r_clear = asyncio.run(self.atm.magnitude_degradation(
            temperature=c["temperature"], humidity=c["humidity"],
            cloud_cover=c["cloud_cover"], wind_speed=c["wind_speed"],
            altitude=c["altitude"], dew_point_temperature=c["dew_point_temperature"],
            air_pressure_at_sea_level=c["air_pressure_at_sea_level"],
        ))
        r_overcast = asyncio.run(self.atm.magnitude_degradation(
            temperature=o["temperature"], humidity=o["humidity"],
            cloud_cover=o["cloud_cover"], wind_speed=o["wind_speed"],
            altitude=o["altitude"], dew_point_temperature=o["dew_point_temperature"],
            air_pressure_at_sea_level=o["air_pressure_at_sea_level"],
        ))
        self.assertGreater(r_overcast, r_clear)

    def test_magnitude_degradation_returns_none_on_missing(self):
        c = self.clear
        result = asyncio.run(self.atm.magnitude_degradation(
            temperature=None, humidity=c["humidity"],
            cloud_cover=c["cloud_cover"], wind_speed=c["wind_speed"],
            altitude=c["altitude"], dew_point_temperature=c["dew_point_temperature"],
            air_pressure_at_sea_level=c["air_pressure_at_sea_level"],
        ))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
