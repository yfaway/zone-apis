import time

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.play_music_at_dinner_time import PlayMusicAtDinnerTime
from aaa_modules.layout_model.devices.activity_times import ActivityTimes
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor

from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.neighbor import Neighbor, NeighborType
from aaa_modules.layout_model.zone import Zone, ZoneEvent


class PlayMusicAtDinnerTimeTest(DeviceTest):
    """ Unit tests for play_music_at_dinner_time.py. """

    def setUp(self):
        self.sink, items = self.create_audio_sink()

        items.append(pe.create_switch_item('MotionSensor'))
        self.motion_item = items[-1]

        self.set_items(items)
        super(PlayMusicAtDinnerTimeTest, self).setUp()

        self.motion = MotionSensor(self.motion_item)

        time_map = {
            'dinner': '0:00 - 23:59',
        }
        self.activity_times = ActivityTimes(time_map)

        self.action = PlayMusicAtDinnerTime()

    def tearDown(self):
        if self.action._timer is not None:
            self.action._timer.cancel()

        super(PlayMusicAtDinnerTimeTest, self).tearDown()

    def testOnAction_noAudioSink_returnsFalse(self):
        zone1 = Zone('Kitchen').add_device(self.motion).add_action(self.action)
        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_audioSinkInZoneButNoActivityTimes_returnsFalse(self):
        zone1 = Zone('Kitchen').add_device(self.sink).add_device(self.motion).add_action(self.action)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_audioSinkInZone_playsStreamAndReturnsTrue(self):
        zone1 = Zone('Kitchen').add_device(self.sink).add_device(self.motion) \
            .add_device(self.activity_times) \
            .add_action(self.action)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

    def testOnAction_audioSinkInNeighborZone_playsStreamAndReturnsTrue(self):
        zone1 = Zone('Kitchen').add_device(self.motion).add_device(self.activity_times) \
            .add_action(self.action)
        zone2 = Zone('great-room').add_device(self.sink)

        zone1 = zone1.add_neighbor(Neighbor(zone2.get_id(), NeighborType.OPEN_SPACE_MASTER))

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

    def testOnAction_audioSinkInZone_automaticallyPauseAtDesignatedPeriod(self):
        self.action = PlayMusicAtDinnerTime(duration_in_minutes=0.00025)
        zone1 = Zone('Kitchen').add_device(self.sink).add_device(self.motion) \
            .add_device(self.activity_times) \
            .add_action(self.action)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1]), pe.get_event_dispatcher())

        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

        time.sleep(0.02)
        self.assertEqual('pause', self.sink._get_last_test_command())
