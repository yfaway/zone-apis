from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.disarm_on_internal_motion import DisarmOnInternalMotion
from aaa_modules.layout_model.devices.activity_times import ActivityTimes, ActivityType
from aaa_modules.layout_model.devices.contact import Door

from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager


class DisarmOnInternalMotionTest(DeviceTest):
    """ Unit tests for DisarmInTheMorning. """

    def setUp(self):
        self.alarmPartition, items = self.create_alarm_partition()

        items = items + [pe.create_switch_item('InternalMotionSensor'), pe.create_switch_item('ExternalDoor')]
        self.set_items(items)

        super(DisarmOnInternalMotionTest, self).setUp()

        self.motionSensor = MotionSensor(items[-2])
        self.door = Door(items[-1])

        time_map = {
            ActivityType.WAKE_UP: '0:00 - 23:59',
        }
        self.activity_times = ActivityTimes(time_map)

        self.action = DisarmOnInternalMotion()
        self.zone1 = Zone('foyer', [self.motionSensor, self.alarmPartition, self.activity_times]) \
            .add_action(self.action)
        self.zone2 = Zone.create_external_zone('porch').add_device(self.door)

        self.mockZoneManager = create_zone_manager([self.zone1, self.zone2])

    def testOnAction_motionTriggeredInWakeupTimePeriod_disarm(self):
        self.assert_disarm(ActivityTimes({
            ActivityType.WAKE_UP: '0:00 - 23:59',}
        ))

    def testOnAction_motionTriggeredInWakeupTimePeriodOverlapWithSleepPeriod_disarm(self):
        self.assert_disarm(ActivityTimes({
            ActivityType.SLEEP: '0:00 - 23:59',
            ActivityType.WAKE_UP: '0:00 - 23:59',}
        ))

    def testOnAction_motionTriggeredInWakeupTimePeriodButExternalDoorWasJustOpened_NotDisarm(self):
        self.mockZoneManager.dispatch_event(ZoneEvent.DOOR_OPEN, pe.get_event_dispatcher(), self.door,
                                            self.door.get_item())

        self.assert_not_disarm(ActivityTimes({
            ActivityType.WAKE_UP: '0:00 - 23:59',}
        ))

    def testOnAction_motionTriggeredInSleepPeriod_NotDisarm(self):
        self.assert_not_disarm(ActivityTimes({ActivityType.SLEEP: '0:00 - 23:59'}))

    def testOnAction_motionTriggeredInAutoArmPeriod_NotDisarm(self):
        self.assert_not_disarm(ActivityTimes({ActivityType.AUTO_ARM_STAY: '0:00 - 23:59'}))

    def assert_not_disarm(self, activity_times):
        value = self.setup_and_invoke_action(activity_times)
        self.assertFalse(value)
        self.assertFalse(self.alarmPartition.is_unarmed())

    def assert_disarm(self, activity_times):
        value = self.setup_and_invoke_action(activity_times)
        self.assertTrue(value)
        self.assertTrue(self.alarmPartition.is_unarmed())

    def setup_and_invoke_action(self, activity_times):
        self.alarmPartition.arm_stay(pe.get_event_dispatcher())

        self.zone1 = Zone('foyer', [self.motionSensor, self.alarmPartition, activity_times]) \
            .add_action(self.action)
        self.mockZoneManager = create_zone_manager([self.zone1, self.zone2])

        event_info = EventInfo(ZoneEvent.MOTION, self.motionSensor.get_item(),
                               self.zone1, self.mockZoneManager, pe.get_event_dispatcher())
        return self.action.on_action(event_info)