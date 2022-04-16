from unittest.mock import patch, MagicMock

from zone_api import platform_encapsulator as pe
from zone_api.core.devices.weather import Weather
from zone_api.core.event_info import EventInfo
from zone_api.core.map_parameters import MapParameters
from zone_api.core.zone import Zone, Level
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


# The remaining code mocks the feedparser module.
entry1 = Zone
entry1.title = "N/A"
entry1.link = "https://not-an-alert-link.ca"
entry1.published_parsed = (2002, 9, 7, 0, 0, 1, 5, 250, 0)

entry2 = Zone
entry2.title = "N/A"
entry2.link = 'https://www.weather.gc.ca/warnings/report_e.html?on41'
entry2.published_parsed = (2002, 9, 7, 0, 0, 1, 5, 250, 0)

feed = Zone
feed.entries = [entry1, entry2]
mock_request = MagicMock()
mock_request.parse = MagicMock(return_value=feed)
with patch.dict('sys.modules', feedparser=mock_request):
    from zone_api.core.actions.send_weather_alert import SendWeatherAlert


class SendWeatherAlertTest(DeviceTest):
    """ Unit tests for SendWeatherAlert. """

    MOCKED_OBJECT_PATH = 'zone_api.core.actions.send_weather_alert.EnvCanada'

    def setUp(self):
        items = [pe.create_number_item('weather-temp'), pe.create_number_item('weather-humidity'),
                 pe.create_string_item('weather-condition'), pe.create_string_item('weather-alert'),
                 pe.create_datetime_item('weather-date')]
        self.set_items(items)
        super(SendWeatherAlertTest, self).setUp()

        self.alert_item = items[-2]
        self.action = SendWeatherAlert(MapParameters({}))
        self.weather = Weather(*items)
        self.zone1 = Zone('office', [], Level.FIRST_FLOOR) \
            .add_action(self.action) \
            .add_device(self.weather)

        pe.set_string_value(self.alert_item, "Bad weather")

        self.zm = create_zone_manager([self.zone1])

    def testHasNewAlert_noAlert_returnsFalse(self):
        self.weather._set_alert_title("N/A")

        has_alert, _ = self.action._has_new_alert(self.weather)
        self.assertFalse(has_alert)

    def testHasNewAlert_newAlert_returnsFalse(self):
        self.weather._set_alert_title("")

        has_alert, alert_url = self.action._has_new_alert(self.weather)
        self.assertTrue(has_alert)
        self.assertEqual(alert_url, entry2.link)
        self.assertEqual(self.weather.get_alert_title(), entry2.title)

    def testOnAction_alertExists_returnsTrueAndSendAlert(self):
        description = "Storm coming"
        url = "https://here.com"
        self.action._has_new_alert = MagicMock(return_value=(True, 'http://blah.com'))

        with patch(SendWeatherAlertTest.MOCKED_OBJECT_PATH) as mock_requests:
            mock_requests.retrieve_alert.return_value = description, url, None

            self.assertTrue(self.invoke_action())
            self.assertTrue(pe.get_string_value(self.alert_item) in self.zm.get_alert_manager()._lastEmailedSubject)
            self.assertTrue(description in self.zm.get_alert_manager()._lastEmailedBody)
            self.assertTrue(url in self.zm.get_alert_manager()._lastEmailedBody)

    def testOnAction_noRemoteAlertExists_returnsFalse(self):
        url = "https://here.com"
        self.action._has_new_alert = MagicMock(return_value=(True, 'http://blah.com'))

        with patch(SendWeatherAlertTest.MOCKED_OBJECT_PATH) as mock_requests:
            mock_requests.retrieve_alert.return_value = None, url, None

            self.assertFalse(self.invoke_action())

    def invoke_action(self) -> bool:
        event_info = EventInfo(ZoneEvent.TIMER, self.alert_item, self.zone1, self.zm,
                               pe.get_event_dispatcher(), None, self.weather)
        return self.action.on_action(event_info)
