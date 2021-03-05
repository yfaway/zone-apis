from typing import List

from aaa_modules.layout_model.device import Device
from aaa_modules.layout_model.neighbor import Neighbor
from aaa_modules.layout_model.zone_manager import ZoneManager
from aaa_modules import platform_encapsulator as pe

from aaa_modules.layout_model.zone import Zone, Level
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.devices.switch import Fan, Light
from aaa_modules.layout_model.devices.illuminance_sensor import IlluminanceSensor
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor

from zone_apis_test.layout_model.device_test import DeviceTest


class ImmutableZoneManagerTest(DeviceTest):
    """ Unit tests for immutable_zone_manager.py. """

    def setUp(self):
        items = [pe.create_switch_item('FF_Kitchen_TestLightName'),
                 pe.create_switch_item('TestMotionSensorName'),
                 pe.create_number_item('IlluminanceSensorName'),
                 pe.create_switch_item('BM_Utility_TestFanName'),
                 pe.create_switch_item('SharedLight'),
                 ]

        self.set_items(items)
        super(ImmutableZoneManagerTest, self).setUp()

        [self.lightItem, self.motionSensorItem, self.illuminanceSensorItem,
         self.fanItem, self.shared_light_item] = items

        self.motionSensor = MotionSensor(self.motionSensorItem)
        self.light = Light(self.lightItem, 2)
        self.illuminanceSensor = IlluminanceSensor(self.illuminanceSensorItem)
        self.fan = Fan(self.fanItem, 2)
        self.shared_light = Light(self.shared_light_item, 2)

        self.dispatched_zones = []

        class MyZone(Zone):
            """ Subclass Zone to simplify the behavior of dispatch_event. """

            def __init__(self, dispatched_list, name, devices: List[Device] = None, level=Level.UNDEFINED,
                         neighbors: List[Neighbor] = None, actions=None, external=False,
                         display_icon=None, display_order=9999):
                super().__init__(name, devices, level, neighbors, actions, external, display_icon, display_order)

                self.dispatched_zones = dispatched_list

            def dispatch_event(self, zone_event, open_hab_events, item,
                               immutable_zone_manager, owning_zone=None):

                self.dispatched_zones.append(self)
                return True

        self.zone1 = MyZone(self.dispatched_zones, 'Foyer', [self.fan, self.motionSensor, self.shared_light],
                            Level.FIRST_FLOOR)
        self.zone2 = MyZone(self.dispatched_zones, 'Kitchen', [self.light, self.shared_light], Level.FIRST_FLOOR)

        self.zone_manager = ZoneManager().add_zone(self.zone1).add_zone(self.zone2)
        self.immutable_zm = self.zone_manager.get_immutable_instance()
        self.immutable_zm.start()

    def tearDown(self):
        self.immutable_zm.stop()
        self.zone_manager.stop_auto_report_watch_dog()
        self.fan._cancel_timer()
        self.light._cancel_timer()

        super(ImmutableZoneManagerTest, self).tearDown()

    def testDispatch_itemNameMappableToZone_correctZoneDispatchedFirst(self):
        self.assertTrue(self.immutable_zm.dispatch_event(
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.lightItem))
        self.assertEqual(self.dispatched_zones, [self.zone2, self.zone1])

    def testDispatch_itemInMultipleZones_returnsTrue(self):
        self.assertTrue(self.immutable_zm.dispatch_event(
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.shared_light_item))
        self.assertTrue(self.zone1 in self.dispatched_zones)
        self.assertTrue(self.zone2 in self.dispatched_zones)

    def testDispatch_itemNotInAnyZone_dispatchToAllZoneAndReturnsTrue(self):
        self.assertTrue(self.immutable_zm.dispatch_event(
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.illuminanceSensorItem))
        self.assertTrue(self.zone1 in self.dispatched_zones, [self.zone1, self.zone2])
