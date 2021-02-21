from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.arm_stay_in_the_night import ArmStayInTheNight
from aaa_modules.layout_model.devices.activity_times import ActivityTimes, ActivityType

from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager


class ArmStayInTheNightTest(DeviceTest):
    """ Unit tests for ArmStayInTheNight. """

    def setUp(self):
        items = [pe.create_switch_item('AlarmStatus'), pe.create_number_item('_AlarmMode')]
        self.set_items(items)
        super(ArmStayInTheNightTest, self).setUp()

        self.alarmPartition = AlarmPartition(items[0], items[1])
        self.alarmPartition.disarm(pe.get_event_dispatcher())

        time_map = {
            ActivityType.AUTO_ARM_STAY: '0:00 - 23:59',
        }
        self.activity_times = ActivityTimes(time_map)

        self.action = ArmStayInTheNight()
        self.zone1 = Zone('foyer', [self.alarmPartition, self.activity_times]) \
            .add_action(self.action)

        self.mockZoneManager = create_zone_manager([self.zone1])

    def testOnAction_timerTriggeredInRightPeriod_armStay(self):
        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.alarmPartition.is_armed_stay())

    def testOnAction_motionTriggeredNotInWakeupTimePeriod_disarm(self):
        self.activity_times = ActivityTimes({ActivityType.AUTO_ARM_STAY: self.create_outside_time_range()})
        self.zone1 = Zone('foyer', [self.alarmPartition, self.activity_times]) \
            .add_action(self.action)
        self.mockZoneManager = create_zone_manager([self.zone1])

        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)
        self.assertTrue(self.alarmPartition.is_unarmed())
