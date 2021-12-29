from zone_api import platform_encapsulator as pe
from zone_api import security_manager as sm
from zone_api.core.devices.alarm_partition import AlarmState
from zone_api.core.zone import Zone

from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class SecurityManagerTest(DeviceTest):
    def setUp(self):
        self.alarmPartition, items = self.create_alarm_partition()
        self.set_items(items)
        super(SecurityManagerTest, self).setUp()

        self.zone1 = Zone('foyer', [self.alarmPartition])

        self.mockZoneManager = create_zone_manager([self.zone1])

    def testIsArmedAway_noAlarmPartition_returnsFalse(self):
        self.mockZoneManager = create_zone_manager([Zone('foyer')])
        self.assertFalse(sm.is_armed_away(self.mockZoneManager))

    def testIsArmedAway_notArmedAway_returnsFalse(self):
        self.assertFalse(sm.is_armed_away(self.mockZoneManager))

    def testIsArmedAway_armedAway_returnsTrue(self):
        pe.set_number_value(self.alarmPartition.get_arm_mode_item(), AlarmState.ARM_AWAY.value)
        self.assertTrue(sm.is_armed_away(self.mockZoneManager))

    def testIsArmedStayed_noAlarmPartition_returnsFalse(self):
        self.mockZoneManager = create_zone_manager([Zone('foyer')])
        self.assertFalse(sm.is_armed_stay(self.mockZoneManager))

    def testIsArmedStayed_notArmed_returnsFalse(self):
        self.assertFalse(sm.is_armed_stay(self.mockZoneManager))

    def testIsArmedStayed_armedStay_returnsTrue(self):
        pe.set_number_value(self.alarmPartition.get_arm_mode_item(), AlarmState.ARM_STAY.value)
        self.assertTrue(sm.is_armed_stay(self.mockZoneManager))
