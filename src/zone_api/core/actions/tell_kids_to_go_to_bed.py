from datetime import datetime
from enum import unique, Enum

from zone_api.audio_manager import get_nearby_audio_sink
from zone_api.core.action import action
from zone_api.core.devices.switch import Light
from zone_api.core.event_info import EventInfo
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.zone_event import ZoneEvent


@action(events=[ZoneEvent.TIMER], zone_name_pattern='.*Kitchen.*')
class TellKidsToGoToBed:
    """
    If there is one or more lights turned on on the first floor, the first audio message asks kids
    to clean up and prepare to go to bed. The second message is played 5' later; all the lights on
    the first floor will be turned off.
    """

    @unique
    class Type(Enum):
        FIRST_NOTICE = 1
        SECOND_NOTICE = 2

    def on_startup(self, event_info: EventInfo):

        # start timer here. Main logic remains in on_action.
        def first_notice_timer_handler():
            if self._is_applicable():
                self.on_action(self.create_timer_event_info(event_info, TellKidsToGoToBed.Type.FIRST_NOTICE))

        def second_notice_timer_handler():
            if self._is_applicable():
                self.on_action(self.create_timer_event_info(event_info, TellKidsToGoToBed.Type.SECOND_NOTICE))

        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every().day.at('19:45').do(first_notice_timer_handler)
        scheduler.every().day.at('19:50').do(second_notice_timer_handler)

    def on_action(self, event_info: EventInfo):
        zone = event_info.get_zone()
        zone_manager: ImmutableZoneManager = event_info.get_zone_manager()

        sink = get_nearby_audio_sink(zone, zone_manager)
        if sink is None:
            self.log_warning("Missing audio device; can't play music.")
            return False

        time_str = datetime.now().strftime("%I:%M")

        if event_info.get_custom_parameter() == TellKidsToGoToBed.Type.FIRST_NOTICE:
            sink.play_message(
                f'Kids, it is {time_str}; please put away everything and prepare to go upstairs.')
        else:
            sink.play_message(f'Kids, it is {time_str}; please go upstairs now.')

            foyer_zone = None
            for z in zone_manager.get_zones():
                if z.get_level() == zone.get_level():
                    if "Foyer" in z.get_name():
                        foyer_zone = z
                    else:
                        z.turn_off_lights(event_info.get_event_dispatcher())

            if foyer_zone is not None:
                for light in foyer_zone.get_devices_by_type(Light):
                    light.turn_on(event_info.get_event_dispatcher())

        return True

    # noinspection PyMethodMayBeStatic
    def _is_applicable(self):
        """ Returns true if the next day is a school day. """
        now = datetime.now()
        if (0 <= now.weekday() < 4) or now.weekday() == 6:  # Mon - Thursday and Sunday
            if now.month >= 9 or now.month <= 5:  # Between Sept and June 20
                return True
            elif now.month == 6:
                return now.day <= 20

            return False
