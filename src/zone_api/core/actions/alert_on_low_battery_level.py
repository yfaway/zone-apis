from typing import List

from zone_api.alert import Alert
from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action


@action(events=[ZoneEvent.TIMER], devices=[], zone_name_pattern='.*Virtual.*')
class AlertOnLowBatteryLevel:
    """ Send an admin info alert if a device's battery level is below a threshold. """

    BATTERY_PERCENTAGE_THRESHOLD = 15

    def __init__(self, period_in_hours: int = 3 * 24, battery_percentage_threshold=BATTERY_PERCENTAGE_THRESHOLD):
        """
        Ctor

        :raise ValueError: if any parameter is invalid
        """
        if period_in_hours <= 0:
            raise ValueError('period_in_hours must be positive')

        if battery_percentage_threshold < 0 or battery_percentage_threshold > 100:
            raise ValueError('battery_percentage_threshold must be a percentage')

        self._period_in_hours = period_in_hours
        self._battery_percentage_threshold = battery_percentage_threshold

    def on_startup(self, event_info: EventInfo):

        def battery_device_timer_handler():
            self.on_action(self.create_timer_event_info(event_info))

        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every(self._period_in_hours).hours.do(battery_device_timer_handler)

    def on_action(self, event_info):
        zone_manager = event_info.get_zone_manager()

        low_battery_devices = []
        for z in zone_manager.get_zones():
            battery_devices: List[Device] = [d for d in z.get_devices() if d.is_battery_powered()]

            for d in battery_devices:
                percentage = d.get_battery_percentage()
                if percentage is not None and percentage <= self._battery_percentage_threshold:
                    low_battery_devices.append(f"{z.get_name()}: {d.get_item_name()}")

        if len(low_battery_devices) > 0:
            subject = "{} low battery devices".format(len(low_battery_devices))
            body = f"The following devices have the battery levels below {self._battery_percentage_threshold}%\r\n  - "
            body += "\r\n  - ".join(low_battery_devices)

            alert = Alert.create_info_alert(subject, body)
            zone_manager.get_alert_manager().process_admin_alert(alert)
        else:
            pe.log_info(f"No devices with low battery percentage.")

        return True
