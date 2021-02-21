from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.arm_stay_if_no_movement import ArmStayIfNoMovement
from aaa_modules.layout_model.devices.activity_times import ActivityTimes, ActivityType
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor

from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager


class ArmStayIfNoMovementTest(DeviceTest):
    """ Unit tests for ArmStayIfNoMovement. """

    def setUp(self):
        self.alarmPartition, items = self.create_alarm_partition()

        items = items + [pe.create_switch_item('InternalMotionSensor')]
        self.set_items(items)
        super(ArmStayIfNoMovementTest, self).setUp()

        self.alarmPartition = AlarmPartition(items[0], items[1])
        self.alarmPartition.disarm(pe.get_event_dispatcher())

        self.motionSensor = MotionSensor(items[2])

        self.activity_times = ActivityTimes({ActivityType.AUTO_ARM_STAY: self.create_outside_time_range()})

        self.action = ArmStayIfNoMovement(0.1)
        self.zone1 = Zone('foyer', [self.alarmPartition, self.activity_times, self.motionSensor]) \
            .add_action(self.action)

        self.mockZoneManager = create_zone_manager([self.zone1])

    def testOnAction_timerTriggeredWithNoOccupancy_armStay(self):
        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.alarmPartition.is_armed_stay())

    def testOnAction_withOccupancy_notArmStay(self):
        self.motionSensor._update_last_activated_timestamp()

        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)
        self.assertTrue(self.alarmPartition.is_unarmed())

    def testOnAction_armedAway_notArmStay(self):
        self.alarmPartition.arm_away(pe.get_event_dispatcher())

        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)
        self.assertTrue(self.alarmPartition.is_armed_away())

    def testOnAction_withOccupancyInAutoArmStayTimePeriod_notArmStay(self):
        self.motionSensor._update_last_activated_timestamp()

        self.activity_times = ActivityTimes({ActivityType.AUTO_ARM_STAY: '0:00 - 23:59'})
        self.zone1 = Zone('foyer', [self.alarmPartition, self.activity_times, self.motionSensor]) \
            .add_action(self.action)
        self.mockZoneManager = create_zone_manager([self.zone1])

        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)
        self.assertTrue(self.alarmPartition.is_unarmed())
