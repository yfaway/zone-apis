from aaa_modules.alert import Alert
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.action import action


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
            alert_message = f'Security system is on alarm.'
            alert = Alert.create_critical_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)

        elif self._notified:
            alert_message = "Security system is NO LONGER in alarm"
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)
            self._notified = False

        return True
