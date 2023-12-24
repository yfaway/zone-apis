import datetime
from typing import List

from zone_api.core.action import action, Action
from zone_api.core.devices.plug import Plug
from zone_api.core.devices.switch import ColorLight
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent

ON_EVENTS = [ZoneEvent.ASTRO_LIGHT_ON]


@action(events=ON_EVENTS + [ZoneEvent.ASTRO_BED_TIME], external_events=ON_EVENTS + [ZoneEvent.ASTRO_BED_TIME],
        devices=[ColorLight, Plug], external=True, internal=False)
class TurnOnOutdoorXmasPlugsAndLights(Action):
    """ Turn on the outdoor XMAS plugs in December. """

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info: EventInfo):
        plugs: List[Plug] = event_info.get_zone().get_devices_by_type(Plug)
        color_lights: List[ColorLight] = event_info.get_zone().get_devices_by_type(ColorLight)

        if event_info.get_event_type() in ON_EVENTS:
            month = datetime.datetime.now().month
            if month in [12, 1]:
                for plug in plugs:
                    plug.turn_on(event_info.get_event_dispatcher())

                for light in color_lights:
                    light.turn_on_holiday_mode(event_info.get_event_dispatcher())
        else:  # events to turn off light
            for plug in plugs:
                plug.turn_off(event_info.get_event_dispatcher())

            for light in color_lights:
                light.turn_off_holiday_mode(event_info.get_event_dispatcher())

        return True