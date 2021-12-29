from zone_api.alert import Alert
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.security_aware_mixin import SecurityAwareMixin
from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action


@action(events=[ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED, ZoneEvent.PARTITION_FIRE_ALARM_STATE_CHANGED],
        devices=[AlarmPartition])
class AlertOnSecurityAlarmTriggered:
    """ Send a critical alert if the security alarm is triggered. """

    def __init__(self):
        """ Ctor """
        self._general_alert = None
        self._fire_alert = None

    def on_action(self, event_info: EventInfo):
        zone_manager = event_info.get_zone_manager()
        # noinspection PyTypeChecker
        partition: AlarmPartition = event_info.get_device()

        if event_info.get_event_type() == ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED:
            if partition.is_in_alarm():
                description = ''
                for z in zone_manager.get_zones():  # type: Zone
                    devices = [d for d in z.get_devices_by_type(SecurityAwareMixin) if d.is_tripped()]
                    if len(devices) > 0:
                        description = f" ({z.get_name()} {type(devices[0]).__name__})"
                        break

                alert_message = f'Security system is on alarm{description}.'
                self._general_alert = Alert.create_critical_alert(alert_message)
                zone_manager.get_alert_manager().process_alert(self._general_alert, zone_manager)

            elif self._general_alert is not None:
                alert = Alert.create_info_alert("Security system is NO LONGER in alarm")
                zone_manager.get_alert_manager().process_alert(alert, zone_manager)
                self._general_alert.cancel()
        elif event_info.get_event_type() == ZoneEvent.PARTITION_FIRE_ALARM_STATE_CHANGED:
            if partition.is_in_fire_alarm():
                self._fire_alert = Alert.create_critical_alert('Security system is on FIRE alarm.')
                zone_manager.get_alert_manager().process_alert(self._fire_alert, zone_manager)
            elif self._fire_alert is not None:
                alert = Alert.create_info_alert("Security system is NO LONGER in FIRE alarm")
                zone_manager.get_alert_manager().process_alert(alert, zone_manager)
                self._fire_alert.cancel()

        return True
