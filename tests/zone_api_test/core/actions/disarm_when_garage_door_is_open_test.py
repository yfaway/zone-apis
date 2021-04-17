import time

from zone_api import platform_encapsulator as pe
from zone_api.core.actions.disarm_when_garage_door_is_open import DisarmWhenGarageDoorIsOpen
from zone_api.core.devices.contact import GarageDoor
from zone_api.core.devices.network_presence import NetworkPresence

from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class DisarmWhenGarageDoorIsOpenTest(DeviceTest):
    """ Unit tests for DisarmWhenGarageDoorIsOpen. """

    def setUp(self):
        self.alarm_partition, items = self.create_alarm_partition()

        items = items + [pe.create_switch_item('_NetworkPresence'), pe.create_switch_item('_Door')]

        self.set_items(items)
        super(DisarmWhenGarageDoorIsOpenTest, self).setUp()

        self.network_presence = NetworkPresence(items[-1])
        self.garage_door = GarageDoor(items[-2])

        self.action = DisarmWhenGarageDoorIsOpen(0.015, 2)
        self.zone1 = Zone('garage', [self.network_presence, self.alarm_partition, self.garage_door])\
            .add_action(self.action)

        self.mockZoneManager = create_zone_manager([self.zone1])
        self.alarm_partition.arm_away(pe.get_event_dispatcher())

    def testOnAction_ownerDetectedImmediately_disarm(self):
        pe.set_switch_state(self.network_presence.get_item(), True)
        event_info = EventInfo(ZoneEvent.DOOR_OPEN, self.garage_door.get_item(),
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.alarm_partition.is_unarmed())

    def testOnAction_ownerDetectedInTimerEvent_disarm(self):
        event_info = EventInfo(ZoneEvent.DOOR_OPEN, self.garage_door.get_item(),
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        time.sleep(0.02)

        self.assertTrue(self.action.timer.is_alive())
        pe.set_switch_state(self.network_presence.get_item(), True)
        time.sleep(0.02)

        self.assertTrue(value)
        self.assertTrue(self.alarm_partition.is_unarmed())

    def testOnAction_ownerNotDetected_disarm(self):
        event_info = EventInfo(ZoneEvent.DOOR_OPEN, self.garage_door.get_item(),
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        time.sleep(0.05)
        self.assertFalse(self.action.timer.is_alive())
        self.assertTrue(value)
        self.assertFalse(self.alarm_partition.is_unarmed())