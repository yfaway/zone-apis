from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.turn_off_adjacent_zones import TurnOffAdjacentZones
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone, ZoneEvent
from aaa_modules.layout_model.neighbor import Neighbor, NeighborType
from aaa_modules.layout_model.devices.switch import Fan, Light

from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager

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
                                 ILLUMINANCE_THRESHOLD_IN_LUX, False, "0-23:59")  # always stay on
        self.show_fan = Fan(self.fan_item, 5)

        self.washroom = Zone('washroom', [self.washroom_light])
        self.shower = Zone('shower', [self.show_fan])
        self.lobby = Zone('lobby', [self.lobby_light])
        self.foyer = Zone('foyer', [self.foyer_light])

        self.lobby = self.lobby.add_neighbor(
            Neighbor(self.foyer.getId(), NeighborType.OPEN_SPACE))
        self.foyer = self.foyer.add_neighbor(
            Neighbor(self.lobby.getId(), NeighborType.OPEN_SPACE))

        self.washroom = self.washroom.add_neighbor(
            Neighbor(self.lobby.getId(), NeighborType.OPEN_SPACE))
        self.washroom = self.washroom.add_neighbor(
            Neighbor(self.shower.getId(), NeighborType.OPEN_SPACE))

        self.zone_manager = create_zone_manager(
            [self.washroom, self.shower, self.lobby, self.foyer])

    def testOnAction_normalOpenSpaceNeighbor_turnsOffLight(self):
        pe.set_switch_state(self.lobby_light_item, True)

        self.assertTrue(self.trigger_action_from_zone(self.washroom))
        self.assertFalse(self.lobby.isLightOn())

    def testOnAction_openSpaceButDisableTurnOffByNeighbor_mustNotTurnsOffLight(self):
        pe.set_switch_state(self.foyer_light_item, True, True)
        self.assertTrue(self.foyer.isLightOn())

        self.assertTrue(self.trigger_action_from_zone(self.lobby))
        self.assertTrue(self.foyer.isLightOn())

    def testOnAction_fanZone_returnsFalse(self):
        pe.set_switch_state(self.fan_item, True)
        self.assertFalse(self.trigger_action_from_zone(self.shower))

    def testOnAction_neighborWithFan_mustNotTurnOffNeighborFan(self):
        pe.set_switch_state(self.fan_item, True, True)
        pe.set_switch_state(self.lobby_light_item, True, True)

        self.assertTrue(self.trigger_action_from_zone(self.washroom))
        self.assertFalse(self.lobby.isLightOn())
        self.assertTrue(pe.is_in_on_state(self.fan_item))

    def trigger_action_from_zone(self, zone):
        """
        Creates a turn-on event on a light in the given zone, and invokes the turn-off-adjacent-zones action.
        :param zone: the zone with the light just turned on.
        :return: Boolean
        """
        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.washroom_light_item, zone,
                               self.zone_manager, pe.get_test_event_dispatcher())

        return TurnOffAdjacentZones().onAction(event_info)
