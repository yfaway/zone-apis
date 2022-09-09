import unittest
from unittest.mock import MagicMock, PropertyMock

from zone_api.core.devices.activity_times import ActivityType, ActivityTimes
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.event_info import EventInfo
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.parameters import Parameters
from zone_api.core.zone import Level
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import validate, action, Action


class ActionTest(unittest.TestCase):
    """ Unit tests for action.py. """

    def testValidate_isFilteringDisabled_alwaysInvokeAction(self):
        test_action = self.create_action()
        test_action.is_filtering_disabled = MagicMock(return_value=True)
        self.assertTrue(validate(test_action.on_action)(test_action, MagicMock()))

    def testValidate_timerEvent_alwaysInvokeAction(self):
        test_action = self.create_action()
        event_info = MagicMock()
        type(event_info).event_type = PropertyMock(return_value=ZoneEvent.TIMER)
        self.assertTrue(validate(test_action.on_action)(test_action, event_info))

    def testValidate_externalEventInList_invokeAction(self):
        test_action = self.create_action()
        type(test_action).external_events = PropertyMock(return_value=[ZoneEvent.MOTION])
        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_external_event(ZoneEvent.MOTION)))

    def testValidate_externalEventNotInList_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).external_events = PropertyMock(return_value=[])
        self.assertFalse(validate(test_action.on_action)(test_action, self.create_event_info_for_external_event()))

    def testValidate_eventNotInList_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).required_events = PropertyMock(return_value=[ZoneEvent.WEATHER_ALERT_CHANGED])
        self.assertFalse(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(ZoneEvent.MOTION)))

    def testValidate_eventInList_invokeAction(self):
        test_action = self.create_action()
        type(test_action).required_events = PropertyMock(return_value=[ZoneEvent.MOTION])
        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(ZoneEvent.MOTION)))

    def testValidate_noRequiredEvent_invokeAction(self):
        test_action = self.create_action()
        type(test_action).required_events = PropertyMock(return_value=[])
        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(ZoneEvent.MOTION)))

    def testValidate_deviceNotInList_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).required_events = PropertyMock(return_value=[ZoneEvent.MOTION])
        type(test_action).required_devices = PropertyMock(return_value=[MotionSensor])
        self.assertFalse(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(ZoneEvent.MOTION)))

    def testValidate_deviceInList_invokeAction(self):
        test_action = self.create_action()
        test_action.get_required_events = MagicMock(return_value=[ZoneEvent.MOTION])
        test_action.get_required_devices = MagicMock(return_value=[MotionSensor])
        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(ZoneEvent.MOTION, MagicMock())))

    def testValidate_noRequiredDevice_invokeAction(self):
        test_action = self.create_action()
        test_action.get_required_devices = MagicMock(return_value=[])
        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(ZoneEvent.MOTION, MagicMock())))

    def testValidate_internalZoneOnActionForExternalZone_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).applicable_to_internal_zone = PropertyMock(return_value=False)
        self.assertFalse(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(internal=True)))

    def testValidate_internalZoneOnActionForInternalZone_invokeAction(self):
        test_action = self.create_action()
        type(test_action).applicable_to_internal_zone = PropertyMock(return_value=True)
        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(internal=True)))

    def testValidate_externalZoneOnActionForInternalZone_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).applicable_to_internal_zone = PropertyMock(return_value=True)
        type(test_action).applicable_to_external_zone = PropertyMock(return_value=False)
        self.assertFalse(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(internal=False)))

    def testValidate_externalZoneOnActionForExternalZone_invokeAction(self):
        test_action = self.create_action()
        type(test_action).applicable_to_external_zone = PropertyMock(return_value=True)
        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(internal=False)))

    def testValidate_wrongLevel_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).applicable_levels = PropertyMock(return_value=[Level.SECOND_FLOOR])
        self.assertFalse(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(level=Level.FIRST_FLOOR)))

    def testValidate_correctLevel_invokeAction(self):
        test_action = self.create_action()
        type(test_action).applicable_levels = PropertyMock(return_value=[Level.FIRST_FLOOR])
        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(level=Level.FIRST_FLOOR)))

    def testValidate_zoneNameNotMatched_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).applicable_zone_name_pattern = PropertyMock(return_value="Foy.*")

        self.assertFalse(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(name='Office')))

    def testValidate_actionNotSpecifyingZoneName_invokeAction(self):
        test_action = self.create_action()

        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(name='Office')))

    def testValidate_zoneNameMatched_invokeAction(self):
        test_action = self.create_action()
        type(test_action).applicable_zone_name_pattern = PropertyMock(return_value="Foy.*")

        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(name='Foyer')))

    def testValidate_actionDefineActivityTypeButSystemNotConfigured_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).activity_types = PropertyMock(return_value=[ActivityType.QUIET])

        zm: ImmutableZoneManager = MagicMock()
        zm.get_first_device_by_type = MagicMock(return_value=None)
        event_info: EventInfo = self.create_event_info_for_internal_event(name='Foyer')
        event_info.get_zone_manager = MagicMock(return_value=zm)

        self.assertFalse(validate(test_action.on_action)(test_action, event_info))

    def testValidate_actionDefineExcludedActivityTypeButSystemNotConfigured_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).excluded_activity_types = PropertyMock(return_value=[ActivityType.QUIET])

        zm: ImmutableZoneManager = MagicMock()
        zm.get_first_device_by_type = MagicMock(return_value=None)
        event_info: EventInfo = self.create_event_info_for_internal_event(name='Foyer')
        event_info.get_zone_manager = MagicMock(return_value=zm)

        self.assertFalse(validate(test_action.on_action)(test_action, event_info))

    def testValidate_inActivityTypes_invokeAction(self):
        test_action = self.create_action()
        type(test_action).activity_types = PropertyMock(return_value=[ActivityType.QUIET])

        activities = ActivityTimes({})
        activities.is_quiet_time = MagicMock(return_value=True)

        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_with_activities(activities)))

    def testValidate_notInActivityTypes_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).activity_types = PropertyMock(return_value=[ActivityType.QUIET])

        activities = ActivityTimes({})
        activities.is_quiet_time = MagicMock(return_value=False)

        self.assertFalse(validate(test_action.on_action)(
            test_action, self.create_event_info_with_activities(activities)))

    def testValidate_inExcludedActivityTypes_notInvokeAction(self):
        test_action = self.create_action()
        type(test_action).excluded_activity_types = PropertyMock(return_value=[ActivityType.QUIET])

        activities = ActivityTimes({})
        activities.is_quiet_time = MagicMock(return_value=True)

        self.assertFalse(validate(test_action.on_action)(
            test_action, self.create_event_info_with_activities(activities)))

    def testValidate_notInExcludedActivityTypes_invokeAction(self):
        test_action = self.create_action()
        type(test_action).excluded_activity_types = PropertyMock(return_value=[ActivityType.QUIET])

        activities = ActivityTimes({})
        activities.is_quiet_time = MagicMock(return_value=False)

        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_with_activities(activities)))

    def testValidate_comprehensiveTestWithAllCriteriaMatched_invokeAction(self):
        test_action = self.create_action()
        type(test_action).required_events = PropertyMock(return_value=[ZoneEvent.MOTION, ZoneEvent.DOOR_OPEN])
        type(test_action).required_devices = PropertyMock(return_value=[MotionSensor])
        type(test_action).applicable_to_internal_zone = PropertyMock(return_value=True)
        type(test_action).applicable_zone_name_pattern = PropertyMock(return_value="Foy.*")
        type(test_action).applicable_levels = PropertyMock(return_value=[Level.FIRST_FLOOR, Level.SECOND_FLOOR])

        self.assertTrue(validate(test_action.on_action)(
            test_action, self.create_event_info_for_internal_event(
                event=ZoneEvent.MOTION, device=MagicMock(), internal=True, level=Level.FIRST_FLOOR, name='Foyer')))

    def testDecorator_defaultSettings_returnsActionWithCorrectAttribute(self):
        @action()
        class TestAction(Action):
            def __init__(self):
                super().__init__(Parameters())

            def on_action(self):
                pass

        self.assertTrue(TestAction().applicable_to_internal_zone)
        self.assertFalse(TestAction().applicable_to_external_zone)
        self.assertEqual(TestAction().required_events, [])
        self.assertEqual(TestAction().external_events, [])
        self.assertEqual(TestAction().required_events, [])
        self.assertEqual(TestAction().applicable_levels, [])
        self.assertEqual(TestAction().applicable_zone_name_pattern, None)
        self.assertFalse(TestAction().must_be_unique_instance)
        self.assertEqual(TestAction().priority, 10)

    def testDecorator_events_returnsActionWithCorrectAttribute(self):
        @action(events=[ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED, ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED])
        class TestAction:
            def on_action(self):
                pass

        self.assertEqual(TestAction().required_events,
                         [ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED, ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED])

    def testDecorator_externalEvents_returnsActionWithCorrectAttribute(self):
        @action(external_events=[ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED])
        class TestAction:
            def on_action(self):
                pass

        self.assertEqual(TestAction().external_events, [ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED])
        self.assertEqual(TestAction().required_events, [])

    def testDecorator_devices_returnsActionWithCorrectAttribute(self):
        @action(devices=[MotionSensor])
        class TestAction:
            def on_action(self):
                pass

        self.assertEqual(TestAction().required_devices, [MotionSensor])

    def testDecorator_internal_returnsActionWithCorrectAttribute(self):
        @action(internal=True)
        class TestAction:
            def on_action(self):
                pass

        self.assertTrue(TestAction().applicable_to_internal_zone)
        self.assertFalse(TestAction().applicable_to_external_zone)

    def testDecorator_external_returnsActionWithCorrectAttribute(self):
        @action(internal=False, external=True)
        class TestAction:
            def on_action(self):
                pass

        self.assertFalse(TestAction().applicable_to_internal_zone)
        self.assertTrue(TestAction().applicable_to_external_zone)

    def testDecorator_levels_returnsActionWithCorrectAttribute(self):
        @action(levels=[Level.FIRST_FLOOR, Level.SECOND_FLOOR])
        class TestAction:
            def on_action(self):
                pass

        self.assertEqual(TestAction().applicable_levels, [Level.FIRST_FLOOR, Level.SECOND_FLOOR])

    def testDecorator_uniqueInstance_returnsActionWithCorrectAttribute(self):
        @action(unique_instance=True)
        class TestAction:
            def on_action(self):
                pass

        self.assertTrue(TestAction().must_be_unique_instance)

    def testDecorator_zoneNamePattern_returnsActionWithCorrectAttribute(self):
        @action(zone_name_pattern="aName")
        class TestAction:
            def on_action(self):
                pass

        self.assertEqual(TestAction().applicable_zone_name_pattern, "aName")

    def testDecorator_priority_returnsActionWithCorrectAttribute(self):
        @action(priority=100)
        class TestAction:
            def on_action(self):
                pass

        self.assertEqual(TestAction().priority, 100)

    @staticmethod
    def create_action():
        """ Creates a mocked action that enables filtering and having no specified zone name pattern. """
        test_action = MagicMock()
        test_action.on_action = MagicMock(return_value=True)
        type(test_action).filtering_disabled = PropertyMock(return_value=False)
        type(test_action).applicable_zone_name_pattern = PropertyMock(return_value=None)

        return test_action

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

    @staticmethod
    def create_event_info_with_activities(activities: ActivityTimes) -> EventInfo:
        """ Create an event info with a mocked zone manager that return 'activities' when
        method get_first_device_by_type is invoked. """
        zm: ImmutableZoneManager = MagicMock()
        zm.get_first_device_by_type = MagicMock(return_value=activities)
        event_info: EventInfo = ActionTest.create_event_info_for_internal_event(name='Foyer')
        event_info.get_zone_manager = MagicMock(return_value=zm)

        return event_info
