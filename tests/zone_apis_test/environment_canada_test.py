import unittest

from aaa_modules.environment_canada import EnvCanada


class EnvCanadaTest(unittest.TestCase):
    """ Unit tests for environment_canada.py. """
    def testRetrieveHourlyForecast_hourCountAboveThreshold_throwsException(self):
        with self.assertRaises(ValueError) as cm:
            EnvCanada.retrieve_hourly_forecast('Ottawa', 25)

        self.assertEqual("hourCount must be between 1 and 24.", cm.exception.args[0])

    def testRetrieveHourlyForecast_hourCountBelowThreshold_throwsException(self):
        with self.assertRaises(ValueError) as cm:
            EnvCanada.retrieve_hourly_forecast('Ottawa', 0)

        self.assertEqual("hourCount must be between 1 and 24.", cm.exception.args[0])

    def testRetrieveHourlyForecast_invalidCity_throwsException(self):
        with self.assertRaises(ValueError) as cm:
            EnvCanada.retrieve_hourly_forecast('blah')

        self.assertEqual("Can't map city name to URL for blah", cm.exception.args[0])

    def testRetrieveHourlyForecast_validCity_returnsForecast(self):
        forecasts = EnvCanada.retrieve_hourly_forecast('Ottawa')
        self.assertTrue(len(forecasts) > 0)

        for forecast in forecasts:
            self.assertTrue(forecast.getForecastTime() >= 0)
            self.assertTrue(len(forecast.getCondition()) > 0)
            self.assertTrue(len(forecast.getPrecipationProbability()) > 0)

    def testRetrieveHourlyForecast_validUrl_returnsForecast(self):
        forecasts = EnvCanada.retrieve_hourly_forecast(
            'https://www.weather.gc.ca/forecast/hourly/on-118_metric_e.html',
            24)
        self.assertEqual(24, len(forecasts))

        for forecast in forecasts:
            self.assertTrue(forecast.getForecastTime() >= 0)
            self.assertTrue(len(forecast.getCondition()) > 0)
            self.assertTrue(len(forecast.getPrecipationProbability()) > 0)

    def testRetrieveAlert_validCity_returnsForecast(self):
        alert, url, raw_data = EnvCanada.retrieve_alert('ottawa')
        self.assertTrue(len(url) > 0)

        if 'No Alerts in effect.' in raw_data:
            self.assertTrue(alert is None)
        else:
            self.assertTrue(len(alert) > 0)
