import unittest
from unittest.mock import MagicMock

from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Level
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import validate


class ActionTest(unittest.TestCase):
    """ Unit tests for action.py. """

    def testValidate_isFilteringDisabled_alwaysInvokeAction(self):
        action = self.create_action()
        action.is_filtering_disabled = MagicMock(return_value=True)
        self.assertTrue(validate(action.on_action)(action, MagicMock()))

    def testValidate_timerEvent_alwaysInvokeAction(self):
        action = self.create_action()
        event_info = MagicMock()
        event_info.get_event_type = MagicMock(return_value=ZoneEvent.TIMER)
        self.assertTrue(validate(action.on_action)(action, event_info))

    def testValidate_externalEventInList_invokeAction(self):
        action = self.create_action()
        action.get_external_events = MagicMock(return_value=[ZoneEvent.MOTION])
        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_external_event(ZoneEvent.MOTION)))

    def testValidate_externalEventNotInList_notInvokeAction(self):
        action = self.create_action()
        action.get_external_events = MagicMock(return_value=[])
        self.assertFalse(validate(action.on_action)(action, self.create_event_info_for_external_event()))

    def testValidate_eventNotInList_notInvokeAction(self):
        action = self.create_action()
        action.get_required_events = MagicMock(return_value=[ZoneEvent.WEATHER_ALERT_CHANGED])
        self.assertFalse(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(ZoneEvent.MOTION)))

    def testValidate_eventInList_invokeAction(self):
        action = self.create_action()
        action.get_required_events = MagicMock(return_value=[ZoneEvent.MOTION])
        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(ZoneEvent.MOTION)))

    def testValidate_noRequiredEvent_invokeAction(self):
        action = self.create_action()
        action.get_required_events = MagicMock(return_value=[])
        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(ZoneEvent.MOTION)))

    def testValidate_deviceNotInList_notInvokeAction(self):
        action = self.create_action()
        action.get_required_events = MagicMock(return_value=[ZoneEvent.MOTION])
        action.get_required_devices = MagicMock(return_value=[MotionSensor])
        self.assertFalse(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(ZoneEvent.MOTION)))

    def testValidate_deviceInList_invokeAction(self):
        action = self.create_action()
        action.get_required_events = MagicMock(return_value=[ZoneEvent.MOTION])
        action.get_required_devices = MagicMock(return_value=[MotionSensor])
        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(ZoneEvent.MOTION, MagicMock())))

    def testValidate_noRequiredDevice_invokeAction(self):
        action = self.create_action()
        action.get_required_devices = MagicMock(return_value=[])
        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(ZoneEvent.MOTION, MagicMock())))

    def testValidate_internalZoneOnActionForExternalZone_notInvokeAction(self):
        action = self.create_action()
        action.is_applicable_to_internal_zone = MagicMock(return_value=False)
        self.assertFalse(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(internal=True)))

    def testValidate_internalZoneOnActionForInternalZone_invokeAction(self):
        action = self.create_action()
        action.is_applicable_to_internal_zone = MagicMock(return_value=True)
        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(internal=True)))

    def testValidate_externalZoneOnActionForInternalZone_notInvokeAction(self):
        action = self.create_action()
        action.is_applicable_to_internal_zone = MagicMock(return_value=True)
        action.is_applicable_to_external_zone = MagicMock(return_value=False)
        self.assertFalse(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(internal=False)))

    def testValidate_externalZoneOnActionForExternalZone_invokeAction(self):
        action = self.create_action()
        action.is_applicable_to_external_zone = MagicMock(return_value=True)
        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(internal=False)))

    def testValidate_wrongLevel_notInvokeAction(self):
        action = self.create_action()
        action.get_applicable_levels = MagicMock(return_value=[Level.SECOND_FLOOR])
        self.assertFalse(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(level=Level.FIRST_FLOOR)))

    def testValidate_correctLevel_invokeAction(self):
        action = self.create_action()
        action.get_applicable_levels = MagicMock(return_value=[Level.FIRST_FLOOR])
        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(level=Level.FIRST_FLOOR)))

    def testValidate_zoneNameNotMatched_notInvokeAction(self):
        action = self.create_action()
        action.get_applicable_zone_name_pattern = MagicMock(return_value="Foy.*")

        self.assertFalse(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(name='Office')))

    def testValidate_actionNotSpecifyingZoneName_invokeAction(self):
        action = self.create_action()

        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(name='Office')))

    def testValidate_zoneNameMatched_invokeAction(self):
        action = self.create_action()
        action.get_applicable_zone_name_pattern = MagicMock(return_value="Foy.*")

        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(name='Foyer')))

    def testValidate_comprehensiveTestWithAllCriteriaMatched_invokeAction(self):
        action = self.create_action()
        action.get_required_events = MagicMock(return_value=[ZoneEvent.MOTION, ZoneEvent.DOOR_OPEN])
        action.get_required_devices = MagicMock(return_value=[MotionSensor])
        action.is_applicable_to_internal_zone = MagicMock(return_value=True)
        action.get_applicable_zone_name_pattern = MagicMock(return_value="Foy.*")
        action.get_applicable_levels = MagicMock(return_value=[Level.FIRST_FLOOR, Level.SECOND_FLOOR])

        self.assertTrue(validate(action.on_action)(
            action, self.create_event_info_for_internal_event(
                event=ZoneEvent.MOTION, device=MagicMock(), internal=True, level=Level.FIRST_FLOOR, name='Foyer')))

    @staticmethod
    def create_action():
        """ Creates a mocked action that enables filtering and having no specified zone name pattern. """
        action = MagicMock()
        action.on_action = MagicMock(return_value=True)
        action.is_filtering_disabled = MagicMock(return_value=False)
        action.get_applicable_zone_name_pattern = MagicMock(return_value=None)

        return action

    @staticmethod
    def create_event_info_for_internal_event(
            event: ZoneEvent = ZoneEvent.MOTION, device=None, internal=True, level=Level.FIRST_FLOOR, name='Kitchen') \
            -> EventInfo:
        """
        Create a mocked EventInfo object with the provided event, device, and zone attributes (internal/external,
        floor level, and name).
        """
        zone = MagicMock()
        zone.contains_open_hab_item = MagicMock(return_value=True)

        if device is None:
            zone.get_devices_by_type = MagicMock(return_value=[])
        else:
            zone.get_devices_by_type = MagicMock(return_value=[device])

        if internal:
            zone.is_internal = MagicMock(return_value=[True])
            zone.is_external = MagicMock(return_value=[False])
        else:
            zone.is_internal = MagicMock(return_value=[False])
            zone.is_external = MagicMock(return_value=[True])

        zone.get_level = MagicMock(return_value=level)
        zone.get_name = MagicMock(return_value=name)

        event_info = MagicMock()
        event_info.get_zone = MagicMock(return_value=zone)
        event_info.get_event_type = MagicMock(return_value=event)

        return event_info

    @staticmethod
    def create_event_info_for_external_event(event: ZoneEvent = ZoneEvent.MOTION) -> EventInfo:
        """ Create a mocked EventInfo object that represents an external event. """
        zone = MagicMock()
        zone.contains_open_hab_item = MagicMock(return_value=False)

        event_info = MagicMock()
        event_info.get_zone = MagicMock(return_value=zone)
        event_info.get_event_type = MagicMock(return_value=event)

        return event_info
