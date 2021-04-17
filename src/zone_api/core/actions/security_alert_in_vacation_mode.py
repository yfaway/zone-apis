from zone_api.alert import Alert
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action

SECURITY_EVENTS = [ZoneEvent.PARTITION_ARMED_AWAY, ZoneEvent.PARTITION_ARMED_STAY,
                   ZoneEvent.PARTITION_DISARMED_FROM_AWAY, ZoneEvent.PARTITION_DISARMED_FROM_STAY,
                   ZoneEvent.PARTITION_RECEIVE_ARM_STAY, ZoneEvent.PARTITION_RECEIVE_ARM_AWAY]
CONTACT_EVENTS = [ZoneEvent.DOOR_OPEN, ZoneEvent.DOOR_CLOSED, ZoneEvent.WINDOW_OPEN, ZoneEvent.WINDOW_CLOSED]


@action(events=SECURITY_EVENTS + CONTACT_EVENTS, external_events=CONTACT_EVENTS, devices=[AlarmPartition])
class SecurityAlertInVacationMode:
    """
    Send an info alert when the security arm state changes or a door/window is open/closed while in vacation mode.
    """

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info):
        zone_manager = event_info.get_zone_manager()

        if not zone_manager.is_in_vacation():
            return False

        if event_info.get_event_type() in SECURITY_EVENTS:
            alert_message = f'[Vacation] Security system state changed: {event_info.get_event_type().name}.'
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)
        else:
            zone = event_info.get_owning_zone()
            alert_message = f'[Vacation] {zone.get_name()} event: {event_info.get_event_type().name}.'
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)

        return True
