
from typing import Union
from unittest.mock import MagicMock, patch
from tests.zone_api_test.core.device_test import DeviceTest, create_zone_manager
from zone_api import platform_encapsulator as pe
from zone_api.core.actions.track_significant_events import TrackSignificantEvents
from zone_api.core.device import Device
from zone_api.core.devices.contact import Door, Window
from zone_api.core.event_info import EventInfo
from zone_api.core.map_parameters import MapParameters
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent


class TrackSignificantEventsTest(DeviceTest):
    """ Unit tests for track_significant_event.py """

    def setUp(self):
        self.alarmPartition, _ = self.create_alarm_partition()

        self.internal_door = Door(contact_item=pe.create_contact_item('Door1'))
        self.external_door = Door(contact_item=pe.create_contact_item('Door2'))
        self.window = Window(contact_item=pe.create_contact_item('window'))

        items =  self.alarmPartition.get_all_items() + [
            self.internal_door.get_item(), self.external_door.get_item(), self.window.get_item(),
            pe.create_string_item(TrackSignificantEvents.DEFAULT_OUTPUT_ITEM_NAME)]
        self.set_items(items)

        super(TrackSignificantEventsTest, self).setUp()

        self.action: TrackSignificantEvents = TrackSignificantEvents(MapParameters({}))
        self.zone1 = Zone('Virtual', [self.alarmPartition]) \
            .add_action(self.action)

        self.zone2 = Zone('kitchen', [self.internal_door, self.window])
        self.external_zone = Zone.create_external_zone("Porch").add_device(self.external_door)

    def tearDown(self):
        super(TrackSignificantEventsTest, self).tearDown()

    def testOnAction_eventTriggered_outputJson(self):
        pe.set_string_value(TrackSignificantEvents.DEFAULT_OUTPUT_ITEM_NAME, '')
        self.invoke(ZoneEvent.PARTITION_ARMED_AWAY, self.alarmPartition)

        self.assertTrue(pe.get_string_value(TrackSignificantEvents.DEFAULT_OUTPUT_ITEM_NAME) != '')

    def testOnAction_armedAway_recorded(self):
        self.invoke(ZoneEvent.PARTITION_ARMED_AWAY, self.alarmPartition)
        self.assert_top_event(ZoneEvent.PARTITION_ARMED_AWAY, "armed away")

    def testOnAction_armedStay_recorded(self):
        self.invoke(ZoneEvent.PARTITION_ARMED_STAY, self.alarmPartition)
        self.assert_top_event(ZoneEvent.PARTITION_ARMED_STAY, "armed stay")

    def testOnAction_disarmFromAway_recorded(self):
        self.invoke(ZoneEvent.PARTITION_DISARMED_FROM_AWAY, self.alarmPartition)
        self.assert_top_event(ZoneEvent.PARTITION_DISARMED_FROM_AWAY, "disarmed from away")

    def testOnAction_disarmFromStay_recorded(self):
        self.invoke(ZoneEvent.PARTITION_DISARMED_FROM_STAY, self.alarmPartition)
        self.assert_top_event(ZoneEvent.PARTITION_DISARMED_FROM_STAY, "disarmed from stay")

    def testOnAction_alarmTriggered_recorded(self):
        self.alarmPartition.is_in_alarm = MagicMock(return_value=True)

        self.invoke(ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED, self.alarmPartition)
        self.assert_top_event(ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED, "on alarm")

    def testOnAction_alarmCleared_recorded(self):
        self.alarmPartition.is_in_alarm = MagicMock(return_value=False)

        self.invoke(ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED, self.alarmPartition)
        self.assert_top_event(ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED, "alarm cleared")

    def testOnAction_windowsOpened_recorded(self):
        self.invoke(ZoneEvent.WINDOW_OPEN, self.window, receiving_zone=self.zone2)
        self.assert_top_event(ZoneEvent.WINDOW_OPEN, "Window opened")

    def testOnAction_windowsClosed_recorded(self):
        self.invoke(ZoneEvent.WINDOW_CLOSED, self.window, receiving_zone=self.zone2)
        self.assert_top_event(ZoneEvent.WINDOW_CLOSED, "Window closed")

    def testOnAction_doorOpened_recorded(self):
        self.invoke(ZoneEvent.DOOR_OPEN, self.external_door, self.external_zone)
        self.assert_top_event(ZoneEvent.DOOR_OPEN, "Door opened")

    def testOnAction_doorClosed_recorded(self):
        self.invoke(ZoneEvent.DOOR_CLOSED, self.external_door, self.external_zone)
        self.assert_top_event(ZoneEvent.DOOR_CLOSED, "Door closed")

    def testOnAction_doorOpenedInInternalZone_notRecorded(self):
        return_value = self.invoke(ZoneEvent.DOOR_OPEN, self.internal_door, self.zone2)
        self.assertFalse(return_value)

    def testOnAction_doorClosedInInternalZone_notRecorded(self):
        return_value = self.invoke(ZoneEvent.DOOR_CLOSED, self.internal_door, self.zone2)
        self.assertFalse(return_value)


    def invoke(self, zone_event: ZoneEvent, device: Union[Device, None]=None, receiving_zone=None):
        """ Invoke the action with the provide params and return the events. """

        if receiving_zone is None:
            receiving_zone = self.zone1
        
        item = device.get_item() if device is not None else None
        event_info = EventInfo(zone_event, item,
                               receiving_zone,
                               create_zone_manager([self.zone1, self.zone2, self.external_zone]),
                               pe.get_event_dispatcher(), receiving_zone, device) # type: ignore

        return self.action.on_action(event_info)

    def assert_top_event(self, zone_event:ZoneEvent, message: str):
        events = self.action._events

        self.assertTrue(len(events) > 0)
        self.assertEqual(events[0]['event_type'], zone_event.value)
        self.assertTrue(message in events[0]['message'])