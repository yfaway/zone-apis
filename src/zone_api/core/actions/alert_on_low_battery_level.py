from typing import List

from zone_api.alert import Alert
from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device
from zone_api.core.event_info import EventInfo
from zone_api.core.parameters import ParameterConstraint, positive_number_validator, percentage_validator, Parameters
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action


@action(events=[ZoneEvent.TIMER], devices=[], zone_name_pattern='.*Virtual.*')
class AlertOnLowBatteryLevel(Action):
    """ Send an admin info alert if a device's battery level is below a threshold. """

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [ParameterConstraint.optional('alertPeriodInHours', positive_number_validator, "must be positive"),
                ParameterConstraint.optional('batteryPercentageThreshold', percentage_validator, "must be a percentage")
                ]

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._period_in_hours = self.parameters().get(self, 'alertPeriodInHours', 3 * 24)
        self._battery_percentage_threshold = self.parameters().get(self, 'alertPeriodInHours', 15)

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
            self.send_notification(zone_manager, alert)
        else:
            pe.log_info(f"No devices with low battery percentage.")

        return True
