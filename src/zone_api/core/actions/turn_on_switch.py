import time
from functools import reduce

from zone_api import platform_encapsulator as pe
from zone_api.core.action import action
from zone_api.core.event_info import EventInfo
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.neighbor import NeighborType
from zone_api.core.devices.switch import Light, Switch, Fan
from zone_api.core.devices.motion_sensor import MotionSensor

from zone_api.core.actions.turn_off_adjacent_zones import TurnOffAdjacentZones

DEBUG = False


@action(events=[ZoneEvent.MOTION], devices=[Switch], internal=True, external=True, priority=1)
class TurnOnSwitch:
    """
    Turns on a switch (fan, dimmer or regular light), after being triggered by
    a motion event.
    If the switch is a dimmer or light, it is only turned on if:
    1. It is evening time, or
    2. The illuminance is below a threshold.

    A light/dimmer switch won't be turned on if:
    1. The light has the flag set to ignore motion event, or
    2. The adjacent zone is of type OPEN_SPACE_MASTER with the light on, or
    3. The light was just turned off, or
    4. The neighbor zone has a light switch that shares the same motion sensor,
    and that light switch was just recently turned off.

    No matter whether the switch is turned on or not (see the condition above),
    any adjacent zones of type OPEN_SPACE, and OPEN_SPACE_SLAVE that currently
    has the light on, will be sent a command to shut off the light.
    """

    DELAY_AFTER_LAST_OFF_TIME_IN_SECONDS = 8
    """
    The period of time in seconds (from the last timestamp a switch was
    turned off) to ignore the motion sensor event. This takes care of the
    scenario when the user manually turns off a light, but that physical
    spot is covered by a motion sensor, which immediately turns on the light
    again.
    """

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info: EventInfo):
        events = event_info.get_event_dispatcher()
        zone = event_info.get_zone()
        zone_manager: ImmutableZoneManager = event_info.get_zone_manager()
        motion_sensor: MotionSensor = event_info.get_device()

        is_processed = False
        can_turn_off_adjacent_zones = True
        light_on_time = zone_manager.is_light_on_time()
        zone_illuminance = zone.get_illuminance_level()

        switch = None
        zone_switches = zone.get_devices_by_type(Switch)
        for switch in zone_switches:
            if switch.is_on():
                switch.turn_on(events)  # renew the timer if a switch is already on
                is_processed = True
                can_turn_off_adjacent_zones = False
                continue

            if not motion_sensor.can_trigger_switches():
                # A special case: if a switch is configured not to be # triggered by a motion sensor, it means there is
                # already another switch sharing that motion sensor. In this case, we # don't want to turn off the
                # other switch.
                can_turn_off_adjacent_zones = False
                if DEBUG:
                    pe.log_info("{}: rejected - can't be triggered by motion sensor".format(
                        switch.get_item_name()))

                continue

            # Break if switch was just turned off.
            if switch.get_last_off_timestamp_in_seconds() is not None:
                if (time.time() - switch.get_last_off_timestamp_in_seconds()) <= \
                        TurnOnSwitch.DELAY_AFTER_LAST_OFF_TIME_IN_SECONDS:
                    if DEBUG:
                        pe.log_info("{}: rejected - switch was just turned off".format(
                            switch.get_item_name()))
                    continue

            # Break if the switch of a neighbor sharing the motion sensor was
            # just turned off.
            open_space_zones = [zone_manager.get_zone_by_id(n.get_zone_id())
                                for n in zone.get_neighbors() if n.is_open_space()]
            shared_motion_sensor_zones = [z for z in open_space_zones
                                          if zone.share_sensor_with(z, MotionSensor)]
            their_switches = reduce(lambda a, b: a + b,
                                    [z.get_devices_by_type(Switch) for z in shared_motion_sensor_zones],
                                    [])
            if any(time.time() - s.get_last_off_timestamp_in_seconds() <=
                   TurnOnSwitch.DELAY_AFTER_LAST_OFF_TIME_IN_SECONDS
                   for s in their_switches):
                if DEBUG:
                    pe.log_info("{}: rejected - can't be triggered by motion sensor".format(
                        switch.get_item_name()))
                continue

            if isinstance(switch, Light):
                if light_on_time or switch.is_low_illuminance(zone_illuminance):
                    is_processed = True

                if is_processed and zone_manager is not None:
                    master_zones = [zone_manager.get_zone_by_id(n.get_zone_id())
                                    for n in zone.get_neighbors()
                                    if NeighborType.OPEN_SPACE_MASTER == n.get_type()]
                    if any(z.is_light_on() for z in master_zones):
                        is_processed = False

                        # This scenario indicates that there is already 
                        # activity in the master zone, and thus such activity
                        # must not prematurely turns off the light in the
                        # adjacent zone.
                        can_turn_off_adjacent_zones = False

                        if DEBUG:
                            pe.log_info("{}: rejected - a master zone's light is on".format(
                                switch.get_item_name()))

                if is_processed:
                    switch.turn_on(events)
            else:
                switch.turn_on(events)
                is_processed = True

        # Special case when the zone has only fans; must not turn off adjacent lights.
        if can_turn_off_adjacent_zones:
            fans = zone.get_devices_by_type(Fan)
            if len(zone_switches) == len(fans):
                can_turn_off_adjacent_zones = False

        # Now shut off the light in any shared space zones
        if can_turn_off_adjacent_zones:
            if DEBUG:
                pe.log_info("{}: turning off adjacent zone's light".format(
                    switch.get_item_name()))
            off_event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON,
                                       event_info.get_item(), event_info.get_zone(),
                                       event_info.get_zone_manager(), event_info.get_event_dispatcher())
            turn_off_action = TurnOffAdjacentZones().disable_filtering()
            turn_off_action.on_action(off_event_info)

        return is_processed
