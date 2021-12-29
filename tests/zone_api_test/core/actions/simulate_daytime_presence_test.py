import time

from zone_api import platform_encapsulator as pe
from zone_api.core.devices.motion_sensor import MotionSensor

from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone, Level
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.activity_times import ActivityTimes, ActivityType
from zone_api_test.core.device_test import DeviceTest, create_zone_manager
from zone_api.core.actions.simulate_daytime_presence import SimulateDaytimePresence


class SimulateDaytimePresenceTest(DeviceTest):
    """ Unit tests for simulate_daytime_presence.py. """

    def setUp(self):
        self.audioSink, sink_items = self.create_audio_sink()
        self.partition, partition_items = self.create_alarm_partition()

        items = sink_items + partition_items + [pe.create_switch_item('_testMotion')]
        self.set_items(items)
        super(SimulateDaytimePresenceTest, self).setUp()

        self.motion_sensor = MotionSensor(items[-1])

        self.action = SimulateDaytimePresence("anUrl", 70, 0.1)

        self.partition.disarm(pe.get_event_dispatcher())
        self.audioSink._set_test_mode()

    def testOnAction_wrongEventType_returnsFalse(self):
        (porch, greatRoom, zm, _) = self.create_test_data()
        event_info = EventInfo(ZoneEvent.DOOR_OPEN, self.motion_sensor.get_item(),
                               porch, zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_motionEventOnInternalZone_returnsFalse(self):
        event_info = EventInfo(ZoneEvent.MOTION, self.motion_sensor.get_item(), Zone('porch'),
                               None, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_noAlarmPartition_returnsFalse(self):
        (porch, greatRoom, zm, event_info) = self.create_test_data([self.partition])

        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_noAudioSink_returnsFalse(self):
        (porch, greatRoom, zm, event_info) = self.create_test_data([self.audioSink])

        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_notInArmAwayMode_returnsFalse(self):
        (porch, greatRoom, zm, event_info) = self.create_test_data()
        self.partition.disarm(pe.get_event_dispatcher())

        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_sleepTime_returnsFalse(self):
        time_map = {ActivityType.SLEEP: '0:00 - 23:59'}
        (porch, greatRoom, zm, event_info) = self.create_test_data(
            [], [ActivityTimes(time_map)])

        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_allConditionSatisfied_playsMusicAndReturnsTrue(self):
        (porch, greatRoom, zm, event_info) = self.create_test_data()

        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual("playStream", self.audioSink._get_last_test_command())

        time.sleep(0.15)
        self.assertEqual("pause", self.audioSink._get_last_test_command())

    def testOnAction_multipleTriggering_renewPauseTimerAndReturnsTrue(self):
        (porch, greatRoom, zm, event_info) = self.create_test_data()

        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual("playStream", self.audioSink._get_last_test_command())

        time.sleep(0.15)
        self.assertEqual("pause", self.audioSink._get_last_test_command())

        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual("playStream", self.audioSink._get_last_test_command())

    def create_test_data(self, excluded_devices=None, extra_included_devices=None):
        """
        :return: a list of two zones, the mocked zone manager, and the event dispatcher
        :rtype: list
        """

        if extra_included_devices is None:
            extra_included_devices = []
        if excluded_devices is None:
            excluded_devices = []

        self.partition.arm_away(pe.get_event_dispatcher())

        porch = Zone.create_external_zone('porch').add_device(self.partition)\
            .add_device(self.motion_sensor) \
            .add_action(self.action)
        great_room = Zone("GR", [self.audioSink], Level.FIRST_FLOOR)

        for d in excluded_devices:
            if porch.has_device(d):
                porch = porch.remove_device(d)

            if great_room.has_device(d):
                great_room = great_room.remove_device(d)

        for d in extra_included_devices:
            great_room = great_room.add_device(d)

        zm = create_zone_manager([porch, great_room])

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_sensor.get_item(),
                               porch, zm, pe.get_event_dispatcher())

        return [porch, great_room, zm, event_info]
