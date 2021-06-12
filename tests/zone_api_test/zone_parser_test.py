import unittest
from unittest.mock import MagicMock

from zone_api import zone_parser as zp
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.zone import Zone, Level


class ZoneParserTest(unittest.TestCase):
    def testCanAddActionToZone_forInternalZone_returnsTrue(self):
        zone = Zone("a zone")
        action = self._create_action_mock()
        action.is_applicable_to_internal_zone.return_value = True
        action.is_applicable_to_external_zone.return_value = False

        self.assertTrue(zp._can_add_action_to_zone(zone, action))

    def testCanAddActionToZone_markForInternalZoneButApplyOnExternalZone_returnsFalse(self):
        zone = Zone.create_external_zone("blah")
        action = self._create_action_mock()
        action.is_applicable_to_internal_zone.return_value = True
        action.is_applicable_to_external_zone.return_value = False

        self.assertFalse(zp._can_add_action_to_zone(zone, action))

    def testCanAddActionToZone_markForExternalZone_returnsTrue(self):
        zone = Zone.create_external_zone("blah")
        action = self._create_action_mock()
        action.is_applicable_to_internal_zone.return_value = False
        action.is_applicable_to_external_zone.return_value = True

        self.assertTrue(zp._can_add_action_to_zone(zone, action))

    def testCanAddActionToZone_markForExternalZoneButApplyOnInternalZone_returnsFalse(self):
        zone = Zone("blah")
        action = self._create_action_mock()
        action.is_applicable_to_internal_zone.return_value = False
        action.is_applicable_to_external_zone.return_value = True

        self.assertFalse(zp._can_add_action_to_zone(zone, action))

    def testCanAddActionToZone_zoneContainsRequiredDevice_returnsTrue(self):
        zone = Zone("blah")
        zone.get_devices_by_type = MagicMock()
        zone.get_devices_by_type.return_value = [MagicMock()]

        action = self._create_action_mock()
        action.get_required_devices.return_value = [MotionSensor]

        self.assertTrue(zp._can_add_action_to_zone(zone, action))

    def testCanAddActionToZone_zoneNotContainRequiredDevice_returnsFalse(self):
        zone = Zone("blah")
        zone.get_devices_by_type = MagicMock()
        zone.get_devices_by_type.return_value = []

        action = self._create_action_mock()
        action.get_required_devices.return_value = [MotionSensor]

        self.assertFalse(zp._can_add_action_to_zone(zone, action))

    def testCanAddActionToZone_levelsMatch_returnsTrue(self):
        zone = Zone("blah", [], Level.THIRD_FLOOR)

        action = self._create_action_mock()
        action.get_applicable_levels.return_value = [Level.THIRD_FLOOR]

        self.assertTrue(zp._can_add_action_to_zone(zone, action))

    def testCanAddActionToZone_levelsNotMatch_returnsFalse(self):
        zone = Zone("blah", [], Level.THIRD_FLOOR)

        action = self._create_action_mock()
        action.get_applicable_levels.return_value = [Level.FIRST_FLOOR]

        self.assertFalse(zp._can_add_action_to_zone(zone, action))

    def testCanAddActionToZone_zoneContainsCorrectNamePattern_returnsTrue(self):
        zone = Zone("Virtual")
        action = self._create_action_mock()
        action.get_applicable_zone_name_pattern.return_value = '.*Virtual.*'

        self.assertTrue(zp._can_add_action_to_zone(zone, action))

    def testCanAddActionToZone_zoneNotContainCorrectNamePattern_returnsFalse(self):
        zone = Zone("Blah")
        action = self._create_action_mock()
        action.get_applicable_zone_name_pattern.return_value = '.*Virtual.*'

        self.assertFalse(zp._can_add_action_to_zone(zone, action))

    # noinspection PyMethodMayBeStatic
    def _create_action_mock(self):
        action = MagicMock()
        action.get_applicable_zone_name_pattern.return_value = None

        return action

    def testGetActionClasses_defaultParams_returnsNonEmptyTypes(self):
        types = zp.get_action_classes()
        self.assertTrue(len(types) > 0)

    def testGetActionClasses_validParameters_returnsNonEmptyTypes(self):
        import zone_api.core.actions as actions
        types = zp.get_action_classes("zone_api.core.actions", actions.__path__)
        self.assertTrue(len(types) > 0)

    def testGetActionClasses_invalidPackage_throwsModuleNotFoundError(self):
        import zone_api.core.actions as actions
        self.assertRaises(ModuleNotFoundError, zp.get_action_classes, "bad.package", actions.__path__)

    def testGetActionClasses_invalidPaths_returnsEmptyTypes(self):
        types = zp.get_action_classes("zone_api.core.actions", ["an invalid path"])
        self.assertEqual(0, len(types))
