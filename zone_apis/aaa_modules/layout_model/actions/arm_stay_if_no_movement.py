from aaa_modules import security_manager as sm
from aaa_modules.layout_model.devices.activity_times import ActivityTimes
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.devices.network_presence import NetworkPresence
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition


@action(events=[ZoneEvent.TIMER], devices=[AlarmPartition, MotionSensor])
class ArmStayIfNoMovement:
    """
    Automatically arm-stay the house if there has been no occupancy event in the last x minutes.
    Use case: user is at home but perhaps taking a nap. Accompanied disarm rule will automatically
    disarm on internal motion sensor.
    """

    def __init__(self, unoccupied_duration_in_minutes=45):
        self._unoccupied_duration_in_minutes = unoccupied_duration_in_minutes

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

        self.log_info(f"*** Debug for ArmStayIfNoMovement: {self._unoccupied_duration_in_minutes} minutes")
        for z in zone_manager.get_zones():
            for d in z.get_devices_by_type(MotionSensor):
                self.log_info("    " + str(d))

        sm.arm_stay(zone_manager, events)
        return True
