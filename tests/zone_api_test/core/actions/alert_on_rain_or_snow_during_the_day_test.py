from unittest.mock import patch

from zone_api import platform_encapsulator as pe
from zone_api.core.actions.alert_on_rain_or_snow_during_the_day import AlertOnRainOrSnowDuringTheDay
from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone, Level
from zone_api.core.zone_event import ZoneEvent
from zone_api.environment_canada import Forecast
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class AlertOnRainOrSnowDuringTheDayTest(DeviceTest):
    """ Unit tests for AlertOnRainOrSnowDuringTheDay. """

    MOCKED_OBJECT_PATH = "zone_api.core.actions.alert_on_rain_or_snow_during_the_day.EnvCanada"

    def setUp(self):
        items = [pe.create_number_item('weather-temp')]
        self.set_items(items)
        super(AlertOnRainOrSnowDuringTheDayTest, self).setUp()

        self.action = AlertOnRainOrSnowDuringTheDay()
        self.zone1 = Zone('Virtual', [], Level.FIRST_FLOOR) \
            .add_action(self.action)
        self.zm = create_zone_manager([self.zone1])

    def testOnAction_forecastRain_returnsTrueAndSendAlert(self):
        with patch(AlertOnRainOrSnowDuringTheDayTest.MOCKED_OBJECT_PATH) as mock_env_canada:
            mock_env_canada.retrieve_hourly_forecast.return_value = [
                Forecast(10, 25, "Rain", "High", "")
            ]

            self.assertTrue(self.invoke_action())
            self.assertTrue("Possible precipitation" in self.zm.get_alert_manager()._lastEmailedSubject)

    def testOnAction_noRainForecast_returnsFalse(self):
        with patch(AlertOnRainOrSnowDuringTheDayTest.MOCKED_OBJECT_PATH) as mock_env_canada:
            mock_env_canada.retrieve_hourly_forecast.return_value = [
                Forecast(10, 25, "Clear", "Nil", "")
            ]

            self.assertFalse(self.invoke_action())

    def invoke_action(self) -> bool:
        event_info = EventInfo(ZoneEvent.TIMER, self.get_items()[0], self.zone1, self.zm,
                               pe.get_event_dispatcher())
        return self.action.on_action(event_info)
