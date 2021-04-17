from zone_api.core.devices.activity_times import ActivityTimes
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.devices.plug import Plug
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action
from zone_api.core.devices.alarm_partition import AlarmPartition


@action(events=[ZoneEvent.TIMER, ZoneEvent.MOTION, ZoneEvent.PARTITION_ARMED_AWAY,
                ZoneEvent.PARTITION_DISARMED_FROM_AWAY],
        devices=[AlarmPartition, MotionSensor])
class ManagePlugs:
    """
    Turns off the plugs if the house is armed-away or if it is evening time (via ActivityTimes).
    Turn on the plug on the first motion sensor trigger during wake-up time period, or when the
    house is disarmed (from armed-away) NOT during the turn-off-plugs time period.
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

    def on_action(self, event_info: EventInfo):
        events = event_info.get_event_dispatcher()
        zm = event_info.get_zone_manager()

        activities = zm.get_devices_by_type(ActivityTimes)
        if len(activities) == 0:
            self.log_warning("Missing activities time; can't determine turn-off-plugs time.")
            return False

        activity: ActivityTimes = activities[0]
        zone_event = event_info.get_event_type()

        if zone_event == ZoneEvent.TIMER:
            if activity.is_turn_off_plugs_time():
                for z in zm.get_zones():
                    occupied, device = z.is_occupied([Plug])
                    if not occupied:
                        for p in z.get_devices_by_type(Plug):
                            if not p.is_always_on():
                                p.turn_off(events)

            return True
        elif zone_event == ZoneEvent.MOTION:
            if activity.is_wakeup_time():
                for p in zm.get_devices_by_type(Plug):
                    p.turn_on(events)

            return True

        elif zone_event == ZoneEvent.PARTITION_ARMED_AWAY:
            for p in zm.get_devices_by_type(Plug):
                if not p.is_always_on():
                    p.turn_off(events)

            return True

        elif zone_event == ZoneEvent.PARTITION_DISARMED_FROM_AWAY:
            if not activity.is_turn_off_plugs_time():
                for p in zm.get_devices_by_type(Plug):
                    p.turn_on(events)

            return True

        else:
            return False
