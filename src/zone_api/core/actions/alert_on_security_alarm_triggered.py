from zone_api.alert import Alert
from zone_api.core.device import Device
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.security_aware_mixin import SecurityAwareMixin
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action


@action(events=[ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED], devices=[AlarmPartition])
class AlertOnSecurityAlarmTriggered:
    """ Send a critical alert if the security alarm is triggered. """

    def __init__(self):
        """ Ctor """
        self._notified = False

    def on_action(self, event_info):
        zone_manager = event_info.get_zone_manager()

        if event_info.get_device().is_in_alarm():
            self._notified = True

            description = ''
            for z in zone_manager.get_zones(): # type: Zone
                devices = [d for d in z.get_devices_by_type(SecurityAwareMixin) if d.is_tripped()]
                if len(devices) > 0:
                    description = f" ({z.get_name()} {type(devices[0]).__name__})"
                    break

            alert_message = f'Security system is on alarm{description}.'
            alert = Alert.create_critical_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)

        elif self._notified:
            alert_message = "Security system is NO LONGER in alarm"
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)
            self._notified = False

        return True
