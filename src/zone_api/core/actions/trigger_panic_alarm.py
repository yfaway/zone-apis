from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.ikea_remote_control import IkeaRemoteControl
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action

EVENTS = [ZoneEvent.MANUALLY_TRIGGER_FIRE_ALARM, ZoneEvent.MANUALLY_TRIGGER_AMBULANCE_ALARM,
          ZoneEvent.MANUALLY_TRIGGER_POLICE_ALARM, ZoneEvent.CANCEL_PANIC_ALARM]


@action(events=EVENTS, devices=[IkeaRemoteControl])
class TriggerPanicAlarm:
    """
    Trigger a fire, ambulance or police panic alarm. Also support cancelling the panic alarm (will restore the arming
    state if system was armed.
    """

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info: EventInfo):
        zone_manager = event_info.get_zone_manager()
        partition: AlarmPartition = zone_manager.get_first_device_by_type(AlarmPartition)
        event_dispatcher = event_info.get_event_dispatcher()

        if event_info.get_event_type() == ZoneEvent.MANUALLY_TRIGGER_FIRE_ALARM:
            partition.trigger_fire_alarm(event_dispatcher)
        elif event_info.get_event_type() == ZoneEvent.MANUALLY_TRIGGER_AMBULANCE_ALARM:
            partition.trigger_ambulance_alarm(event_dispatcher)
        elif event_info.get_event_type() == ZoneEvent.MANUALLY_TRIGGER_POLICE_ALARM:
            partition.trigger_police_alarm(event_dispatcher)
        elif event_info.get_event_type() == ZoneEvent.CANCEL_PANIC_ALARM:
            if partition.is_armed_stay():
                partition.cancel_panic_alarm(event_dispatcher)
                partition.arm_stay(event_dispatcher)
            elif partition.is_armed_away():
                partition.cancel_panic_alarm(event_dispatcher)
                partition.arm_away(event_dispatcher)
            else:
                partition.cancel_panic_alarm(event_dispatcher)

        return True
