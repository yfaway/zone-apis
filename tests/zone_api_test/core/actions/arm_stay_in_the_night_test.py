from zone_api import platform_encapsulator as pe
from zone_api.core.actions.arm_stay_in_the_night import ArmStayInTheNight
from zone_api.core.devices.activity_times import ActivityTimes, ActivityType

from zone_api.core.event_info import EventInfo
from zone_api.core.map_parameters import MapParameters
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class ArmStayInTheNightTest(DeviceTest):
    """ Unit tests for ArmStayInTheNight. """

    def setUp(self):
        self.alarm_partition, items = self.create_alarm_partition()
        self.set_items(items)
        super(ArmStayInTheNightTest, self).setUp()

        self.alarm_partition.disarm(pe.get_event_dispatcher())

        time_map = {
            ActivityType.AUTO_ARM_STAY: '0:00 - 23:59',
        }
        self.activity_times = ActivityTimes(time_map)

        self.action = ArmStayInTheNight(MapParameters({}))
        self.zone1 = Zone('foyer', [self.alarm_partition, self.activity_times]) \
            .add_action(self.action)

        self.mockZoneManager = create_zone_manager([self.zone1])

    def testOnAction_timerTriggeredInRightPeriod_armStay(self):
        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.alarm_partition.is_armed_stay())

    def testOnAction_motionTriggeredNotInWakeupTimePeriod_disarm(self):
        self.activity_times = ActivityTimes({ActivityType.AUTO_ARM_STAY: self.create_outside_time_range()})
        self.zone1 = Zone('foyer', [self.alarm_partition, self.activity_times]) \
            .add_action(self.action)
        self.mockZoneManager = create_zone_manager([self.zone1])

        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)
        self.assertTrue(self.alarm_partition.is_unarmed())
