import time

from zone_api import platform_encapsulator as pe
from zone_api.core.actions.announce_morning_weather_and_play_music import AnnounceMorningWeatherAndPlayMusic
from zone_api.core.devices.activity_times import ActivityTimes, ActivityType
from zone_api.core.devices.contact import Door
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.devices.weather import Weather
from zone_api.core.map_parameters import MapParameters

from zone_api_test.core.device_test import DeviceTest, create_zone_manager
from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent


class AnnounceMorningWeatherAndPlayMusicTest(DeviceTest):
    """ Unit tests for AnnounceMorningWeatherAndPlayMusic. """

    def setUp(self):
        self.sink, items = self.create_audio_sink()

        items.append(pe.create_number_item('Weather_Temperature'))
        items.append(pe.create_number_item('Weather_Humidity'))
        items.append(pe.create_string_item('Weather_Condition'))
        items.append(pe.create_number_item('Weather_ForecastTempMin'))
        items.append(pe.create_number_item('Weather_ForecastTempMax'))
        items.append(pe.create_switch_item('Door1'))
        items.append(pe.create_switch_item('Door2'))
        items.append(pe.create_switch_item('MotionSensor'))

        self.motion_item = items[-1]
        self.internal_door_item = items[-2]
        self.external_door_item = items[-3]

        self.set_items(items)
        super(AnnounceMorningWeatherAndPlayMusicTest, self).setUp()

        self.weather = Weather(items[0], items[1], items[2], None, None, items[4], items[5])
        self.motion = MotionSensor(self.motion_item)
        self.internal_door = Door(self.internal_door_item)
        self.external_door = Door(self.external_door_item)

        time_map = {
            ActivityType.WAKE_UP: '0:00 - 23:59',
        }
        self.activity_times = ActivityTimes(time_map)

        self.action = AnnounceMorningWeatherAndPlayMusic(MapParameters({}))

    def tearDown(self):
        if self.action._timer is not None:
            self.action._timer.cancel()

        super(AnnounceMorningWeatherAndPlayMusicTest, self).tearDown()

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

    def testOnAction_audioSinkInZone_announceAndPlaysStreamAndReturnsTrue(self):
        zone1 = Zone('Kitchen').add_device(self.sink).add_device(self.motion) \
            .add_device(self.activity_times) \
            .add_device(self.weather) \
            .add_action(self.action)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())
        self.assertTrue('Good morning' in self.sink.get_last_tts_message())

    def testOnAction_audioSinkInZoneNoWeather_announceAndPlaysStreamAndReturnsTrue(self):
        zone1 = Zone('Kitchen').add_device(self.sink).add_device(self.motion) \
            .add_device(self.activity_times) \
            .add_action(self.action)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())
        self.assertTrue(self.sink.get_last_tts_message() is None)

    def testOnAction_audioSinkInZone_stopAfterDoorClosed(self):
        zone1 = Zone('Kitchen').add_device(self.sink).add_device(self.motion) \
            .add_device(self.activity_times) \
            .add_action(self.action)
        zone2 = Zone.create_external_zone('garage').add_device(self.external_door)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

        event_info = EventInfo(ZoneEvent.DOOR_CLOSED, self.external_door_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher(), zone2)
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('pause', self.sink._get_last_test_command())

    def testOnAction_musicPlayingInternalDoorClosed_wontStopMusic(self):
        zone1 = Zone('Kitchen').add_device(self.sink).add_device(self.motion) \
            .add_device(self.activity_times) \
            .add_action(self.action)
        zone2 = Zone.create_first_floor_zone('bedroom').add_device(self.internal_door)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

        event_info = EventInfo(ZoneEvent.DOOR_CLOSED, self.internal_door_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher(), zone2)
        value = self.action.on_action(event_info)
        self.assertFalse(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

    def testOnAction_audioSinkInZone_automaticallyPauseAtDesignatedPeriod(self):
        parameters = MapParameters({'AnnounceMorningWeatherAndPlayMusic.durationInMinutes': 0.00025})
        self.action = AnnounceMorningWeatherAndPlayMusic(parameters)
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
