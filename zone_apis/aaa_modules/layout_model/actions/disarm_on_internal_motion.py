from aaa_modules import security_manager as sm
from aaa_modules.layout_model.devices.activity_times import ActivityTimes
from aaa_modules.layout_model.devices.contact import Door
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition


@action(events=[ZoneEvent.MOTION], devices=[AlarmPartition, MotionSensor])
class DisarmOnInternalMotion:
    """
    Automatically disarm the security system when the motion sensor in the zone containing the
    security panel is triggered and the current time is not in the auto-arm-stay or sleep
    time periods.
    """

    def on_action(self, event_info):
        events = event_info.get_event_dispatcher()
        zone_manager = event_info.get_zone_manager()

        if not sm.is_armed_stay(zone_manager):
            return False

        activity = zone_manager.get_first_device_by_type(ActivityTimes)
        if activity is None:
            self.log_warning("Missing activities time; can't determine wake-up time.")
            return False

        if activity.is_auto_arm_stay_time() or (activity.is_sleep_time() and not activity.is_wakeup_time()):
            return False

        # determine if any external door was just opened.
        external_zones = [z for z in zone_manager.get_zones() if z.is_external()]
        for z in external_zones:
            doors = [d for d in z.get_devices_by_type(Door) if d.was_recently_activated(30)]
            if len(doors) > 0:
                return False

        sm.disarm(zone_manager, events)
        return True
