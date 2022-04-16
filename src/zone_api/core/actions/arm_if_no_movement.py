from typing import List

from zone_api import security_manager as sm
from zone_api.core.devices.activity_times import ActivityTimes
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.devices.network_presence import NetworkPresence
from zone_api.core.event_info import EventInfo
from zone_api.core.parameters import positive_number_validator, ParameterConstraint, Parameters
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action
from zone_api.core.devices.alarm_partition import AlarmPartition


@action(events=[ZoneEvent.TIMER], devices=[AlarmPartition, MotionSensor])
class ArmIfNoMovement(Action):
    """
    Automatically arm-stay the house if there has been no occupancy event in the last x minutes.
    Use case: user is at home but perhaps taking a nap. Accompanied disarm rule will automatically
    disarm on internal motion sensor.
    If the house is in vacation mode, arm away instead.
    """

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return [ParameterConstraint.optional('unoccupiedDurationInMinutes', positive_number_validator)]

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._unoccupied_duration_in_minutes = self.parameters().get(self, self.supported_parameters()[0].name(), 30)

    def on_startup(self, event_info: EventInfo):
        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every(15).minutes.do(lambda: self.on_action(self.create_timer_event_info(event_info)))

    def on_action(self, event_info):
        events = event_info.get_event_dispatcher()
        zone_manager = event_info.get_zone_manager()

        if not sm.is_unarmed(zone_manager):
            return False

        activity = zone_manager.get_first_device_by_type(ActivityTimes)
        if activity is None:
            self.log_warning("Missing activities time; can't determine wake-up time.")
            return False

        if activity.is_auto_arm_stay_time():  # taken care by another deterministic rule.
            return False

        for z in zone_manager.get_zones():
            (occupied, device) = z.is_occupied([NetworkPresence], self._unoccupied_duration_in_minutes * 60)
            if occupied:
                return False

        if zone_manager.is_in_vacation():
            sm.arm_away(zone_manager, events)
        else:
            sm.arm_stay(zone_manager, events)

        return True
