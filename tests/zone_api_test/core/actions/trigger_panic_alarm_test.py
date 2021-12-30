from unittest.mock import MagicMock

from zone_api import platform_encapsulator as pe
from zone_api.core.actions.trigger_panic_alarm import TriggerPanicAlarm
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
