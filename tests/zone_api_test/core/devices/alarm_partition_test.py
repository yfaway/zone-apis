from zone_api_test.core.device_test import DeviceTest

from zone_api.core.devices.alarm_partition import AlarmPartition, AlarmState
from zone_api import platform_encapsulator as pe


class AlarmPartitionTest(DeviceTest):
    """ Unit tests for alarm_partition.py. """

    def setUp(self):
        self.alarmPartition, items = self.create_alarm_partition()
        self.set_items(items)
        super(AlarmPartitionTest, self).setUp()

        pe.set_number_value(items[1], AlarmState.UNARMED.value)

    def testIsInAlarm_notInAlarm_returnsFalse(self):
        self.assertFalse(self.alarmPartition.is_in_alarm())

    def testIsInAlarm_inAlarm_returnsTrue(self):
        pe.set_switch_state(self.alarmPartition.get_item(), True)
        self.assertTrue(self.alarmPartition.is_in_alarm())

    def testArmAway_noParam_setCorrectValue(self):
        self.alarmPartition.arm_away(pe.get_event_dispatcher())

        self.assertEqual(AlarmState.ARM_AWAY,
                         self.alarmPartition.get_arm_mode())

    def testArmStay_noParam_setCorrectValue(self):
        self.alarmPartition.arm_stay(pe.get_event_dispatcher())

        self.assertEqual(AlarmState.ARM_STAY,
                         self.alarmPartition.get_arm_mode())

    def testDisarm_noParam_setCorrectValue(self):
        self.alarmPartition.disarm(pe.get_event_dispatcher())

        self.assertEqual(AlarmState.UNARMED,
                         self.alarmPartition.get_arm_mode())
