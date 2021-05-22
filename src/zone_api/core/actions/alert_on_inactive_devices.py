from enum import unique, Enum

from zone_api.alert import Alert
from zone_api import platform_encapsulator as pe
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action


@action(events=[ZoneEvent.TIMER], devices=[], zone_name_pattern='.*Virtual.*')
class AlertOnInactiveDevices:
    """
    Send an admin info alert if a battery-powered or an auto-report device hasn't got any update in the specified
    duration.
    There are different thresholds for these types of devices as battery-powered devices tend to not auto-report (cause
    rapid battery drain). As such, the inactivity timer for those devices are much bigger than for auto-report devices.
    """

    @unique
    class Type(Enum):
        BATTERY_DEVICES = 1
        AUTO_REPORT_WIFI_DEVICES = 2

    def __init__(self, battery_powered_period_in_hours: float = 3 * 24,
                 auto_report_period_in_hours: float = 0.25):
        """
        Ctor

        :raise ValueError: if any parameter is invalid
        """
        if battery_powered_period_in_hours <= 0:
            raise ValueError('battery_powered_period_in_hours must be positive')

        if auto_report_period_in_hours <= 0:
            raise ValueError('auto_report_period_in_hours must be positive')

        self._battery_powered_period_in_hours = battery_powered_period_in_hours
        self._auto_report_period_in_hours = auto_report_period_in_hours

    def on_startup(self, event_info: EventInfo):

        def battery_device_timer_handler():
            self.on_action(
                self.create_timer_event_info(event_info,
                                             AlertOnInactiveDevices.Type.BATTERY_DEVICES))

        def auto_report_device_timer_handler():
            self.on_action(
                self.create_timer_event_info(event_info,
                                             AlertOnInactiveDevices.Type.AUTO_REPORT_WIFI_DEVICES))

        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every(self._battery_powered_period_in_hours).hours.do(battery_device_timer_handler)
        scheduler.every(self._auto_report_period_in_hours).hours.do(auto_report_device_timer_handler)

    def on_action(self, event_info):
        zone_manager = event_info.get_zone_manager()

        if event_info.get_custom_parameter() == AlertOnInactiveDevices.Type.BATTERY_DEVICES:
            self._check_and_send_alert(zone_manager, self.get_inactive_battery_devices,
                                       "battery", self._battery_powered_period_in_hours)
        elif event_info.get_custom_parameter() == AlertOnInactiveDevices.Type.AUTO_REPORT_WIFI_DEVICES:
            self._check_and_send_alert(zone_manager, self.get_inactive_auto_report_devices,
                                       "auto-report WiFi", self._auto_report_period_in_hours)
        else:
            raise RuntimeError("Invalid state.")

        return True

    # noinspection PyMethodMayBeStatic
    def _check_and_send_alert(self, zone_manager, check_function, device_type_string, threshold_in_hours):
        inactive_devices = check_function(zone_manager, threshold_in_hours * 3600)

        if len(inactive_devices) > 0:
            subject = "{} inactive {} devices".format(
                len(inactive_devices), device_type_string)
            body = f"The following devices haven't triggered in the last {threshold_in_hours} hours\r\n  - "
            body += "\r\n  - ".join(inactive_devices)

            alert = Alert.create_info_alert(subject, body)
            zone_manager.get_alert_manager().process_admin_alert(alert)
        else:
            pe.log_info(f"No inactive {device_type_string} devices detected.")

    # noinspection PyMethodMayBeStatic
    def get_inactive_battery_devices(self, zone_manager, threshold_in_seconds):
        """
        :rtype: list(str) the list of inactive devices
        """
        inactive_device_name = []
        for z in zone_manager.get_zones():
            battery_devices = [d for d in z.get_devices() if d.is_battery_powered()]

            for d in battery_devices:
                if not d.was_recently_activated(threshold_in_seconds):
                    inactive_device_name.append(f"{z.get_name()}: {d.get_item_name()}")

        return inactive_device_name

    # noinspection PyMethodMayBeStatic
    def get_inactive_auto_report_devices(self, zone_manager, threshold_in_seconds):
        """
        :rtype: list(str) the list of auto-reported WiFi devices that haven't
            sent anything in the specified number of seconds.
        """
        inactive_device_name = []
        for z in zone_manager.get_zones():
            auto_report_devices = [d for d in z.get_devices() if d.is_auto_report()]

            for d in auto_report_devices:
                if not d.was_recently_activated(threshold_in_seconds):
                    inactive_device_name.append(f"{z.get_name()}: {d.get_item_name()}")

        return inactive_device_name
