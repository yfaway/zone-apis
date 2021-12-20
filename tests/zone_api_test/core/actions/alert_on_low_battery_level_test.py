import time

from zone_api import platform_encapsulator as pe
from zone_api.core.actions.alert_on_inactive_devices import AlertOnInactiveDevices
from zone_api.core.actions.alert_on_low_battery_level import AlertOnLowBatteryLevel
from zone_api.core.devices.motion_sensor import MotionSensor

from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class AlertOnLowBatteryLevelTest(DeviceTest):
    """ Unit tests for AlertOnLowBatteryLevel. """

    def setUp(self):
        items = [pe.create_switch_item('motion1'), pe.create_number_item('percentage')]

        self.set_items(items)
        super(AlertOnLowBatteryLevelTest, self).setUp()

        self.motion1 = MotionSensor(items[0], True, None, items[1])

        self.action = AlertOnLowBatteryLevel()
        self.zone1 = Zone("foyer", [self.motion1])

        self.zm = create_zone_manager([self.zone1])

    def testOnAction_noInactiveBatteryDevice_noAlert(self):
        pe.set_number_value(self.get_items()[1], 90)
        self.assert_no_low_battery_devices()

    def testOnAction_oneLowBatteryDevice_sendAlert(self):
        pe.set_number_value(self.get_items()[1], 10)
        self.assert_low_battery_devices()

    def assert_no_low_battery_devices(self):
        event_info = EventInfo(ZoneEvent.TIMER, None, self.zone1, self.zm, pe.get_event_dispatcher(), None, None)
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.zm.get_alert_manager()._lastEmailedSubject is None)

    def assert_low_battery_devices(self):
        event_info = EventInfo(ZoneEvent.TIMER, None, self.zone1, self.zm, pe.get_event_dispatcher(), None, None)
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue("1 low battery devices" in self.zm.get_alert_manager()._lastEmailedSubject)
