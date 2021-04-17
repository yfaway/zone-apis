import time

from zone_api import platform_encapsulator as pe

from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.devices.contact import Door
from zone_api_test.core.device_test import DeviceTest, create_zone_manager

from zone_api.core.actions.arm_after_front_door_closed import ArmAfterFrontDoorClosed


class ArmAfterFrontDoorClosedTest(DeviceTest):
    """ Unit tests for arm_after_front_door_closed.py. """

    def setUp(self):
        items = [pe.create_switch_item('Door1'), pe.create_switch_item('Door2'),
                 pe.create_switch_item('AlarmStatus'), pe.create_number_item('_AlarmMode'),
                 pe.create_switch_item('ExternalMotionSensor'), pe.create_switch_item('InternalMotionSensor')]
        self.set_items(items)
        super(ArmAfterFrontDoorClosedTest, self).setUp()

        self.alarmPartition = AlarmPartition(items[2], items[3])
        self.externalMotionSensor = MotionSensor(items[4])
        self.internalMotionSensor = MotionSensor(items[5])

        self.door = Door(items[0])
        self.action = ArmAfterFrontDoorClosed(0.1)
        self.zone1 = Zone.create_external_zone('porch') \
            .add_device(self.door) \
            .add_device(self.externalMotionSensor) \
            .add_action(self.action)

        self.zone2 = Zone('foyer', [self.internalMotionSensor, self.alarmPartition])

        self.mockZoneManager = create_zone_manager([self.zone1, self.zone2])

    def testOnAction_motionTriggeredInAnExternalZone_ignoreMotionEventAndContinueToArm(self):
        pe.set_switch_state(self.get_items()[0], False)  # close door
        self.alarmPartition.disarm(pe.get_event_dispatcher())

        event_info = EventInfo(ZoneEvent.DOOR_CLOSED, self.get_items()[0],
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)

        time.sleep(0.1)
        # simulate a motion event
        self.externalMotionSensor._update_last_activated_timestamp()

        time.sleep(0.2)
        self.assertTrue(self.alarmPartition.is_armed_away())

    def testOnAction_doorClosedWithNoPresenceEvent_armAndReturnsTrue(self):
        pe.set_switch_state(self.get_items()[0], False)  # close door
        self.alarmPartition.disarm(pe.get_event_dispatcher())

        event_info = EventInfo(ZoneEvent.DOOR_CLOSED, self.get_items()[0],
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())

        value = self.action.on_action(event_info)
        self.assertTrue(value)

        time.sleep(0.2)
        self.assertTrue(self.alarmPartition.is_armed_away())

    def testOnAction_doorClosedWithPresenceEvent_notArmedAndReturnsTrue(self):
        pe.set_switch_state(self.get_items()[0], False)  # close door
        self.alarmPartition.disarm(pe.get_event_dispatcher())

        self.action = ArmAfterFrontDoorClosed(0.2)
        self.zone1 = Zone.create_external_zone('porch') \
            .add_device(self.door) \
            .add_device(self.externalMotionSensor) \
            .add_action(self.action)
        self.mockZoneManager = create_zone_manager([self.zone1, self.zone2])

        event_info = EventInfo(ZoneEvent.DOOR_CLOSED, self.get_items()[0],
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)

        # simulate a motion event
        time.sleep(0.1)
        self.internalMotionSensor._update_last_activated_timestamp()

        time.sleep(0.1)
        self.assertFalse(self.alarmPartition.is_armed_away())
        self.assertFalse(self.action.timer.is_alive())
