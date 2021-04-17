from zone_api.core.zone_event import ZoneEvent
from zone_api.core.neighbor import NeighborType
from zone_api.core.devices.switch import Light
from zone_api.core.action import action


@action(events=[ZoneEvent.SWITCH_TURNED_ON], devices=[Light], internal=True, external=True)
class TurnOffAdjacentZones:
    """
    Turn off the lights in the zones adjacent to the current zone if the 
    current zone's light is on and if the adjacent zones are of the OPEN_SPACE
    and OPEN_SPACE_SLAVE type.
    """

    def __init__(self):
        pass

    def on_action(self, event_info):
        events = event_info.get_event_dispatcher()
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        if zone_manager is None:
            raise ValueError('zone_manager must be specified')

        adjacent_zones = zone.get_neighbor_zones(zone_manager,
                                                 [NeighborType.OPEN_SPACE, NeighborType.OPEN_SPACE_SLAVE])
        for z in adjacent_zones:
            for light in z.get_devices_by_type(Light):
                if light.is_on() and light.can_be_turned_off_by_adjacent_zone():
                    light.turn_off(events)

        return True
