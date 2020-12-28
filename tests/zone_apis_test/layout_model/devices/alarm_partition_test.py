from zone_apis_test.layout_model.device_test import DeviceTest

from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition, AlarmState
from aaa_modules import platform_encapsulator as pe


class AlarmPartitionTest(DeviceTest):
    """ Unit tests for alarm_partition.py. """

    def setUp(self):
        items = [pe.create_switch_item('_Plug'), pe.create_number_item('_Power')]
        self.set_items(items)
        super(AlarmPartitionTest, self).setUp()

        self.alarmPartition = AlarmPartition(self.get_items()[0], self.get_items()[1])
        pe.set_number_value(items[1], AlarmState.UNARMED.value)

    def testIsInAlarm_notInAlarm_returnsFalse(self):
        self.assertFalse(self.alarmPartition.is_in_alarm())

    def testIsInAlarm_inAlarm_returnsTrue(self):
        pe.set_switch_state(self.alarmPartition.getItem(), True)
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
