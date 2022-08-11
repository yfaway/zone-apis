import time

from zone_api import platform_encapsulator as pe
from zone_api.core.actions.alert_on_inactive_devices import AlertOnInactiveDevices
from zone_api.core.devices.deferred_auto_report_notification import DeferredAutoReportNotification
from zone_api.core.devices.motion_sensor import MotionSensor

from zone_api.core.event_info import EventInfo
from zone_api.core.map_parameters import MapParameters
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class AlertOnInactiveDevicesTest(DeviceTest):
    """ Unit tests for AlertOnInactiveDevices.py. """

    def setUp(self):
        items = [pe.create_switch_item('motion1'), pe.create_switch_item('motion2'),
                 pe.create_string_item("deferred-device-name"), pe.create_number_item("deferred-duration")]

        self.set_items(items)
        super(AlertOnInactiveDevicesTest, self).setUp()

        self.motion1 = MotionSensor(items[0])
        self.motion2 = MotionSensor(items[1]).set_use_wifi(True).set_auto_report(True)
        self.deferred_setting = DeferredAutoReportNotification(items[2], items[3])

        parameters = MapParameters({'AlertOnInactiveDevices.batteryPoweredPeriodInHours': 1,
                                    'AlertOnInactiveDevices.autoReportPeriodInHours': 1
                                    })
        self.action = AlertOnInactiveDevices(parameters)
        self.zone1 = Zone("Virtual", [self.motion1, self.motion2, self.deferred_setting])

        self.zm = create_zone_manager([self.zone1])

    def testOnAction_noInactiveBatteryDevice_noAlert(self):
        self.assert_no_inactive_devices(AlertOnInactiveDevices.Type.BATTERY_DEVICES)

    def testOnAction_noInactiveAutoReportWifiDevice_noAlert(self):
        self.assert_no_inactive_devices(AlertOnInactiveDevices.Type.AUTO_REPORT_WIFI_DEVICES)

    def testOnAction_oneInactiveBatteryDevice_sendAlert(self):
        self.motion1.last_activated_timestamp = time.time() - (2 * 3600)  # 10 secs ago
        self.motion2.update_last_activated_timestamp()

        self.assert_inactive_devices(AlertOnInactiveDevices.Type.BATTERY_DEVICES, "1 inactive battery devices")

    def testOnAction_oneInactiveAutoReportWifiDevice_sendAlert(self):
        self.motion1.update_last_activated_timestamp()
        self.motion2.last_activated_timestamp = time.time() - (2 * 3600)  # 10 secs ago

        self.assert_inactive_devices(AlertOnInactiveDevices.Type.AUTO_REPORT_WIFI_DEVICES,
                                     "1 inactive auto-report WiFi devices")

    def testOnAction_oneInactiveAutoReportWifiDeviceAndDeviceNotDeferred_sendAlert(self):
        self.motion1.update_last_activated_timestamp()
        self.motion2.last_activated_timestamp = time.time() - (2 * 3600)  # 10 secs ago

        pe.set_string_value(self.deferred_setting.get_item_name(), "invalid device name")
        pe.set_number_value(self.deferred_setting.get_all_items()[-1], 1)
        event_info = EventInfo(ZoneEvent.DEFERRED_NOTIFICATION_DEVICE_NAME_CHANGED, self.get_items()[3], self.zone1,
                               self.zm, pe.get_event_dispatcher(), None, self.deferred_setting)
        self.action.on_action(event_info)

        self.assert_inactive_devices(AlertOnInactiveDevices.Type.AUTO_REPORT_WIFI_DEVICES,
                                     "1 inactive auto-report WiFi devices")
        self.action._cancel_all_auto_report_defer_timer()

    def testOnAction_oneInactiveAutoReportWifiDeviceButDeviceDeferred_noAlert(self):
        self.motion1.update_last_activated_timestamp()
        self.motion2.last_activated_timestamp = time.time() - (2 * 3600)  # 10 secs ago

        pe.set_string_value(self.deferred_setting.get_item_name(), self.motion2.get_item_name())
        pe.set_number_value(self.deferred_setting.get_all_items()[-1], 1)
        event_info = EventInfo(ZoneEvent.DEFERRED_NOTIFICATION_DEVICE_NAME_CHANGED, self.get_items()[2], self.zone1,
                               self.zm, pe.get_event_dispatcher(), None, self.deferred_setting)
        self.action.on_action(event_info)

        value = self.action.on_action(self._get_timer_event(AlertOnInactiveDevices.Type.AUTO_REPORT_WIFI_DEVICES))
        self.assertTrue(value)
        self.assertTrue(self.zm.get_alert_manager()._lastEmailedSubject is None)
        self.action._cancel_all_auto_report_defer_timer()

    def assert_no_inactive_devices(self, custom_param):
        self.motion1.update_last_activated_timestamp()
        self.motion2.update_last_activated_timestamp()

        value = self.action.on_action(self._get_timer_event(custom_param))
        self.assertTrue(value)
        self.assertTrue(self.zm.get_alert_manager()._lastEmailedSubject is None)

    def assert_inactive_devices(self, custom_param, alert_subject: str):
        value = self.action.on_action(self._get_timer_event(custom_param))
        self.assertTrue(value)
        self.assertTrue(alert_subject in self.zm.get_alert_manager()._lastEmailedSubject)

    def _get_timer_event(self, custom_param):
        return EventInfo(ZoneEvent.TIMER, None, self.zone1, self.zm, pe.get_event_dispatcher(),
                         None, None, custom_param)
