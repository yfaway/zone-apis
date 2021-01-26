import time

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.alert_on_inactive_devices import AlertOnInactiveDevices
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor

from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone
from aaa_modules.layout_model.zone_event import ZoneEvent
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager


class AlertOnInactiveDevicesTest(DeviceTest):
    """ Unit tests for AlertOnInactiveDevices.py. """

    def setUp(self):
        items = [pe.create_switch_item('motion1'), pe.create_switch_item('motion2')]

        self.set_items(items)
        super(AlertOnInactiveDevicesTest, self).setUp()

        self.motion1 = MotionSensor(items[0], True)
        self.motion2 = MotionSensor(items[1]).set_use_wifi(True).set_auto_report(True)

        self.action = AlertOnInactiveDevices(1, 1)
        self.zone1 = Zone("foyer", [self.motion1, self.motion2])

        self.zm = create_zone_manager([self.zone1])

    def testOnAction_noInactiveBatteryDevice_noAlert(self):
        self.action._battery = True
        self.assert_no_inactive_devices()

    def testOnAction_noInactiveAutoReportWifiDevice_noAlert(self):
        self.action._wifi = True
        self.assert_no_inactive_devices()

    def testOnAction_oneInactiveBatteryDevice_noAlert(self):
        self.action._battery = True
        self.motion1.last_activated_timestamp = time.time() - (2 * 3600)  # 10 secs ago
        self.motion2._update_last_activated_timestamp()

        self.assert_inactive_devices("1 inactive battery devices")

    def testOnAction_oneInactiveAutoReportWifiDevice_noAlert(self):
        self.action._wifi = True
        self.motion1._update_last_activated_timestamp()
        self.motion2.last_activated_timestamp = time.time() - (2 * 3600)  # 10 secs ago

        self.assert_inactive_devices("1 inactive auto-report WiFi devices")

    def assert_no_inactive_devices(self):
        self.motion1._update_last_activated_timestamp()
        self.motion2._update_last_activated_timestamp()

        event_info = EventInfo(ZoneEvent.TIMER, None, self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.zm.get_alert_manager()._lastEmailedSubject is None)

    def assert_inactive_devices(self, alert_subject: str):
        event_info = EventInfo(ZoneEvent.TIMER, None, self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(alert_subject in self.zm.get_alert_manager()._lastEmailedSubject)
