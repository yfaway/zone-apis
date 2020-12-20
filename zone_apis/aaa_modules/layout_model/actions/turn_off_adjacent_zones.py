from aaa_modules.layout_model.zone import ZoneEvent
from aaa_modules.layout_model.neighbor import NeighborType
from aaa_modules.layout_model.devices.switch import Light
from aaa_modules.layout_model.action import action


@action(events=[ZoneEvent.SWITCH_TURNED_ON], devices=[Light], internal=True, external=True)
class TurnOffAdjacentZones:
    """
    Turn off the lights in the zones adjacent to the current zone if the 
    current zone's light is on and if the adjacent zones are of the OPEN_SPACE
    and OPEN_SPACE_SLAVE type.
    """

    def __init__(self):
        pass

    def onAction(self, event_info):
        events = event_info.getEventDispatcher()
        zone = event_info.getZone()
        zone_manager = event_info.getZoneManager()

        if zone_manager is None:
            raise ValueError('zone_manager must be specified')

        adjacent_zones = zone.getNeighborZones(zone_manager,
                                               [NeighborType.OPEN_SPACE, NeighborType.OPEN_SPACE_SLAVE])
        for z in adjacent_zones:
            for light in z.getDevicesByType(Light):
                if light.isOn() and light.canBeTurnedOffByAdjacentZone():
                    light.turnOff(events)

        return True
