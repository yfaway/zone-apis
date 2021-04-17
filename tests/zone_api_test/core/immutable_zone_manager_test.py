from typing import List

from zone_api.core.device import Device
from zone_api.core.devices.astro_sensor import AstroSensor
from zone_api.core.devices.thermostat import EcobeeThermostat
from zone_api.core.neighbor import Neighbor
from zone_api.core.zone_manager import ZoneManager
from zone_api import platform_encapsulator as pe

from zone_api.core.zone import Zone, Level
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.switch import Fan, Light
from zone_api.core.devices.illuminance_sensor import IlluminanceSensor
from zone_api.core.devices.motion_sensor import MotionSensor

from zone_api_test.core.device_test import DeviceTest


class ImmutableZoneManagerTest(DeviceTest):
    """ Unit tests for immutable_zone_manager.py. """

    def setUp(self):
        items = [pe.create_switch_item('FF_Kitchen_TestLightName'),
                 pe.create_switch_item('TestMotionSensorName'),
                 pe.create_number_item('IlluminanceSensorName'),
                 pe.create_switch_item('BM_Utility_TestFanName'),
                 pe.create_switch_item('SharedLight'),
                 pe.create_string_item('EcobeeName'),
                 pe.create_string_item('EcobeeEventType'),
                 pe.create_string_item('AstroSensorName'),
                 ]

        self.set_items(items)
        super(ImmutableZoneManagerTest, self).setUp()

        [self.lightItem, self.motionSensorItem, self.illuminanceSensorItem,
         self.fanItem, self.shared_light_item, self.ecobee_name_item, self.ecobee_event_type,
         self.astroSensorItem] = items

        self.motionSensor = MotionSensor(self.motionSensorItem)
        self.light = Light(self.lightItem, 2)
        self.illuminanceSensor = IlluminanceSensor(self.illuminanceSensorItem)
        self.fan = Fan(self.fanItem, 2)
        self.shared_light = Light(self.shared_light_item, 2)
        self.thermostat = EcobeeThermostat(self.ecobee_name_item, self.ecobee_event_type)
        self.astroSensor = AstroSensor(self.astroSensorItem)

        self.dispatched_zones = []

        class MyZone(Zone):
            """ Subclass Zone to simplify the behavior of dispatch_event. """

            def __init__(self, dispatched_list, name, devices: List[Device] = None, level=Level.UNDEFINED,
                         neighbors: List[Neighbor] = None, actions=None, external=False,
                         display_icon=None, display_order=9999):
                super().__init__(name, devices, level, neighbors, actions, external, display_icon, display_order)

                self.dispatched_zones = dispatched_list

            def dispatch_event(self, zone_event, open_hab_events, device, item,
                               immutable_zone_manager, owning_zone=None):

                self.dispatched_zones.append(self)
                return True

        self.zone1 = MyZone(self.dispatched_zones, 'Foyer', [self.fan, self.motionSensor, self.shared_light],
                            Level.FIRST_FLOOR)
        self.zone2 = MyZone(self.dispatched_zones, 'Kitchen', [self.light, self.shared_light], Level.FIRST_FLOOR)
        self.zone3 = MyZone(self.dispatched_zones, 'GreatRoom', [self.thermostat], Level.FIRST_FLOOR)
        self.zone4 = MyZone(self.dispatched_zones, 'Virtual', [self.astroSensor], Level.FIRST_FLOOR)

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
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.light, self.lightItem))
        self.assertEqual(self.dispatched_zones, [self.zone2, self.zone1])

    def testDispatch_itemInMultipleZones_returnsTrue(self):
        self.assertTrue(self.immutable_zm.dispatch_event(
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.shared_light, self.shared_light_item))
        self.assertTrue(self.zone1 in self.dispatched_zones)
        self.assertTrue(self.zone2 in self.dispatched_zones)

    def testDispatch_itemNotInAnyZone_dispatchToAllZoneAndReturnsTrue(self):
        self.assertTrue(self.immutable_zm.dispatch_event(
            ZoneEvent.MOTION, pe.get_event_dispatcher(), self.illuminanceSensor, self.illuminanceSensorItem))
        self.assertTrue(self.zone1 in self.dispatched_zones, [self.zone1, self.zone2])

    def testIsInVacation_noDeviceImplementVacation_returnsFalse(self):
        self.assertFalse(self.immutable_zm.is_in_vacation())

    def testIsInVacation_oneDeviceImplementVacationButNotInVacation_returnsFalse(self):
        zm = ZoneManager().add_zone(self.zone1).add_zone(self.zone2).add_zone(self.zone3)
        izm = zm.get_immutable_instance()

        self.assertFalse(izm.is_in_vacation())

    def testIsInVacation_inVacationMode_returnsTrue(self):
        pe.set_string_value(self.ecobee_event_type, 'vacation')
        zm = ZoneManager().add_zone(self.zone1).add_zone(self.zone2).add_zone(self.zone3)
        izm = zm.get_immutable_instance()

        self.assertTrue(izm.is_in_vacation())

    def testIsLightOnTime_noSensor_returnsNone(self):
        self.assertEqual(None, self.immutable_zm.is_light_on_time())

    def testIsLightOnTime_withSensorIndicatesDayTime_returnsFalse(self):
        pe.set_string_value(self.astroSensorItem, 'MORNING')
        izm = ZoneManager().add_zone(self.zone4).get_immutable_instance()
        self.assertFalse(izm.is_light_on_time())

    def testIsLightOnTime_withSensorIndicatesEveningTime_returnsTrue(self):
        pe.set_string_value(self.astroSensorItem, AstroSensor.LIGHT_ON_TIMES[0])
        izm = ZoneManager().add_zone(self.zone4).get_immutable_instance()
        self.assertTrue(izm.is_light_on_time())
