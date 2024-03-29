from zone_api import platform_encapsulator as pe
from zone_api.core.actions.turn_off_adjacent_zones import TurnOffAdjacentZones
from zone_api.core.event_info import EventInfo
from zone_api.core.map_parameters import MapParameters
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.neighbor import Neighbor, NeighborType
from zone_api.core.devices.switch import Fan, Light

from zone_api_test.core.device_test import DeviceTest, create_zone_manager

ILLUMINANCE_THRESHOLD_IN_LUX = 10


class TurnOffAdjacentZonesTest(DeviceTest):
    """ Unit tests for turn_off_adjacent_zones.py """

    def setUp(self):
        self.items = [pe.create_switch_item('TestLightName1'),
                      pe.create_switch_item('TestLightName2'),
                      pe.create_switch_item('TestLightName3'),
                      pe.create_switch_item('TestFanName'),
                      ]
        self.set_items(self.items)
        super(TurnOffAdjacentZonesTest, self).setUp()

        [self.washroom_light_item, self.lobby_light_item, self.foyer_light_item, self.fan_item] = self.items

        self.washroom_light = Light(self.washroom_light_item, 5)
        self.lobby_light = Light(self.lobby_light_item, 5)
        self.foyer_light = Light(self.foyer_light_item, 5,
                                 ILLUMINANCE_THRESHOLD_IN_LUX, "0-23:59")  # always stay on
        self.show_fan = Fan(self.fan_item, 5)

        self.action = TurnOffAdjacentZones(MapParameters({}))

        self.washroom = Zone('washroom', [self.washroom_light]).add_action(self.action)
        self.shower = Zone('shower', [self.show_fan]).add_action(self.action)
        self.lobby = Zone('lobby', [self.lobby_light]).add_action(self.action)
        self.foyer = Zone('foyer', [self.foyer_light]).add_action(self.action)

        self.lobby = self.lobby.add_neighbor(
            Neighbor(self.foyer.get_id(), NeighborType.OPEN_SPACE))
        self.foyer = self.foyer.add_neighbor(
            Neighbor(self.lobby.get_id(), NeighborType.OPEN_SPACE))

        self.washroom = self.washroom.add_neighbor(
            Neighbor(self.lobby.get_id(), NeighborType.OPEN_SPACE))
        self.washroom = self.washroom.add_neighbor(
            Neighbor(self.shower.get_id(), NeighborType.OPEN_SPACE))

        self.zone_manager = create_zone_manager(
            [self.washroom, self.shower, self.lobby, self.foyer])

    def testOnAction_normalOpenSpaceNeighbor_turnsOffLight(self):
        pe.set_switch_state(self.lobby_light_item, True)

        self.assertTrue(self.trigger_action_from_zone(self.washroom))
        self.assertFalse(self.lobby.is_light_on())

    def testOnAction_openSpaceButDisableTurnOffByNeighbor_mustNotTurnsOffLight(self):
        pe.set_switch_state(self.foyer_light_item, True)
        self.assertTrue(self.foyer.is_light_on())

        self.assertTrue(self.trigger_action_from_zone(self.lobby))
        self.assertTrue(self.foyer.is_light_on())

    def testOnAction_fanZone_returnsFalse(self):
        pe.set_switch_state(self.fan_item, True)
        self.assertFalse(self.trigger_action_from_zone(self.shower))

    def testOnAction_neighborWithFan_mustNotTurnOffNeighborFan(self):
        pe.set_switch_state(self.fan_item, True)
        pe.set_switch_state(self.lobby_light_item, True)

        self.assertTrue(self.trigger_action_from_zone(self.washroom))
        self.assertFalse(self.lobby.is_light_on())
        self.assertTrue(pe.is_in_on_state(self.fan_item))

    def trigger_action_from_zone(self, zone):
        """
        Creates a turn-on event on a light in the given zone, and invokes the turn-off-adjacent-zones action.
        :param zone: the zone with the light just turned on.
        :return: Boolean
        """
        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, zone.get_devices()[0].get_item(), zone,
                               self.zone_manager, pe.get_event_dispatcher())

        return self.action.on_action(event_info)
