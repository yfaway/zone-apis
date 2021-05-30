from unittest.mock import patch

from zone_api import platform_encapsulator as pe
from zone_api.core.actions.send_weather_alert import SendWeatherAlert
from zone_api.core.devices.weather import Weather
from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone, Level
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class SendWeatherAlertTest(DeviceTest):
    """ Unit tests for SendWeatherAlert. """

    MOCKED_OBJECT_PATH = 'zone_api.core.actions.send_weather_alert.EnvCanada'

    def setUp(self):
        items = [pe.create_number_item('weather-temp'), pe.create_number_item('weather-humidity'),
                 pe.create_string_item('weather-condition'), pe.create_string_item('weather-alert')]
        self.set_items(items)
        super(SendWeatherAlertTest, self).setUp()

        self.alert_item = items[-1]
        self.action = SendWeatherAlert()
        self.weather = Weather(*items)
        self.zone1 = Zone('office', [], Level.FIRST_FLOOR) \
            .add_action(self.action) \
            .add_device(self.weather)

        pe.set_string_value(self.alert_item, "Bad weather")

        self.zm = create_zone_manager([self.zone1])

    def testOnAction_alertExists_returnsTrueAndSendAlert(self):
        description = "Storm coming"
        url = "https://here.com"

        with patch(SendWeatherAlertTest.MOCKED_OBJECT_PATH) as mock_requests:
            mock_requests.retrieve_alert.return_value = description, url, None

            self.assertTrue(self.invoke_action())
            self.assertTrue(pe.get_string_value(self.alert_item) in self.zm.get_alert_manager()._lastEmailedSubject)
            self.assertTrue(description in self.zm.get_alert_manager()._lastEmailedBody)
            self.assertTrue(url in self.zm.get_alert_manager()._lastEmailedBody)

    def testOnAction_noRemoteAlertExists_returnsFalse(self):
        url = "https://here.com"

        with patch(SendWeatherAlertTest.MOCKED_OBJECT_PATH) as mock_requests:
            mock_requests.retrieve_alert.return_value = None, url, None

            self.assertFalse(self.invoke_action())

    def invoke_action(self) -> bool:
        event_info = EventInfo(ZoneEvent.WEATHER_ALERT_CHANGED, self.alert_item, self.zone1, self.zm,
                               pe.get_event_dispatcher(), None, self.weather)
        return self.action.on_action(event_info)
