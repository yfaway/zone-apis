from aaa_modules import platform_encapsulator as pe

from aaa_modules.layout_model.zone import Zone, Level, ZoneEvent, createExternalZone, createFirstFloorZone, \
    createSecondFloorZone
from aaa_modules.layout_model.neighbor import Neighbor, NeighborType
from aaa_modules.layout_model.event_info import EventInfo

from aaa_modules.layout_model.devices.astro_sensor import AstroSensor
from aaa_modules.layout_model.devices.dimmer import Dimmer
from aaa_modules.layout_model.devices.illuminance_sensor import IlluminanceSensor
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.devices.switch import Fan, Light

from aaa_modules.layout_model.actions.turn_on_switch import TurnOnSwitch
from aaa_modules.layout_model.actions.turn_off_adjacent_zones import TurnOffAdjacentZones

from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager

ILLUMINANCE_THRESHOLD_IN_LUX = 10


class ZoneTest(DeviceTest):
    """ Unit tests for zone_manager.py. """

    def setUp(self):
        items = [pe.create_switch_item('TestLightName'),
                 pe.create_switch_item('TestMotionSensorName'),
                 pe.create_number_item('IlluminanceSensorName'),
                 pe.create_string_item('AstroSensorName'),
                 pe.create_dimmer_item('TestDimmerName'),
                 pe.create_switch_item('TestFanName'),
                 pe.create_switch_item('TestPlug'),
                 pe.create_number_item('TestPlugPower'),
                 ]
        self.set_items(items)
        super(ZoneTest, self).setUp()

        [self.lightItem, self.motionSensorItem,
         self.illuminanceSensorItem, self.astroSensorItem, self.dimmerItem,
         self.fanItem, self.plugItem, self.plugPowerItem] = items

        self.illuminanceSensor = IlluminanceSensor(self.illuminanceSensorItem)
        self.light = Light(self.lightItem, 2)
        self.lightWithIlluminance = Light(self.lightItem, 2,
                                          ILLUMINANCE_THRESHOLD_IN_LUX)
        self.motionSensor = MotionSensor(self.motionSensorItem)
        self.astroSensor = AstroSensor(self.astroSensorItem)
        self.dimmer = Dimmer(self.dimmerItem, 2, 100, "0-23:59")
        self.fan = Fan(self.lightItem, 2)

    def tearDown(self):
        self.fan._cancel_timer()
        self.dimmer._cancel_timer()
        self.lightWithIlluminance._cancel_timer()
        self.light._cancel_timer()

        super(ZoneTest, self).tearDown()

    def testZoneCtor_validParams_gettersReturnValidValues(self):
        zone_name = 'bed room'
        zone = Zone(zone_name, [self.light], Level.SECOND_FLOOR)
        self.assertEqual(zone_name, zone.getName())
        self.assertEqual(Level.SECOND_FLOOR, zone.getLevel())
        self.assertEqual(Level.SECOND_FLOOR.value + '_' + zone_name, zone.getId())
        self.assertEqual(1, len(zone.getDevices()))

    def testCreateExternalZone_validParams_returnsAnExternalZone(self):
        zone_name = 'bed room'
        zone = createExternalZone(zone_name)
        self.assertEqual(zone_name, zone.getName())
        self.assertTrue(zone.isExternal())

    def testCreateFirstFloorZone_validParams_returnsAFirstFloorZone(self):
        zone_name = 'bed room'
        zone = createFirstFloorZone(zone_name)
        self.assertEqual(zone_name, zone.getName())
        self.assertEqual(Level.FIRST_FLOOR, zone.getLevel())
        self.assertFalse(zone.isExternal())

    def testCreateSecondFloorZone_validParams_returnsASecondFloorZone(self):
        zone_name = 'bed room'
        zone = createSecondFloorZone(zone_name)
        self.assertEqual(zone_name, zone.getName())
        self.assertEqual(Level.SECOND_FLOOR, zone.getLevel())
        self.assertFalse(zone.isExternal())

    def testContainsOpenHabItem_negativeValue_returnsFalse(self):
        zone = Zone('name', [self.light], Level.SECOND_FLOOR)
        self.assertFalse(zone.containsOpenHabItem(self.fanItem))

    def testContainsOpenHabItem_validNameButWrongType_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor, self.astroSensor])
        self.assertFalse(zone.containsOpenHabItem(
            self.lightItem, MotionSensor))

    def testContainsOpenHabItem_validNameWithNoTypeSpecified_returnsTrue(self):
        zone = Zone('ff', [self.light, self.motionSensor, self.astroSensor])
        self.assertTrue(zone.containsOpenHabItem(self.lightItem))

    def testContainsOpenHabItem_validNameWithTypeSpecified_returnsTrue(self):
        zone = Zone('ff', [self.light, self.motionSensor, self.astroSensor])
        self.assertTrue(zone.containsOpenHabItem(self.lightItem, Light))

    def testAddDevice_validDevice_deviceAdded(self):
        zone = Zone('ff').addDevice(self.light)
        self.assertEqual(1, len(zone.getDevices()))

    def testRemoveDevice_validDevice_deviceRemoved(self):
        zone = Zone('ff', [self.light])
        self.assertEqual(1, len(zone.getDevices()))

        zone = zone.removeDevice(self.light)
        self.assertEqual(0, len(zone.getDevices()))

    def testGetDevicesByType_validType_returnsExpectedDevices(self):
        zone = Zone('ff', [self.light])
        self.assertEqual(1, len(zone.getDevicesByType(Light)))
        self.assertEqual(0, len(zone.getDevicesByType(Dimmer)))

    def testGetDeviceByEvent_validEvent_returnsExpectedDevice(self):
        zone = Zone('ff', [self.light])

        event_info = EventInfo(ZoneEvent.MOTION, self.lightItem, zone,
                               create_zone_manager([zone]), pe.get_test_event_dispatcher())
        self.assertEqual(self.light, zone.getDeviceByEvent(event_info))

    def testGetDeviceByEvent_invalidEvent_returnsNone(self):
        zone = Zone('ff', [self.light])

        event_info = EventInfo(ZoneEvent.MOTION, self.motionSensorItem, zone,
                               create_zone_manager([zone]), pe.get_test_event_dispatcher())
        self.assertEqual(None, zone.getDeviceByEvent(event_info))

    def testAddAction_oneValidAction_actionAdded(self):
        zone = Zone('ff').add_action(TurnOnSwitch())
        self.assertEqual(1, len(zone.get_actions(ZoneEvent.MOTION)))

        self.assertEqual(0, len(zone.get_actions(ZoneEvent.SWITCH_TURNED_ON)))

    def testAddAction_twoValidAction_actionAdded(self):
        zone = Zone('ff').add_action(TurnOnSwitch())
        zone = zone.add_action(TurnOffAdjacentZones())
        self.assertEqual(1, len(zone.get_actions(ZoneEvent.MOTION)))
        self.assertEqual(1, len(zone.get_actions(ZoneEvent.SWITCH_TURNED_ON)))

    def testIsOccupied_everythingOff_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        (occupied, device) = zone.isOccupied()
        self.assertFalse(occupied)
        self.assertEqual(None, device)

    def testIsOccupied_switchIsOn_returnsTrue(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.light.turnOn(pe.get_test_event_dispatcher())

        (occupied, device) = zone.isOccupied()
        self.assertTrue(occupied)
        self.assertEqual(self.light, device)

    def testIsOccupied_switchIsOnAndIgnoreMotionSensor_returnsTrue(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.light.turnOn(pe.get_test_event_dispatcher())

        (occupied, device) = zone.isOccupied([MotionSensor])
        self.assertTrue(occupied)
        self.assertEqual(self.light, device)

    def testIsOccupied_switchIsOnAndIgnoreLight_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.light.turnOn(pe.get_test_event_dispatcher())

        (occupied, device) = zone.isOccupied([Light])
        self.assertFalse(occupied)
        self.assertEqual(None, device)

    def testIsOccupied_switchIsOnAndIgnoreLightAndMotionSensor_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.light.turnOn(pe.get_test_event_dispatcher())

        (occupied, device) = zone.isOccupied([Light, MotionSensor])
        self.assertFalse(occupied)
        self.assertEqual(None, device)

    def testIsOccupied_motionEventTriggeredButLightIsOff_returnsTrue(self):
        self.assertFalse(self.light.isOn())

        zone = Zone('ff', [self.light, self.motionSensor, self.illuminanceSensor])
        self.motionSensor._update_last_activated_timestamp()
        (occupied, device) = zone.isOccupied()
        self.assertTrue(occupied)
        self.assertEqual(self.motionSensor, device)

    def testGetIlluminanceLevel_noSensor_returnsMinusOne(self):
        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor])
        self.assertEqual(-1, zone.getIlluminanceLevel())

    def testGetIlluminanceLevel_withSensor_returnsPositiveValue(self):
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX, True)

        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor,
                           self.illuminanceSensor])
        self.assertEqual(ILLUMINANCE_THRESHOLD_IN_LUX, zone.getIlluminanceLevel())

    def testIsLightOnTime_noSensor_returnsNone(self):
        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor])
        self.assertEqual(None, zone.isLightOnTime())

    def testIsLightOnTime_withSensorIndicatesDayTime_returnsFalse(self):
        pe.set_string_value(self.astroSensorItem, 'MORNING', True)
        zone = Zone('ff', [self.lightWithIlluminance, self.astroSensor])
        self.assertFalse(zone.isLightOnTime())

    def testIsLightOnTime_withSensorIndicatesEveningTime_returnsTrue(self):
        pe.set_string_value(self.astroSensorItem, AstroSensor.LIGHT_ON_TIMES[0], True)
        zone = Zone('ff', [self.lightWithIlluminance, self.astroSensor])
        self.assertTrue(zone.isLightOnTime())

    def testShareSensorWith_noSharedSensors_returnsFalse(self):
        zone1 = Zone('ff', [self.lightWithIlluminance, self.astroSensor])
        zone2 = Zone('foyer', [])

        self.assertFalse(zone1.shareSensorWith(zone2, Light))

    def testShareSensorWith_sharedSensorsWithNoChannel_returnsFalse(self):
        zone1 = Zone('ff', [self.lightWithIlluminance, self.astroSensor])
        zone2 = Zone('foyer', [self.lightWithIlluminance])

        self.assertFalse(zone1.shareSensorWith(zone2, Light))

    def testShareSensorWith_sharedSensorsWithChannel_returnsTrue(self):
        zone1 = Zone('ff', [self.lightWithIlluminance, self.astroSensor])
        zone2 = Zone('foyer', [self.lightWithIlluminance])

        self.lightWithIlluminance.getChannel = lambda: 'a channel'
        self.assertTrue(zone1.shareSensorWith(zone2, Light))

    def testOnTimerExpired_invalidTimerItem_returnsFalse(self):
        zone = Zone('ff', [self.light])

        is_processed = zone.onTimerExpired(
            pe.get_test_event_dispatcher(), pe.create_string_item('dummy name'))
        self.assertFalse(is_processed)

    def testOnSwitchedTurnedOn_validItemName_returnsTrue(self):
        zone = Zone('ff', [self.light])

        is_processed = zone.on_switch_turned_on(pe.get_test_event_dispatcher(), self.lightItem, None)
        self.assertTrue(is_processed)

    def testOnSwitchedTurnedOff_validItemName_returnsTrue(self):
        zone = Zone('ff', [self.light])

        is_processed = zone.on_switch_turned_off(pe.get_test_event_dispatcher(), self.lightItem, None)
        self.assertTrue(is_processed)

    def testOnMotionSensorTurnedOn_validItemNameNoIlluminanceSensorNoAstroSensor_returnsFalse(self):
        self.assertFalse(self.light.isOn())

        zone = Zone('ff', [self.light, self.motionSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_test_event_dispatcher(),
                                           self.motionSensor.getItem(), create_zone_manager([zone]), True)
        self.assertFalse(is_processed)

    def testOnMotionSensorTurnedOn_illuminanceAboveThreshold_returnsFalse(self):
        self.assertFalse(self.light.isOn())
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX + 1, True)

        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor,
                           self.illuminanceSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_test_event_dispatcher(),
                                           self.motionSensor.getItem(), create_zone_manager([zone]), True)
        self.assertFalse(is_processed)
        self.assertFalse(self.light.isOn())

    def testOnMotionSensorTurnedOn_illuminanceBelowThreshold_turnsOnLight(self):
        self.assertFalse(self.light.isOn())
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1, True)

        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor,
                           self.illuminanceSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_test_event_dispatcher(),
                                           self.motionSensor.getItem(), create_zone_manager([zone]), True)
        self.assertTrue(is_processed)

        self.assertTrue(self.light.isOn())

    def testOnMotionSensorTurnedOn_notLightOnTime_returnsFalse(self):
        pe.set_string_value(self.astroSensorItem, 'MORNING', True)

        zone = Zone('ff', [self.light, self.astroSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_test_event_dispatcher(),
                                           self.motionSensor.getItem(), None, True)
        self.assertFalse(is_processed)

    def testOnMotionSensorTurnedOn_notLightOnTimeButIlluminanceBelowThreshold_turnsOnLight(self):
        self.assertFalse(self.light.isOn())
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1, True)
        pe.set_string_value(self.astroSensorItem, 'MORNING', True)

        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor,
                           self.illuminanceSensor, self.astroSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_test_event_dispatcher(),
                                           self.motionSensor.getItem(), create_zone_manager([zone]), True)
        self.assertTrue(is_processed)
        self.assertTrue(self.light.isOn())

    def testOnMotionSensorTurnedOn_lightOnTime_turnsOnLight(self):
        self.assertFalse(self.light.isOn())

        pe.set_string_value(self.astroSensorItem, AstroSensor.LIGHT_ON_TIMES[0], True)
        zone = Zone('ff', [self.light, self.motionSensor, self.astroSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_test_event_dispatcher(),
                                           self.motionSensor.getItem(), create_zone_manager([zone]), True)
        self.assertTrue(is_processed)
        self.assertTrue(self.light.isOn())

    def testStr_noParam_returnsNonEmptyString(self):
        zone = Zone('ff', [self.light, self.motionSensor, self.astroSensor,
                           self.illuminanceSensor, self.dimmer, self.fan])
        info = str(zone)

        self.assertTrue(len(info) > 0)

    def testGetNeighborZones_noZoneManager_throwsException(self):
        zone1 = Zone('ff')
        with self.assertRaises(ValueError) as cm:
            zone1.getNeighborZones(None)

        self.assertEqual('zoneManager must not be None', cm.exception.args[0])

    def testGetNeighborZones_noNeighborTypesSpecified_returnsCorrectList(self):
        zone1 = Zone('foyer')
        zone2 = Zone('porch')
        zone3 = Zone('office')

        zone1 = zone1.add_neighbor(Neighbor(zone2.getId(), NeighborType.OPEN_SPACE))
        zone1 = zone1.add_neighbor(Neighbor(zone3.getId(), NeighborType.OPEN_SPACE_MASTER))
        zm = create_zone_manager([zone1, zone2, zone3])

        self.assertEqual(2, len(zone1.getNeighborZones(zm)))

    def testGetNeighborZones_neighborTypeSpecified_returnsCorrectList(self):
        zone1 = Zone('foyer')
        zone2 = Zone('porch')
        zone3 = Zone('office')

        zone1 = zone1.add_neighbor(Neighbor(zone2.getId(), NeighborType.OPEN_SPACE))
        zone1 = zone1.add_neighbor(Neighbor(zone3.getId(), NeighborType.OPEN_SPACE_MASTER))
        zm = create_zone_manager([zone1, zone2, zone3])

        zones = zone1.getNeighborZones(zm, [NeighborType.OPEN_SPACE_MASTER])
        self.assertEqual(1, len(zones))
        self.assertEqual(zone3, zones[0])
