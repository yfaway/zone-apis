import time
from functools import reduce

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import ZoneEvent
from aaa_modules.layout_model.neighbor import NeighborType
from aaa_modules.layout_model.devices.switch import Light, Switch
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor

from aaa_modules.layout_model.actions.turn_off_adjacent_zones import TurnOffAdjacentZones
from aaa_modules.layout_model.zone_manager import ZoneManager

DEBUG = False


@action(events=[ZoneEvent.MOTION], devices=[Switch], internal=True, external=True)
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

    def __init__(self):
        pass

    def onAction(self, event_info):
        events = event_info.getEventDispatcher()
        zone = event_info.getZone()
        zone_manager: ZoneManager = event_info.getZoneManager()

        is_processed = False
        can_turn_off_adjacent_zones = True
        light_on_time = zone.isLightOnTime()
        zone_illuminance = zone.getIlluminanceLevel()

        switch = None
        for switch in zone.getDevicesByType(Switch):
            if switch.isOn():
                switch.turnOn(events)  # renew the timer if a switch is already on
                is_processed = True
                can_turn_off_adjacent_zones = False
                continue

            if not switch.canBeTriggeredByMotionSensor():
                # A special case: if a switch is configured not to be
                # triggered by a motion sensor, it means there is already 
                # another switch sharing that motion sensor. In this case, we
                # don't want to turn off the other switch.
                can_turn_off_adjacent_zones = False
                if DEBUG:
                    pe.log_info("{}: rejected - can't be triggered by motion sensor".format(
                        switch.getItemName()))

                continue

            # Break if switch was just turned off.
            if switch.getLastOffTimestampInSeconds() is not None:
                if (time.time() - switch.getLastOffTimestampInSeconds()) <= \
                        TurnOnSwitch.DELAY_AFTER_LAST_OFF_TIME_IN_SECONDS:
                    if DEBUG:
                        pe.log_info("{}: rejected - switch was just turned off".format(
                            switch.getItemName()))
                    continue

            # Break if the switch of a neighbor sharing the motion sensor was
            # just turned off.
            open_space_zones = [zone_manager.get_zone_by_id(n.getZoneId())
                                for n in zone.getNeighbors() if n.isOpenSpace()]
            shared_motion_sensor_zones = [z for z in open_space_zones
                                          if zone.shareSensorWith(z, MotionSensor)]
            their_switches = reduce(lambda a, b: a + b,
                                    [z.getDevicesByType(Switch) for z in shared_motion_sensor_zones],
                                    [])
            if any(time.time() - s.getLastOffTimestampInSeconds() <=
                   TurnOnSwitch.DELAY_AFTER_LAST_OFF_TIME_IN_SECONDS
                   for s in their_switches):
                if DEBUG:
                    pe.log_info("{}: rejected - can't be triggered by motion sensor".format(
                        switch.getItemName()))
                continue

            if isinstance(switch, Light):
                if light_on_time or switch.isLowIlluminance(zone_illuminance):
                    is_processed = True

                if is_processed and zone_manager is not None:
                    master_zones = [zone_manager.get_zone_by_id(n.getZoneId())
                                    for n in zone.getNeighbors()
                                    if NeighborType.OPEN_SPACE_MASTER == n.get_type()]
                    if any(z.isLightOn() for z in master_zones):
                        is_processed = False

                        # This scenario indicates that there is already 
                        # activity in the master zone, and thus such activity
                        # must not prematurely turns off the light in the
                        # adjacent zone.
                        can_turn_off_adjacent_zones = False

                        if DEBUG:
                            pe.log_info("{}: rejected - a master zone's light is on".format(
                                switch.getItemName()))

                if is_processed:
                    switch.turnOn(events)
            else:
                switch.turnOn(events)
                is_processed = True

        # Now shut off the light in any shared space zones
        if can_turn_off_adjacent_zones:
            if DEBUG:
                pe.log_info("{}: turning off adjacent zone's light".format(
                    switch.getItemName()))
            off_event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON,
                                       event_info.getItem(), event_info.getZone(),
                                       event_info.getZoneManager(), event_info.getEventDispatcher())
            TurnOffAdjacentZones().onAction(off_event_info)

        return is_processed
