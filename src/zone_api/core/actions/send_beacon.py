import datetime
from typing import cast

from zone_api import platform_encapsulator as pe
from zone_api.core.action import action, Action
from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Level
from zone_api.core.zone_event import ZoneEvent
from zone_api.models import DateTimeItem, NumberItem


@action(events=[ZoneEvent.TIMER], levels=[Level.FIRST_FLOOR])
class SendBeacon(Action):
    """
    Periodically update several OpenHab items to help determine if zone_api is alive.
    """

    DURATION_IN_MINUTES = 5

    def on_startup(self, event_info: EventInfo):

        # start timer here. Main logic remains in on_action.
        def invoke_action():
            self.on_action(self.create_timer_event_info(event_info))

        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every(SendBeacon.DURATION_IN_MINUTES).minutes.do(invoke_action)

    def on_action(self, event_info: EventInfo):
        interval_item = pe.get_item('Out_HabApp_Beacon_Interval')
        if interval_item:
            cast(NumberItem, interval_item).set_value(SendBeacon.DURATION_IN_MINUTES)

        timestamp_item = pe.get_item('Out_HabApp_Beacon_Timestamp')
        if timestamp_item:
            cast(DateTimeItem, timestamp_item).set_value(datetime.datetime.now())

        return True
