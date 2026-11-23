import math
import unittest

import weather_calculations as wc


class WeatherCalculationTests(unittest.TestCase):
    def test_provo_recorded_fixture(self):
        temperatures_f = [47.2, 48.1, 47.7]
        sustained_mph = [2.8, 2.1, 2.9]
        gust_mph = [6.3, 5.4, 5.6]
        precipitation = [0.0, 0.0, 0.0]

        crane = wc.crane_rating(max(max(sustained_mph), max(gust_mph)), 15.0)
        concrete = wc.concrete_rating(min(temperatures_f), 35.0)
        roofing = wc.roofing_rating(max(precipitation))

        self.assertEqual(crane.status, "Go")
        self.assertEqual(concrete.status, "Go")
        self.assertEqual(roofing.status, "Go")

    def test_crane_threshold_property_and_boundaries(self):
        limit = 15.0
        self.assertEqual(wc.crane_rating(11.99, limit).status, "Go")
        self.assertEqual(wc.crane_rating(12.0, limit).status, "Caution")
        self.assertEqual(wc.crane_rating(14.99, limit).status, "Caution")
        self.assertEqual(wc.crane_rating(15.0, limit).status, "No-Go")

    def test_unit_round_trip_property(self):
        temperature_c = 20.0
        temperature_round_trip = wc.fahrenheit_to_celsius(wc.celsius_to_fahrenheit(temperature_c))
        speed_mph = 25.0
        speed_round_trip = wc.kmh_to_mph(wc.mph_to_kmh(speed_mph))
        self.assertTrue(math.isclose(temperature_round_trip, temperature_c, rel_tol=0, abs_tol=1e-9))
        self.assertTrue(math.isclose(speed_round_trip, speed_mph, rel_tol=0, abs_tol=1e-9))


if __name__ == "__main__":
    unittest.main()
