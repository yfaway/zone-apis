from unittest.mock import MagicMock

from zone_api import platform_encapsulator as pe
from zone_api.core.actions.trigger_panic_alarm import TriggerPanicAlarm
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.ikea_remote_control import IkeaRemoteControl
from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone, Level
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class TriggerPanicAlarmTest(DeviceTest):
    """ Unit tests for TriggerPanicAlarm. """

    def setUp(self):
        self.alarm_partition, items = self.create_alarm_partition()
        self.set_items(items)
        super(TriggerPanicAlarmTest, self).setUp()

        self.action = TriggerPanicAlarm()
        self.zone1 = Zone('foyer', [], Level.FIRST_FLOOR) \
            .add_action(self.action) \
            .add_device(self.alarm_partition)

        # Set up the mock to avoid having to create the IkeaRemoteControl object. Without the mock, the action won't
        # be triggered dues to filtering effect.
        def mock_get_devices_by_type(*args, **kwargs):
            if args[0] == IkeaRemoteControl:
                return [True]
            elif args[0] == AlarmPartition:
                return [self.alarm_partition]

            return None
        self.zone1.contains_open_hab_item = MagicMock(side_effect=lambda x: True)
        self.zone1.get_devices_by_type = MagicMock(side_effect=mock_get_devices_by_type)

        self.motion_sensor_item = pe.create_switch_item("blah")

        self.zm = create_zone_manager([self.zone1])

        self.alarm_partition.trigger_fire_alarm = MagicMock()
        self.alarm_partition.cancel_panic_alarm = MagicMock()

    def testOnAction_fireAlarm_returnsTrueAndTriggerAlarm(self):
        self.sendEvent(ZoneEvent.MANUALLY_TRIGGER_FIRE_ALARM)
        self.alarm_partition.trigger_fire_alarm.assert_called()

    def testOnAction_cancelPanicAlarmInDisarmState_returnsTrueAndCancelAlarm(self):
        self.testOnAction_fireAlarm_returnsTrueAndTriggerAlarm()

        self.sendEvent(ZoneEvent.CANCEL_PANIC_ALARM)
        self.alarm_partition.cancel_panic_alarm.assert_called()
        self.assertTrue(self.alarm_partition.is_unarmed())

    def testOnAction_cancelPanicAlarmInArmStayState_returnsTrueAndCancelAlarm(self):
        self.alarm_partition.arm_stay(pe.get_event_dispatcher())
        self.testOnAction_fireAlarm_returnsTrueAndTriggerAlarm()

        self.sendEvent(ZoneEvent.CANCEL_PANIC_ALARM)
        self.alarm_partition.cancel_panic_alarm.assert_called()
        self.assertTrue(self.alarm_partition.is_armed_stay())

    def testOnAction_cancelPanicAlarmInArmAwayState_returnsTrueAndCancelAlarm(self):
        self.alarm_partition.arm_away(pe.get_event_dispatcher())
        self.testOnAction_fireAlarm_returnsTrueAndTriggerAlarm()

        self.sendEvent(ZoneEvent.CANCEL_PANIC_ALARM)
        self.alarm_partition.cancel_panic_alarm.assert_called()
        self.assertTrue(self.alarm_partition.is_armed_away())

    def sendEvent(self, event):
        event_info = EventInfo(event, self.motion_sensor_item, self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
