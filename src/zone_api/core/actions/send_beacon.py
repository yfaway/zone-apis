import datetime

from zone_api import platform_encapsulator as pe
from zone_api.core.action import action, Action
from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Level
from zone_api.core.zone_event import ZoneEvent


@action(events=[ZoneEvent.TIMER], levels=[Level.FIRST_FLOOR])
class SendBeacon(Action):
    """
    Periodically update several OpenHab items to help determine if HABApps is alive.
    """

    DURATION_IN_MINUTES = 5

    def on_startup(self, event_info: EventInfo):

        # start timer here. Main logic remains in on_action.
        def invoke_action():
            self.on_action(self.create_timer_event_info(event_info))

        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every(SendBeacon.DURATION_IN_MINUTES).minutes.do(invoke_action)

    def on_action(self, event_info: EventInfo):
        pe.set_number_value('Out_HabApp_Beacon_Interval', SendBeacon.DURATION_IN_MINUTES)
        pe.set_datetime_value('Out_HabApp_Beacon_Timestamp', datetime.datetime.now())

        return True
