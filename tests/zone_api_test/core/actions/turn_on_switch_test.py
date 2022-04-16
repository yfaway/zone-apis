from zone_api.core.actions.turn_on_switch import TurnOnSwitch

from zone_api import platform_encapsulator as pe
from zone_api.core.event_info import EventInfo
from zone_api.core.map_parameters import MapParameters
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.neighbor import Neighbor, NeighborType
from zone_api.core.devices.illuminance_sensor import IlluminanceSensor
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.devices.switch import Light, Fan

from zone_api_test.core.device_test import DeviceTest, create_zone_manager

ILLUMINANCE_THRESHOLD_IN_LUX = 10


class TurnOnSwitchTest(DeviceTest):
    """ Unit tests for zone_manager.py. """

    def setUp(self):
        items = [pe.create_switch_item('TestLightName1'),
                 pe.create_switch_item('TestLightName2'),
                 pe.create_number_item('IlluminanceSensorName'),
                 pe.create_switch_item('TestMotionSensor1'),
                 pe.create_switch_item('TestMotionSensor2'),
                 pe.create_switch_item('TestLightName3'),
                 pe.create_switch_item('TestFan'),
                 ]
        self.set_items(items)
        super(TurnOnSwitchTest, self).setUp()

        [self.lightItem1, self.lightItem2,
         self.illuminanceSensorItem, self.motionSensorItem1,
         self.motionSensorItem2, self.lightItem3, self.fanItem] = items

        self.illuminanceSensor = IlluminanceSensor(self.illuminanceSensorItem)
        self.light1 = Light(self.lightItem1, 30,
                            ILLUMINANCE_THRESHOLD_IN_LUX)
        self.light2 = Light(self.lightItem2, 30,
                            ILLUMINANCE_THRESHOLD_IN_LUX)
        self.light3 = Light(self.lightItem3, 30,
                            ILLUMINANCE_THRESHOLD_IN_LUX)
        self.fan = Fan(self.fanItem, 30)
        self.motionSensor1 = MotionSensor(self.motionSensorItem1)
        self.motionSensor2 = MotionSensor(self.motionSensorItem2)

        self.action = TurnOnSwitch(MapParameters({}))

        self.zone1 = Zone('great room', [self.light1, self.illuminanceSensor, self.motionSensor1]) \
            .add_action(self.action)
        self.zone2 = Zone('kitchen', [self.light2, self.illuminanceSensor, self.motionSensor2]) \
            .add_action(self.action)
        self.zone3 = Zone('foyer', [self.light3, self.illuminanceSensor]) \
            .add_action(self.action)
        self.zoneWithFan = Zone('office', [self.fan, self.motionSensor2]).add_action(self.action)

    def tearDown(self):
        # self.zm.stop_auto_report_watch_dog()
        self.fan._cancel_timer()
        self.light1._cancel_timer()
        self.light2._cancel_timer()
        self.light3._cancel_timer()

        super(TurnOnSwitchTest, self).tearDown()

    def testOnAction_illuminanceBelowThreshold_turnsOnLight(self):
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        self.assertTrue(self.turnOn())

    def testOnAction_illuminanceAboveThreshold_returnsFalse(self):
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX + 1)

        self.assertFalse(self.turnOn())

    def testOnAction_renewTimerIfLightIsAlreadyOnEvenIfIlluminanceIsAboveThreshold_returnsTrue(self):
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX + 1)
        self.light1.turn_on(pe.get_event_dispatcher())

        self.assertTrue(self.turnOn())

    def testOnAction_switchDisablesTriggeringByMotionSensor_returnsFalse(self):
        motion_sensor: MotionSensor = self.zone1.get_devices_by_type(MotionSensor)[0]
        motion_sensor._can_trigger_switches = False

        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        self.assertFalse(self.turnOn())

    def testOnAction_switchWasJustTurnedOff_returnsFalse(self):
        self.light1.on_switch_turned_off(pe.get_event_dispatcher(), self.light1.get_item_name())

        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        self.assertFalse(self.turnOn())

    def testOnAction_adjacentZoneWasNotOn_returnsTrue(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE, True)

        # shared channel
        self.motionSensor1.get_channel = lambda: 'a channel'
        self.motionSensor2.get_channel = lambda: 'a channel'

        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        self.assertTrue(self.turnOn())

    def testOnAction_adjacentZoneWasJustTurnedOff_returnsFalse(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE, True)

        # shared channel
        self.motionSensor1.get_channel = lambda: 'a channel'
        self.motionSensor2.get_channel = lambda: 'a channel'

        self.light2.on_switch_turned_off(pe.get_event_dispatcher(), self.light2.get_item_name())

        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        self.assertFalse(self.turnOn())

    def testOnAction_openSpaceMasterNeighborIsOn_returnsFalse(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE_MASTER, True)

        self.assertFalse(self.turnOn())

    def testOnAction_openSpaceMasterNeighborIsOff_returnsFalse(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE_MASTER, False)

        self.assertTrue(self.turnOn())

    def testOnAction_openSpaceNeighborIsOn_returnsTrueAndTurnOffNeighbor(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE, True)
        self.assertTrue(self.zone2.is_light_on())

        self.assertTrue(self.turnOn())
        self.assertFalse(self.zone2.is_light_on())

    def testOnAction_openSpaceNeighborIsOff_returnsTrue(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE, False)
        self.assertFalse(self.zone2.is_light_on())

        self.assertTrue(self.turnOn())
        self.assertTrue(self.zone1.is_light_on())
        self.assertFalse(self.zone2.is_light_on())

    def testOnAction_openSpaceSlaveNeighborIsOn_returnsTrueAndTurnOffNeighbor(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE_SLAVE, True)
        self.assertTrue(self.zone2.is_light_on())

        self.assertTrue(self.turnOn())
        self.assertFalse(self.zone2.is_light_on())

    def testOnAction_openSpaceSlaveNeighborIsOff_returnsTrue(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE_SLAVE, False)
        self.assertFalse(self.zone2.is_light_on())

        self.assertTrue(self.turnOn())
        self.assertTrue(self.zone1.is_light_on())
        self.assertFalse(self.zone2.is_light_on())

    def testOnAction_renewTimerWhenBothMasterAndSlaveAreOn_returnsTrueAndNotTurningOffNeighbor(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE_SLAVE, True)
        pe.set_switch_state(self.lightItem1, True)

        self.assertTrue(self.turnOn())
        self.assertTrue(self.zone2.is_light_on())

    def testOnAction_masterIsOn_returnsTrueAndNotTurningOffOpenSpaceNeighbor(self):
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        # zone3 (foyer) is an open space neighbor with zone2
        self.zone2 = self.zone2.add_neighbor(Neighbor(self.zone3.get_id(), NeighborType.OPEN_SPACE))
        # zone2 (kitchen) is an open space slave with zone1 (great room)
        self.zone2 = self.zone2.add_neighbor(Neighbor(self.zone1.get_id(), NeighborType.OPEN_SPACE_MASTER))

        # Turn on the light in the great room and the foyer. 
        # We want to make sure that when the motion sensor in the kitchen is
        # triggered, it won't be turn on, and also the foyer light must not
        # be turned off.
        # The rationale is that someone just open the door to come to the foyer
        # area. However, as the great room light was already on, that indicates
        # someone is already in that area. As such, any movement in that 
        # area must not prematurely turn off the the foyer light.
        pe.set_switch_state(self.lightItem1, True)
        pe.set_switch_state(self.lightItem3, True)

        event_info = EventInfo(ZoneEvent.MOTION, self.lightItem1,
                               self.zone2, create_zone_manager([self.zone1, self.zone2, self.zone3]),
                               pe.get_event_dispatcher())

        return_val = TurnOnSwitch(MapParameters({})).on_action(event_info)
        self.assertFalse(return_val)
        self.assertFalse(self.zone2.is_light_on())
        self.assertTrue(self.zone3.is_light_on())

    def testOnAction_fanIsTurnedOn_returnsTrueAndDoNotTurnOffNeighborLight(self):
        self.zoneWithFan = self.zoneWithFan.add_neighbor(Neighbor(self.zone1.get_id(), NeighborType.OPEN_SPACE))
        pe.set_switch_state(self.lightItem1, True)
        self.assertTrue(self.zone1.is_light_on())

        value = self.turnOn(self.zoneWithFan)
        self.assertTrue(value)
        self.assertTrue(self.zone1.is_light_on())

    def turnOn(self, receiving_zone=None):
        if receiving_zone is None:
            receiving_zone = self.zone1

        motion_sensor = receiving_zone.get_devices_by_type(MotionSensor)[0]
        event_info = EventInfo(ZoneEvent.MOTION, motion_sensor.get_item(),
                               receiving_zone,
                               create_zone_manager([self.zone1, self.zone2, self.zone3, self.zoneWithFan]),
                               pe.get_event_dispatcher(), receiving_zone, motion_sensor)

        return self.action.on_action(event_info)

    # Helper method to set up the relationship between the provided zone and zone1.
    def setUpNeighborRelationship(self, zone, neighbor_type, neighbor_light_on):
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)
        self.zone1 = self.zone1.add_neighbor(Neighbor(zone.get_id(), neighbor_type))

        if neighbor_light_on:
            pe.set_switch_state(self.lightItem2, True)
