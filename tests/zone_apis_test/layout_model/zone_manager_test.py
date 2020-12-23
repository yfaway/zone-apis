from aaa_modules.layout_model.zone_manager import ZoneManager
from aaa_modules import platform_encapsulator as pe

from aaa_modules.layout_model.zone import Zone, ZoneEvent
from aaa_modules.layout_model.devices.dimmer import Dimmer
from aaa_modules.layout_model.devices.switch import Fan, Light, Switch
from aaa_modules.layout_model.devices.illuminance_sensor import IlluminanceSensor
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.actions.turn_on_switch import TurnOnSwitch

from zone_apis_test.layout_model.device_test import DeviceTest

ILLUMINANCE_THRESHOLD_IN_LUX = 8
INVALID_ITEM_NAME = 'invalid item name'


class ZoneManagerTest(DeviceTest):
    """ Unit tests for zone_manager.py. """

    def setUp(self):
        items = [pe.create_switch_item('TestLightName'),
                 pe.create_switch_item('TestMotionSensorName'),
                 pe.create_number_item('IlluminanceSensorName'),
                 pe.create_string_item('AstroSensorName'),
                 pe.create_dimmer_item('TestDimmerName'),
                 pe.create_switch_item('TestFanName'),
                 ]

        self.set_items(items)
        super(ZoneManagerTest, self).setUp()

        [self.lightItem, self.motionSensorItem,
         self.illuminanceSensorItem, self.astroSensorItem, self.dimmerItem,
         self.fanItem] = items

        self.illuminanceSensor = IlluminanceSensor(self.illuminanceSensorItem)
        self.light = Light(self.lightItem, 2,
                           ILLUMINANCE_THRESHOLD_IN_LUX)
        self.motionSensor = MotionSensor(self.motionSensorItem)
        self.dimmer = Dimmer(self.dimmerItem, 2, 100, "0-23:59")
        self.fan = Fan(self.fanItem, 2)

        self.zm = ZoneManager()

    def tearDown(self):
        self.zm.stop_auto_report_watch_dog()
        self.fan._cancel_timer()
        self.dimmer._cancel_timer()
        self.light._cancel_timer()

        super(ZoneManagerTest, self).tearDown()

    def testAddZone_validZone_zoneAdded(self):
        zone1 = Zone('ff')
        self.zm.add_zone(zone1)
        self.assertEqual(1, len(self.zm.get_zones()))

        zone2 = Zone('2f')
        self.zm.add_zone(zone2)
        self.assertEqual(2, len(self.zm.get_zones()))

    def testGetZoneById_validZoneId_returnValidZone(self):
        zone1 = Zone('ff')
        self.zm.add_zone(zone1)

        zone2 = Zone('2f')
        self.zm.add_zone(zone2)

        self.assertEqual(zone1.getName(),
                         self.zm.get_zone_by_id(zone1.getId()).getName())
        self.assertEqual(zone2.getName(),
                         self.zm.get_zone_by_id(zone2.getId()).getName())

    def testGetZoneById_invalidZoneId_returnNone(self):
        self.assertTrue(self.zm.get_zone_by_id('invalid zone id') is None)

    def testRemoveZone_validZone_zoneRemoved(self):
        zone1 = Zone('ff')
        self.zm.add_zone(zone1)

        zone2 = Zone('2f')
        self.zm.add_zone(zone2)

        self.assertEqual(2, len(self.zm.get_zones()))

        self.zm.remove_zone(zone1)
        self.assertEqual(1, len(self.zm.get_zones()))

        self.zm.remove_zone(zone2)
        self.assertEqual(0, len(self.zm.get_zones()))

    def testContainingZone_validDevice_returnsCorrectZone(self):
        zone1 = Zone('ff').addDevice(self.light)
        zone2 = Zone('sf').addDevice(self.fan)

        self.zm.add_zone(zone1)
        self.zm.add_zone(zone2)
        self.assertEqual(zone1,
                         self.zm.get_immutable_instance().get_containing_zone(self.light))
        self.assertEqual(zone2,
                         self.zm.get_immutable_instance().get_containing_zone(self.fan))

    def testContainingZone_invalidDevice_returnsNone(self):
        zone1 = Zone('ff').addDevice(self.light)

        self.zm.add_zone(zone1)
        self.assertEqual(None,
                         self.zm.get_immutable_instance().get_containing_zone(self.fan))

    def testGetDevicesByType_variousScenarios_returnsCorrectList(self):
        zone1 = Zone('ff').addDevice(self.light)
        zone2 = Zone('sf').addDevice(self.fan)

        self.zm.add_zone(zone1)
        self.zm.add_zone(zone2)
        self.assertEqual(2, len(self.zm.get_zones()))

        self.assertEqual(1, len(self.zm.get_devices_by_type(Light)))
        self.assertEqual(2, len(self.zm.get_devices_by_type(Switch)))

        self.assertEqual(0, len(self.zm.get_devices_by_type(Dimmer)))

    def testOnMotionSensorTurnedOn_noZone_returnsFalse(self):
        self.assertFalse(self.zm.dispatch_event(ZoneEvent.MOTION,
                                                pe.get_test_event_dispatcher(),
                                                pe.create_string_item(INVALID_ITEM_NAME)))

    def testOnMotionSensorTurnedOn_withNonApplicableZone_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.zm.add_zone(zone)

        self.assertFalse(self.zm.dispatch_event(ZoneEvent.MOTION,
                                                pe.get_test_event_dispatcher(),
                                                pe.create_string_item(INVALID_ITEM_NAME)))

    def testOnMotionSensorTurnedOn_withApplicableZone_returnsTrue(self):
        self.assertFalse(self.light.isOn())
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1, True)

        zone = Zone('ff', [self.light, self.motionSensor, self.illuminanceSensor])
        zone = zone.add_action(TurnOnSwitch())
        self.zm.add_zone(zone)

        self.assertTrue(self.zm.dispatch_event(ZoneEvent.MOTION,
                                               pe.get_test_event_dispatcher(), self.motionSensor.getItem()))

    def testOnTimerExpired_noZone_returnsFalse(self):
        self.assertFalse(self.zm.on_timer_expired(
            pe.get_test_event_dispatcher(), pe.create_string_item(INVALID_ITEM_NAME)))

    def testOnTimerExpired_withNonApplicableZone_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.zm.add_zone(zone)

        self.assertFalse(self.zm.on_timer_expired(
            pe.get_test_event_dispatcher(), pe.create_string_item(INVALID_ITEM_NAME)))

    def testOnSwitchTurnedOn_noZone_returnsFalse(self):
        self.assertFalse(self.zm.on_switch_turned_on(
            pe.get_test_event_dispatcher(), pe.create_string_item(INVALID_ITEM_NAME)))

    def testOnSwitchTurnedOn_withNonApplicableZone_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.zm.add_zone(zone)

        self.assertFalse(self.zm.on_switch_turned_on(
            pe.get_test_event_dispatcher(), pe.create_string_item(INVALID_ITEM_NAME)))

    def testOnSwitchTurnedOn_withApplicableZone_returnsTrue(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.zm.add_zone(zone)

        self.assertTrue(self.zm.on_switch_turned_on(
            pe.get_test_event_dispatcher(), self.light.getItem()))

    def testOnSwitchTurnedOff_noZone_returnsFalse(self):
        self.assertFalse(self.zm.on_switch_turned_off(
            pe.get_test_event_dispatcher(), pe.create_string_item(INVALID_ITEM_NAME)))

    def testOnSwitchTurnedOff_withNonApplicableZone_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.zm.add_zone(zone)

        self.assertFalse(self.zm.on_switch_turned_off(
            pe.get_test_event_dispatcher(), pe.create_string_item(INVALID_ITEM_NAME)))

    def testOnSwitchTurnedOff_withApplicableZone_returnsTrue(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.zm.add_zone(zone)

        self.assertTrue(self.zm.on_switch_turned_off(
            pe.get_test_event_dispatcher(), self.light.getItem()))
