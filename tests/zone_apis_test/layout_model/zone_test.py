from aaa_modules import platform_encapsulator as pe

from aaa_modules.layout_model.zone import Zone, Level
from aaa_modules.layout_model.zone_event import ZoneEvent
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
        self.assertEqual(zone_name, zone.get_name())
        self.assertEqual(Level.SECOND_FLOOR, zone.get_level())
        self.assertEqual(Level.SECOND_FLOOR.value + '_' + zone_name, zone.get_id())
        self.assertEqual(1, len(zone.get_devices()))

    def testCreateExternalZone_validParams_returnsAnExternalZone(self):
        zone_name = 'bed room'
        zone = Zone.create_external_zone(zone_name)
        self.assertEqual(zone_name, zone.get_name())
        self.assertTrue(zone.is_external())

    def testCreateFirstFloorZone_validParams_returnsAFirstFloorZone(self):
        zone_name = 'bed room'
        zone = Zone.create_first_floor_zone(zone_name)
        self.assertEqual(zone_name, zone.get_name())
        self.assertEqual(Level.FIRST_FLOOR, zone.get_level())
        self.assertFalse(zone.is_external())

    def testCreateSecondFloorZone_validParams_returnsASecondFloorZone(self):
        zone_name = 'bed room'
        zone = Zone.create_second_floor_zone(zone_name)
        self.assertEqual(zone_name, zone.get_name())
        self.assertEqual(Level.SECOND_FLOOR, zone.get_level())
        self.assertFalse(zone.is_external())

    def testContainsOpenHabItem_negativeValue_returnsFalse(self):
        zone = Zone('name', [self.light], Level.SECOND_FLOOR)
        self.assertFalse(zone.contains_open_hab_item(self.fanItem))

    def testContainsOpenHabItem_validNameButWrongType_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor, self.astroSensor])
        self.assertFalse(zone.contains_open_hab_item(
            self.lightItem, MotionSensor))

    def testContainsOpenHabItem_validNameWithNoTypeSpecified_returnsTrue(self):
        zone = Zone('ff', [self.light, self.motionSensor, self.astroSensor])
        self.assertTrue(zone.contains_open_hab_item(self.lightItem))

    def testContainsOpenHabItem_validNameWithTypeSpecified_returnsTrue(self):
        zone = Zone('ff', [self.light, self.motionSensor, self.astroSensor])
        self.assertTrue(zone.contains_open_hab_item(self.lightItem, Light))

    def testAddDevice_validDevice_deviceAdded(self):
        zone = Zone('ff').add_device(self.light)
        self.assertEqual(1, len(zone.get_devices()))

    def testRemoveDevice_validDevice_deviceRemoved(self):
        zone = Zone('ff', [self.light])
        self.assertEqual(1, len(zone.get_devices()))

        zone = zone.remove_device(self.light)
        self.assertEqual(0, len(zone.get_devices()))

    def testGetDevicesByType_validType_returnsExpectedDevices(self):
        zone = Zone('ff', [self.light])
        self.assertEqual(1, len(zone.get_devices_by_type(Light)))
        self.assertEqual(0, len(zone.get_devices_by_type(Dimmer)))

    def testGetDeviceByEvent_validEvent_returnsExpectedDevice(self):
        zone = Zone('ff', [self.light])

        event_info = EventInfo(ZoneEvent.MOTION, self.lightItem, zone,
                               create_zone_manager([zone]), pe.get_event_dispatcher())
        self.assertEqual(self.light, zone.get_device_by_event(event_info))

    def testGetDeviceByEvent_invalidEvent_returnsNone(self):
        zone = Zone('ff', [self.light])

        event_info = EventInfo(ZoneEvent.MOTION, self.motionSensorItem, zone,
                               create_zone_manager([zone]), pe.get_event_dispatcher())
        self.assertEqual(None, zone.get_device_by_event(event_info))

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
        (occupied, device) = zone.is_occupied()
        self.assertFalse(occupied)
        self.assertEqual(None, device)

    def testIsOccupied_switchIsOn_returnsTrue(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.light.turn_on(pe.get_event_dispatcher())

        (occupied, device) = zone.is_occupied()
        self.assertTrue(occupied)
        self.assertEqual(self.light, device)

    def testIsOccupied_switchIsOnAndIgnoreMotionSensor_returnsTrue(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.light.turn_on(pe.get_event_dispatcher())

        (occupied, device) = zone.is_occupied([MotionSensor])
        self.assertTrue(occupied)
        self.assertEqual(self.light, device)

    def testIsOccupied_switchIsOnAndIgnoreLight_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.light.turn_on(pe.get_event_dispatcher())

        (occupied, device) = zone.is_occupied([Light])
        self.assertFalse(occupied)
        self.assertEqual(None, device)

    def testIsOccupied_switchIsOnAndIgnoreLightAndMotionSensor_returnsFalse(self):
        zone = Zone('ff', [self.light, self.motionSensor])
        self.light.turn_on(pe.get_event_dispatcher())

        (occupied, device) = zone.is_occupied([Light, MotionSensor])
        self.assertFalse(occupied)
        self.assertEqual(None, device)

    def testIsOccupied_motionEventTriggeredButLightIsOff_returnsTrue(self):
        self.assertFalse(self.light.is_on())

        zone = Zone('ff', [self.light, self.motionSensor, self.illuminanceSensor])
        self.motionSensor._update_last_activated_timestamp()
        (occupied, device) = zone.is_occupied()
        self.assertTrue(occupied)
        self.assertEqual(self.motionSensor, device)

    def testGetIlluminanceLevel_noSensor_returnsMinusOne(self):
        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor])
        self.assertEqual(-1, zone.get_illuminance_level())

    def testGetIlluminanceLevel_withSensor_returnsPositiveValue(self):
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX)

        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor,
                           self.illuminanceSensor])
        self.assertEqual(ILLUMINANCE_THRESHOLD_IN_LUX, zone.get_illuminance_level())

    def testIsLightOnTime_noSensor_returnsNone(self):
        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor])
        self.assertEqual(None, zone.is_light_on_time())

    def testIsLightOnTime_withSensorIndicatesDayTime_returnsFalse(self):
        pe.set_string_value(self.astroSensorItem, 'MORNING')
        zone = Zone('ff', [self.lightWithIlluminance, self.astroSensor])
        self.assertFalse(zone.is_light_on_time())

    def testIsLightOnTime_withSensorIndicatesEveningTime_returnsTrue(self):
        pe.set_string_value(self.astroSensorItem, AstroSensor.LIGHT_ON_TIMES[0])
        zone = Zone('ff', [self.lightWithIlluminance, self.astroSensor])
        self.assertTrue(zone.is_light_on_time())

    def testShareSensorWith_noSharedSensors_returnsFalse(self):
        zone1 = Zone('ff', [self.lightWithIlluminance, self.astroSensor])
        zone2 = Zone('foyer', [])

        self.assertFalse(zone1.share_sensor_with(zone2, Light))

    def testShareSensorWith_sharedSensorsWithNoChannel_returnsFalse(self):
        zone1 = Zone('ff', [self.lightWithIlluminance, self.astroSensor])
        zone2 = Zone('foyer', [self.lightWithIlluminance])

        self.assertFalse(zone1.share_sensor_with(zone2, Light))

    def testShareSensorWith_sharedSensorsWithChannel_returnsTrue(self):
        zone1 = Zone('ff', [self.lightWithIlluminance, self.astroSensor])
        zone2 = Zone('foyer', [self.lightWithIlluminance])

        self.lightWithIlluminance.get_channel = lambda: 'a channel'
        self.assertTrue(zone1.share_sensor_with(zone2, Light))

    def testOnTimerExpired_invalidTimerItem_returnsFalse(self):
        zone = Zone('ff', [self.light])

        is_processed = zone.on_timer_expired(
            pe.get_event_dispatcher(), pe.create_string_item('dummy name'))
        self.assertFalse(is_processed)

    def testOnSwitchedTurnedOn_validItemName_returnsTrue(self):
        zone = Zone('ff', [self.light])

        is_processed = zone.on_switch_turned_on(pe.get_event_dispatcher(), self.lightItem, None)
        self.assertTrue(is_processed)

    def testOnSwitchedTurnedOff_validItemName_returnsTrue(self):
        zone = Zone('ff', [self.light])

        is_processed = zone.on_switch_turned_off(pe.get_event_dispatcher(), self.lightItem, None)
        self.assertTrue(is_processed)

    def testOnMotionSensorTurnedOn_validItemNameNoIlluminanceSensorNoAstroSensor_returnsFalse(self):
        self.assertFalse(self.light.is_on())

        zone = Zone('ff', [self.light, self.motionSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_event_dispatcher(),
                                           self.motionSensor.get_item(), create_zone_manager([zone]), True)
        self.assertFalse(is_processed)

    def testOnMotionSensorTurnedOn_illuminanceAboveThreshold_returnsFalse(self):
        self.assertFalse(self.light.is_on())
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX + 1)

        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor,
                           self.illuminanceSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_event_dispatcher(),
                                           self.motionSensor.get_item(), create_zone_manager([zone]), True)
        self.assertFalse(is_processed)
        self.assertFalse(self.light.is_on())

    def testOnMotionSensorTurnedOn_illuminanceBelowThreshold_turnsOnLight(self):
        self.assertFalse(self.light.is_on())
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)

        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor,
                           self.illuminanceSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_event_dispatcher(),
                                           self.motionSensor.get_item(), create_zone_manager([zone]), True)
        self.assertTrue(is_processed)

        self.assertTrue(self.light.is_on())

    def testOnMotionSensorTurnedOn_notLightOnTime_returnsFalse(self):
        pe.set_string_value(self.astroSensorItem, 'MORNING')

        zone = Zone('ff', [self.light, self.astroSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_event_dispatcher(),
                                           self.motionSensor.get_item(), None, True)
        self.assertFalse(is_processed)

    def testOnMotionSensorTurnedOn_notLightOnTimeButIlluminanceBelowThreshold_turnsOnLight(self):
        self.assertFalse(self.light.is_on())
        pe.set_number_value(self.illuminanceSensorItem, ILLUMINANCE_THRESHOLD_IN_LUX - 1)
        pe.set_string_value(self.astroSensorItem, 'MORNING')

        zone = Zone('ff', [self.lightWithIlluminance, self.motionSensor,
                           self.illuminanceSensor, self.astroSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_event_dispatcher(),
                                           self.motionSensor.get_item(), create_zone_manager([zone]), True)
        self.assertTrue(is_processed)
        self.assertTrue(self.light.is_on())

    def testOnMotionSensorTurnedOn_lightOnTime_turnsOnLight(self):
        self.assertFalse(self.light.is_on())

        pe.set_string_value(self.astroSensorItem, AstroSensor.LIGHT_ON_TIMES[0])
        zone = Zone('ff', [self.light, self.motionSensor, self.astroSensor])
        zone = zone.add_action(TurnOnSwitch())

        is_processed = zone.dispatch_event(ZoneEvent.MOTION, pe.get_event_dispatcher(),
                                           self.motionSensor.get_item(), create_zone_manager([zone]), True)
        self.assertTrue(is_processed)
        self.assertTrue(self.light.is_on())

    def testStr_noParam_returnsNonEmptyString(self):
        zone = Zone('ff', [self.light, self.motionSensor, self.astroSensor,
                           self.illuminanceSensor, self.dimmer, self.fan])
        info = str(zone)

        self.assertTrue(len(info) > 0)

    def testGetNeighborZones_noZoneManager_throwsException(self):
        zone1 = Zone('ff')
        with self.assertRaises(ValueError) as cm:
            zone1.get_neighbor_zones(None)

        self.assertEqual('zoneManager must not be None', cm.exception.args[0])

    def testGetNeighborZones_noNeighborTypesSpecified_returnsCorrectList(self):
        zone1 = Zone('foyer')
        zone2 = Zone('porch')
        zone3 = Zone('office')

        zone1 = zone1.add_neighbor(Neighbor(zone2.get_id(), NeighborType.OPEN_SPACE))
        zone1 = zone1.add_neighbor(Neighbor(zone3.get_id(), NeighborType.OPEN_SPACE_MASTER))
        zm = create_zone_manager([zone1, zone2, zone3])

        self.assertEqual(2, len(zone1.get_neighbor_zones(zm)))

    def testGetNeighborZones_neighborTypeSpecified_returnsCorrectList(self):
        zone1 = Zone('foyer')
        zone2 = Zone('porch')
        zone3 = Zone('office')

        zone1 = zone1.add_neighbor(Neighbor(zone2.get_id(), NeighborType.OPEN_SPACE))
        zone1 = zone1.add_neighbor(Neighbor(zone3.get_id(), NeighborType.OPEN_SPACE_MASTER))
        zm = create_zone_manager([zone1, zone2, zone3])

        zones = zone1.get_neighbor_zones(zm, [NeighborType.OPEN_SPACE_MASTER])
        self.assertEqual(1, len(zones))
        self.assertEqual(zone3, zones[0])

    def testZoneIdFromItemName_validPattern_returnsId(self):
        self.assertEqual('FF_Foyer', Zone.get_zone_id_from_item_name('FF_Foyer_Door'))
        self.assertEqual('SF_Bedroom1', Zone.get_zone_id_from_item_name('SF_Bedroom1_Light_Main'))

    def testZoneIdFromItemName_invalidPattern_returnsNone(self):
        self.assertEqual(None, Zone.get_zone_id_from_item_name('FFFoyer_Door'))
        self.assertEqual(None, Zone.get_zone_id_from_item_name('FFFoyerDoor'))
