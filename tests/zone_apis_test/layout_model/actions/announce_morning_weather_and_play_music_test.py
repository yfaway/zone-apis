import time

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.announce_morning_weather_and_play_music import AnnounceMorningWeatherAndPlayMusic
from aaa_modules.layout_model.devices.activity_times import ActivityTimes
from aaa_modules.layout_model.devices.contact import Door
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor

from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone, ZoneEvent


class AnnounceMorningWeatherAndPlayMusicTest(DeviceTest):
    """ Unit tests for AnnounceMorningWeatherAndPlayMusic. """

    def setUp(self):
        self.sink, items = self.create_audio_sink()

        items.append(pe.create_number_item('VT_Weather_Temperature'))
        items.append(pe.create_number_item('VT_Weather_ForecastTempMin'))
        items.append(pe.create_number_item('VT_Weather_ForecastTempMax'))
        items.append(pe.create_string_item('VT_Weather_Condition'))
        items.append(pe.create_switch_item('Door1'))
        items.append(pe.create_switch_item('Door2'))
        items.append(pe.create_switch_item('MotionSensor'))

        self.motion_item = items[-1]
        self.internal_door_item = items[-2]
        self.external_door_item = items[-3]

        self.set_items(items)
        super(AnnounceMorningWeatherAndPlayMusicTest, self).setUp()

        self.motion = MotionSensor(self.motion_item)
        self.internal_door = Door(self.internal_door_item)
        self.external_door = Door(self.external_door_item)

        time_map = {
            'wakeup': '0:00 - 23:59',
        }
        self.activity_times = ActivityTimes(time_map)

        self.action = AnnounceMorningWeatherAndPlayMusic()

    def tearDown(self):
        if self.action._timer is not None:
            self.action._timer.cancel()

        super(AnnounceMorningWeatherAndPlayMusicTest, self).tearDown()

    def testOnAction_noAudioSink_returnsFalse(self):
        zone1 = Zone('Kitchen').addDevice(self.motion).add_action(self.action)
        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1]), pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertFalse(value)

    def testOnAction_audioSinkInZoneButNoActivityTimes_returnsFalse(self):
        zone1 = Zone('Kitchen').addDevice(self.sink).addDevice(self.motion).add_action(self.action)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1]), pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertFalse(value)

    def testOnAction_audioSinkInZone_announceAndPlaysStreamAndReturnsTrue(self):
        zone1 = Zone('Kitchen').addDevice(self.sink).addDevice(self.motion) \
            .addDevice(self.activity_times) \
            .add_action(self.action)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1]), pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())
        self.assertTrue('Good morning' in self.sink.get_last_tts_message())

    def testOnAction_audioSinkInZone_stopAfterDoorClosed(self):
        zone1 = Zone('Kitchen').addDevice(self.sink).addDevice(self.motion) \
            .addDevice(self.activity_times) \
            .add_action(self.action)
        zone2 = Zone.create_external_zone('garage').addDevice(self.external_door)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

        event_info = EventInfo(ZoneEvent.CONTACT_CLOSED, self.external_door_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher(), zone2)
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('pause', self.sink._get_last_test_command())

    def testOnAction_musicPlayingInternalDoorClosed_wontStopMusic(self):
        zone1 = Zone('Kitchen').addDevice(self.sink).addDevice(self.motion) \
            .addDevice(self.activity_times) \
            .add_action(self.action)
        zone2 = Zone.create_first_floor_zone('bedroom').addDevice(self.internal_door)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

        event_info = EventInfo(ZoneEvent.CONTACT_CLOSED, self.internal_door_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher(), zone2)
        value = self.action.onAction(event_info)
        self.assertFalse(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

    def testOnAction_audioSinkInZone_automaticallyPauseAtDesignatedPeriod(self):
        self.action = AnnounceMorningWeatherAndPlayMusic(duration_in_minutes=0.00025)
        zone1 = Zone('Kitchen').addDevice(self.sink).addDevice(self.motion) \
            .addDevice(self.activity_times) \
            .add_action(self.action)

        event_info = EventInfo(ZoneEvent.MOTION, self.motion_item, zone1,
                               create_zone_manager([zone1]), pe.get_event_dispatcher())

        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

        time.sleep(0.02)
        self.assertEqual('pause', self.sink._get_last_test_command())
