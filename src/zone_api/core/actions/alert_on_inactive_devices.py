from enum import unique, Enum
from threading import Timer
from typing import List

from zone_api.alert import Alert
from zone_api import platform_encapsulator as pe
from zone_api.core.devices.deferred_auto_report_notification import DeferredAutoReportNotification
from zone_api.core.devices.flash_message import FlashMessage
from zone_api.core.event_info import EventInfo
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.parameters import ParameterConstraint, positive_number_validator, Parameters
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action


@action(events=[ZoneEvent.TIMER, ZoneEvent.DEFERRED_NOTIFICATION_DEVICE_NAME_CHANGED], devices=[],
        zone_name_pattern='.*Virtual.*')
class AlertOnInactiveDevices(Action):
    """
    Send an admin info alert if a battery-powered or an auto-report device hasn't got any update in the specified
    duration.
    There are different thresholds for these types of devices as battery-powered devices tend to not auto-report (cause
    rapid battery drain). As such, the inactivity timer for those devices are much bigger than for auto-report devices.
    This action also handles the UI interface to defer auto-report devices for a specific period.
    """

    @unique
    class Type(Enum):
        BATTERY_DEVICES = 1
        AUTO_REPORT_WIFI_DEVICES = 2

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [ParameterConstraint.optional(
                   'batteryPoweredPeriodInHours', positive_number_validator, "must be positive"),
                   ParameterConstraint.optional('autoReportPeriodInHours', positive_number_validator,
                                                "must be positive")]

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._deferred_auto_report_devices = {}

        self._battery_powered_period_in_hours = self.parameters().get(self, 'batteryPoweredPeriodInHours', 3 * 24)
        self._auto_report_period_in_hours = self.parameters().get(self, 'autoReportPeriodInHours', 1 * 24)

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

        # Set some initial values.
        zm = event_info.get_zone_manager()
        setting: DeferredAutoReportNotification = zm.get_first_device_by_type(DeferredAutoReportNotification)
        if setting is not None:
            pe.set_number_value(setting.duration_in_hour_item_name, 0)
            pe.set_string_value(setting.get_item_name(), '')

    def on_action(self, event_info):
        zone_manager = event_info.get_zone_manager()

        if event_info.get_event_type() == ZoneEvent.TIMER:
            if event_info.get_custom_parameter() == AlertOnInactiveDevices.Type.BATTERY_DEVICES:
                self._check_and_send_alert(zone_manager, self.get_inactive_battery_devices,
                                           "battery", self._battery_powered_period_in_hours)
            elif event_info.get_custom_parameter() == AlertOnInactiveDevices.Type.AUTO_REPORT_WIFI_DEVICES:
                self._check_and_send_alert(zone_manager, self.get_inactive_auto_report_devices,
                                           "auto-report WiFi", self._auto_report_period_in_hours)
            else:
                raise RuntimeError("Invalid state.")

        elif event_info.get_event_type() == ZoneEvent.DEFERRED_NOTIFICATION_DEVICE_NAME_CHANGED:
            # noinspection PyTypeChecker
            self._start_auto_report_defer_timer(zone_manager, event_info.get_device())

        return True

    def _start_auto_report_defer_timer(self, zone_manager: 'ImmutableZoneManager',
                                       setting: DeferredAutoReportNotification):
        """
        Creates the timer to defer auto-report notification.
        """

        if len(setting.device_name) == 0:
            return

        def remove_deferral():
            self._deferred_auto_report_devices.pop(setting.device_name)

        # remove existing deferral if any
        if setting.device_name in self._deferred_auto_report_devices.keys():
            timer: Timer = self._deferred_auto_report_devices.pop(setting.device_name)
            if timer.is_alive():
                timer.cancel()

        duration_in_secs = setting.deferred_duration_in_hours * 3600
        timer = Timer(duration_in_secs, remove_deferral)
        timer.start()

        self._deferred_auto_report_devices[setting.device_name] = timer
        msg = f"Defer auto-report error reporting for device '{setting.device_name} for " \
              f"{setting.deferred_duration_in_hours} hours"
        self.log_info(msg)

        # update UI
        flash_message: FlashMessage = zone_manager.get_first_device_by_type(FlashMessage)
        if flash_message:
            flash_message.set_value(msg)

        # reset
        pe.set_string_value(setting.get_item_name(), '')

    def _cancel_all_auto_report_defer_timer(self):
        for timer in self._deferred_auto_report_devices.values():
            if timer.is_alive:
                timer.cancel()

        self._deferred_auto_report_devices.clear()

    # noinspection PyMethodMayBeStatic
    def _check_and_send_alert(self, zone_manager, check_function, device_type_string, threshold_in_hours):
        inactive_devices = check_function(zone_manager, threshold_in_hours * 3600)

        if len(inactive_devices) > 0:
            subject = "{} inactive {} devices".format(
                len(inactive_devices), device_type_string)
            body = f"<p>The following devices haven't triggered in the last {threshold_in_hours} hours:</p>\r\n"
            body += "<ul>\r\n"
            for device_name in inactive_devices:
                body += f"  <li>{device_name}</li>\r\n"
            body += "</ul>\r\n"

            alert = Alert.create_info_alert(subject, body)
            self.send_notification(zone_manager, alert)
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
        :rtype: list(str) the list of auto-reported devices that haven't
            sent anything in the specified number of seconds.
        """
        inactive_device_name = []
        for z in zone_manager.get_zones():
            auto_report_devices = [d for d in z.get_devices() if d.is_auto_report()]

            for d in auto_report_devices:
                if not d.was_recently_activated(threshold_in_seconds) \
                        and d.get_item_name() not in self._deferred_auto_report_devices.keys():
                    inactive_device_name.append(f"{z.get_name()}: {d.get_item_name()}")

        return inactive_device_name
