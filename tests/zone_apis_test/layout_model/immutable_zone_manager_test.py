from typing import List

from aaa_modules.layout_model.device import Device
from aaa_modules.layout_model.neighbor import Neighbor
from aaa_modules.layout_model.zone_manager import ZoneManager
from aaa_modules import platform_encapsulator as pe

from aaa_modules.layout_model.zone import Zone, ZoneEvent, Level
from aaa_modules.layout_model.devices.dimmer import Dimmer
from aaa_modules.layout_model.devices.switch import Fan, Light, Switch
from aaa_modules.layout_model.devices.illuminance_sensor import IlluminanceSensor
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.actions.turn_on_switch import TurnOnSwitch

from zone_apis_test.layout_model.device_test import DeviceTest


class ImmutableZoneManagerTest(DeviceTest):
    """ Unit tests for immutable_zone_manager.py. """

    def setUp(self):
        items = [pe.create_switch_item('FF_Foyer_TestLightName'),
                 pe.create_switch_item('TestMotionSensorName'),
                 pe.create_number_item('IlluminanceSensorName'),
                 pe.create_switch_item('BM_Utility_TestFanName'),
                 pe.create_switch_item('SharedLight'),
                 ]

        self.set_items(items)
        super(ImmutableZoneManagerTest, self).setUp()

        [self.lightItem, self.motionSensorItem, self.illuminanceSensorItem,
         self.fanItem, self.shared_light_item] = items

        self.light = Light(self.lightItem, 2)
        self.motionSensor = MotionSensor(self.motionSensorItem)
        self.illuminanceSensor = IlluminanceSensor(self.illuminanceSensorItem)
        self.fan = Fan(self.fanItem, 2)
        self.shared_light = Light(self.shared_light_item, 2)

        class MyZone(Zone):
            """ Subclass Zone to simplify the behavior of dispatch_event. """

            def __init__(self, name, devices: List[Device] = None, level=Level.UNDEFINED,
                         neighbors: List[Neighbor] = None, actions=None, external=False,
                         display_icon=None, display_order=9999):
                super().__init__(name, devices, level, neighbors, actions, external, display_icon, display_order)

                self.dispatched = False

            def dispatch_event(self, zone_event, open_hab_events, item,
                               immutable_zone_manager, enforce_item_in_zone):
                value = self.containsOpenHabItem(item)
                self.dispatched = value

                return value

        self.zone1 = MyZone('Foyer', [self.light, self.motionSensor, self.shared_light], Level.FIRST_FLOOR)
        self.zone2 = MyZone('Kitchen', [self.fan, self.shared_light], Level.FIRST_FLOOR)

        self.zone_manager = ZoneManager().add_zone(self.zone1).add_zone(self.zone2)
        self.immutable_zm = self.zone_manager.get_immutable_instance()

    def tearDown(self):
        self.zone_manager.stop_auto_report_watch_dog()
        self.fan._cancel_timer()
        self.light._cancel_timer()

        super(ImmutableZoneManagerTest, self).tearDown()

    def testDispatch_zoneIdInItemName_returnsTrue(self):
        self.assertTrue(self.immutable_zm.dispatch_event(
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.lightItem))
        self.assertTrue(self.zone1.dispatched)
        self.assertFalse(self.zone2.dispatched)

    def testDispatch_zoneIdNotInItemNameButItemInZone_returnsTrue(self):
        self.assertTrue(self.immutable_zm.dispatch_event(
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.motionSensorItem))
        self.assertTrue(self.zone1.dispatched)
        self.assertFalse(self.zone2.dispatched)

    def testDispatch_zoneIdInItemNameButIdNotMapToZoneAndItemInZone_returnsTrue(self):
        self.assertTrue(self.immutable_zm.dispatch_event(
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.fanItem))
        self.assertFalse(self.zone1.dispatched)
        self.assertTrue(self.zone2.dispatched)

    def testDispatch_zoneIdNotInItemNameAndItemInMultipleZones_returnsTrue(self):
        self.assertTrue(self.immutable_zm.dispatch_event(
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.shared_light_item))
        self.assertTrue(self.zone1.dispatched)
        self.assertTrue(self.zone2.dispatched)

    def testDispatch_itemNotInAnyZone_returnsTrue(self):
        self.assertFalse(self.immutable_zm.dispatch_event(
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.illuminanceSensorItem))
        self.assertFalse(self.zone1.dispatched)
        self.assertFalse(self.zone2.dispatched)
