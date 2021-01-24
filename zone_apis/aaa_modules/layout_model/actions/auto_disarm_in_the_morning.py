from aaa_modules import security_manager as sm
from aaa_modules.layout_model.devices.activity_times import ActivityTimes
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition
from aaa_modules import platform_encapsulator as pe


@action(events=[ZoneEvent.MOTION], devices=[AlarmPartition, MotionSensor])
class AutoDisarmInTheMorning:
    """
    Automatically disarm the security system when the motion sensor in the zone containing the
    security panel is triggered during the wake-up hour range.
    """

    def on_action(self, event_info):
        events = event_info.get_event_dispatcher()
        zone_manager = event_info.get_zone_manager()

        if not sm.is_armed_stay(zone_manager):
            return False

        activities = zone_manager.get_devices_by_type(ActivityTimes)
        if len(activities) == 0:
            pe.log_warning(f"{self.__class__.__name__}: missing activities time; can't determine wake-up time.")
            return False

        activity = activities[0]
        if activity.is_wakeup_time():
            sm.disarm(zone_manager, events)
            return True
        else:
            return False
