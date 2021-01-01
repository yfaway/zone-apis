from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.devices.switch import Fan

from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.neighbor import Neighbor, NeighborType
from aaa_modules.layout_model.zone import Zone, ZoneEvent
from aaa_modules.layout_model.devices.chromecast_audio_sink import ChromeCastAudioSink
from aaa_modules.layout_model.actions.play_music_during_shower import PlayMusicDuringShower


class PlayMusicDuringShowerTest(DeviceTest):
    """ Unit tests for play_music_during_shower.py. """

    def setUp(self):
        items = [pe.create_switch_item('Fan1'),
                 pe.create_player_item('_testPlayer'),
                 pe.create_number_item('_testVolume'),
                 pe.create_string_item('_testTitle'),
                 pe.create_switch_item('_testIdling'),
                 ]
        self.set_items(items)
        super(PlayMusicDuringShowerTest, self).setUp()

        self.fan = Fan(items[0], 2)
        self.sink = ChromeCastAudioSink('sinkName', items[1], items[2], items[3], items[4])
        self.action = PlayMusicDuringShower("anUrl")

        self.sink._set_test_mode()

    def testOnAction_wrongEventType_returnsFalse(self):
        event_info = EventInfo(ZoneEvent.CONTACT_OPEN, self.get_items()[0], Zone('innerZone'),
                               None, pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertFalse(value)

    def testOnAction_noAudioSink_returnsFalse(self):
        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.get_items()[0], Zone('innerZone'),
                               create_zone_manager([]), pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertFalse(value)

    def testOnAction_switchOnEventAndAudioSinkInZone_playsStreamAndReturnsTrue(self):
        zone1 = Zone('shower').addDevice(self.sink).addDevice(self.fan)

        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.get_items()[0], zone1,
                               None, pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

    def testOnAction_switchOnEventAndAudioSinkInNeighborZone_playsStreamAndReturnsTrue(self):
        zone1 = Zone('shower').addDevice(self.fan)
        zone2 = Zone('washroom').addDevice(self.sink)

        zone1 = zone1.add_neighbor(Neighbor(zone2.getId(), NeighborType.OPEN_SPACE))

        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.get_items()[0], zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

    def testOnAction_switchOffEvent_pauseStreamAndReturnsTrue(self):
        zone1 = Zone('shower').addDevice(self.sink).addDevice(self.fan)

        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_OFF, self.get_items()[0], zone1,
                               None, pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('pause', self.sink._get_last_test_command())
