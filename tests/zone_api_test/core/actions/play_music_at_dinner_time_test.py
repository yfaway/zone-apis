import time

from zone_api import platform_encapsulator as pe
from zone_api.core.actions.play_music_at_dinner_time import PlayMusicAtDinnerTime
from zone_api.core.devices.activity_times import ActivityTimes, ActivityType
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.map_parameters import MapParameters

from zone_api_test.core.device_test import DeviceTest, create_zone_manager
from zone_api.core.event_info import EventInfo
from zone_api.core.neighbor import Neighbor, NeighborType
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent


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
            ActivityType.DINNER: '0:00 - 23:59',
        }
        self.activity_times = ActivityTimes(time_map)

        self.action = PlayMusicAtDinnerTime(MapParameters({}))

    def tearDown(self):
        if self.action._timer is not None:
            self.action._timer.cancel()

        super(PlayMusicAtDinnerTimeTest, self).tearDown()

    def testOnAction_noAudioSink_returnsFalse(self):
        zone1 = Zone('Kitchen').add_device(self.motion).add_device(self.activity_times).add_action(self.action)
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
        parameters = MapParameters({'PlayMusicAtDinnerTime.durationInMinutes': 0.00025})
        self.action = PlayMusicAtDinnerTime(parameters)
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
