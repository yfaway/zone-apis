from aaa_modules import platform_encapsulator as pe
from aaa_modules import security_manager as sm
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition, AlarmState
from aaa_modules.layout_model.zone import Zone

from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager


class SecurityManagerTest(DeviceTest):
    def setUp(self):
        items = [pe.create_switch_item('AlarmStatus'), pe.create_number_item('_AlarmMode')]
        self.set_items(items)
        super(SecurityManagerTest, self).setUp()

        self.alarmPartition = AlarmPartition(items[0], items[1])
        self.zone1 = Zone('foyer', [self.alarmPartition])

        self.mockZoneManager = create_zone_manager([self.zone1])

    def testIsArmedAway_noAlarmPartition_returnsFalse(self):
        self.mockZoneManager = create_zone_manager([Zone('foyer')])
        self.assertFalse(sm.is_armed_away(self.mockZoneManager))

    def testIsArmedAway_notArmedAway_returnsFalse(self):
        self.assertFalse(sm.is_armed_away(self.mockZoneManager))

    def testIsArmedAway_armedAway_returnsTrue(self):
        pe.set_number_value(self.get_items()[1], AlarmState.ARM_AWAY.value)
        self.assertTrue(sm.is_armed_away(self.mockZoneManager))

    def testIsArmedStayed_noAlarmPartition_returnsFalse(self):
        self.mockZoneManager = create_zone_manager([Zone('foyer')])
        self.assertFalse(sm.is_armed_stay(self.mockZoneManager))

    def testIsArmedStayed_notArmed_returnsFalse(self):
        self.assertFalse(sm.is_armed_stay(self.mockZoneManager))

    def testIsArmedStayed_armedStay_returnsTrue(self):
        pe.set_number_value(self.get_items()[1], AlarmState.ARM_STAY.value)
        self.assertTrue(sm.is_armed_stay(self.mockZoneManager))

