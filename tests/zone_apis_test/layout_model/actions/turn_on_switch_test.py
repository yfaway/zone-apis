from aaa_modules.layout_model.actions.turn_on_switch import TurnOnSwitch

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone, ZoneEvent
from aaa_modules.layout_model.neighbor import Neighbor, NeighborType
from aaa_modules.layout_model.devices.illuminance_sensor import IlluminanceSensor
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.devices.switch import Light

from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager

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
                 ]
        self.set_items(items)
        super(TurnOnSwitchTest, self).setUp()

        [self.lightItem1, self.lightItem2,
         self.illuminanceSensorItem, self.motionSensorItem1,
         self.motionSensorItem2, self.lightItem3] = items

        self.illuminanceSensor = IlluminanceSensor(self.illuminanceSensorItem)
        self.light1 = Light(self.lightItem1, 30,
                            ILLUMINANCE_THRESHOLD_IN_LUX)
        self.light2 = Light(self.lightItem2, 30,
                            ILLUMINANCE_THRESHOLD_IN_LUX)
        self.light3 = Light(self.lightItem3, 30,
                            ILLUMINANCE_THRESHOLD_IN_LUX)
        self.motionSensor1 = MotionSensor(self.motionSensorItem1)
        self.motionSensor2 = MotionSensor(self.motionSensorItem2)

        self.zone1 = Zone('great room', [self.light1, self.illuminanceSensor, self.motionSensor1])
        self.zone2 = Zone('kitchen', [self.light2, self.illuminanceSensor, self.motionSensor2])
        self.zone3 = Zone('foyer', [self.light3, self.illuminanceSensor])

    def tearDown(self):
        # self.zm.stop_auto_report_watch_dog()
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
        self.light1.turnOn(pe.get_test_event_dispatcher())

        self.assertTrue(self.turnOn())

    def testOnAction_switchDisablesTriggeringByMotionSensor_returnsFalse(self):
        self.light1 = Light(self.lightItem1, 30, ILLUMINANCE_THRESHOLD_IN_LUX, True)
        self.zone1 = Zone('foyer', [self.light1, self.illuminanceSensor])

        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        self.assertFalse(self.turnOn())

    def testOnAction_switchWasJustTurnedOff_returnsFalse(self):
        self.light1.on_switch_turned_off(pe.get_test_event_dispatcher(), self.light1.getItemName())

        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        self.assertFalse(self.turnOn())

    def testOnAction_adjacentZoneWasNotOn_returnsTrue(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE, True)

        # shared channel
        self.motionSensor1.getChannel = lambda: 'a channel'
        self.motionSensor2.getChannel = lambda: 'a channel'

        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        self.assertTrue(self.turnOn())

    def testOnAction_adjacentZoneWasJustTurnedOff_returnsFalse(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE, True)

        # shared channel
        self.motionSensor1.getChannel = lambda: 'a channel'
        self.motionSensor2.getChannel = lambda: 'a channel'

        self.light2.on_switch_turned_off(pe.get_test_event_dispatcher(), self.light2.getItemName())

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
        self.assertTrue(self.zone2.isLightOn())

        self.assertTrue(self.turnOn())
        self.assertFalse(self.zone2.isLightOn())

    def testOnAction_openSpaceNeighborIsOff_returnsTrue(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE, False)
        self.assertFalse(self.zone2.isLightOn())

        self.assertTrue(self.turnOn())
        self.assertTrue(self.zone1.isLightOn())
        self.assertFalse(self.zone2.isLightOn())

    def testOnAction_openSpaceSlaveNeighborIsOn_returnsTrueAndTurnOffNeighbor(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE_SLAVE, True)
        self.assertTrue(self.zone2.isLightOn())

        self.assertTrue(self.turnOn())
        self.assertFalse(self.zone2.isLightOn())

    def testOnAction_openSpaceSlaveNeighborIsOff_returnsTrue(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE_SLAVE, False)
        self.assertFalse(self.zone2.isLightOn())

        self.assertTrue(self.turnOn())
        self.assertTrue(self.zone1.isLightOn())
        self.assertFalse(self.zone2.isLightOn())

    def testOnAction_renewTimerWhenBothMasterAndSlaveAreOn_returnsTrueAndNotTurningOffNeighbor(self):
        self.setUpNeighborRelationship(self.zone2, NeighborType.OPEN_SPACE_SLAVE, True)
        pe.set_switch_state(self.lightItem1, True)

        self.assertTrue(self.turnOn())
        self.assertTrue(self.zone2.isLightOn())

    def testOnAction_masterIsOn_returnsTrueAndNotTurningOffOpenSpaceNeighbor(self):
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        # zone3 (foyer) is an open space neighbor with zone2
        self.zone2 = self.zone2.add_neighbor(Neighbor(self.zone3.getId(), NeighborType.OPEN_SPACE))
        # zone2 (kitchen) is an open space slave with zone1 (great room)
        self.zone2 = self.zone2.add_neighbor(Neighbor(self.zone1.getId(), NeighborType.OPEN_SPACE_MASTER))

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
                               pe.get_test_event_dispatcher())

        return_val = TurnOnSwitch().onAction(event_info)
        self.assertFalse(return_val)
        self.assertFalse(self.zone2.isLightOn())
        self.assertTrue(self.zone3.isLightOn())

    def turnOn(self):
        event_info = EventInfo(ZoneEvent.MOTION, self.lightItem1,
                               self.zone1, create_zone_manager([self.zone1, self.zone2, self.zone3]),
                               pe.get_test_event_dispatcher())

        return TurnOnSwitch().onAction(event_info)

    # Helper method to set up the relationship between the provided zone and zone1.
    def setUpNeighborRelationship(self, zone, neighbor_type, neighbor_light_on):
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)
        self.zone1 = self.zone1.add_neighbor(Neighbor(zone.getId(), neighbor_type))

        if neighbor_light_on:
            pe.set_switch_state(self.lightItem2, True)
