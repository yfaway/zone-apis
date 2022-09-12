
from zone_api import security_manager as sm
from zone_api.core.devices.activity_times import ActivityType
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action
from zone_api.core.devices.alarm_partition import AlarmPartition


@action(events=[ZoneEvent.TIMER], devices=[AlarmPartition, MotionSensor], activity_types=[ActivityType.AUTO_ARM_STAY])
class ArmStayInTheNight(Action):
    """
    Automatically arm-stay the house when the current time is within an auto-arm period. Continue to
    check every 15' and arm-stay (if necessary) during that period.
    """

    def on_startup(self, event_info: EventInfo):

        # start timer here. Main logic remains in on_action.
        def timer_handler():
            self.on_action(self.create_timer_event_info(event_info))

        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every().hour.at(':00').do(timer_handler)
        scheduler.every().hour.at(':15').do(timer_handler)
        scheduler.every().hour.at(':30').do(timer_handler)
        scheduler.every().hour.at(':45').do(timer_handler)

    def on_action(self, event_info):
        events = event_info.get_event_dispatcher()
        zone_manager = event_info.get_zone_manager()

        if not sm.is_unarmed(zone_manager):
            return False

        sm.arm_stay(zone_manager, events)
        return True
