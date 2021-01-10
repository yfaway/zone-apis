from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.devices.switch import Fan

from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.neighbor import Neighbor, NeighborType
from aaa_modules.layout_model.zone import Zone, ZoneEvent
from aaa_modules.layout_model.actions.play_music_during_shower import PlayMusicDuringShower


class PlayMusicDuringShowerTest(DeviceTest):
    """ Unit tests for play_music_during_shower.py. """

    def setUp(self):
        self.sink, items = self.create_audio_sink()

        items.append(pe.create_switch_item('Fan1'))
        self.fan_item = items[-1]

        self.set_items(items)
        super(PlayMusicDuringShowerTest, self).setUp()

        self.fan = Fan(self.fan_item, 2)
        self.action = PlayMusicDuringShower("anUrl")

    def testOnAction_wrongEventType_returnsFalse(self):
        self.zone = Zone('innerZone').add_action(self.action)
        event_info = EventInfo(ZoneEvent.CONTACT_OPEN, self.fan_item, self.zone,
                               create_zone_manager([self.zone]), pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertFalse(value)

    def testOnAction_noAudioSink_returnsFalse(self):
        self.zone = Zone('innerZone').add_action(self.action)
        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.fan_item, self.zone,
                               create_zone_manager([self.zone]), pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertFalse(value)

    def testOnAction_switchOnEventAndAudioSinkInZone_playsStreamAndReturnsTrue(self):
        zone1 = Zone('shower').addDevice(self.sink).addDevice(self.fan).add_action(self.action)

        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.fan_item, zone1,
                               None, pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

    def testOnAction_switchOnEventAndAudioSinkInNeighborZone_playsStreamAndReturnsTrue(self):
        zone1 = Zone('shower').addDevice(self.fan).add_action(self.action)
        zone2 = Zone('washroom').addDevice(self.sink)

        zone1 = zone1.add_neighbor(Neighbor(zone2.getId(), NeighborType.OPEN_SPACE))

        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.fan_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

    def testOnAction_switchOffEvent_pauseStreamAndReturnsTrue(self):
        zone1 = Zone('shower').addDevice(self.sink).addDevice(self.fan).add_action(self.action)

        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_OFF, self.fan_item, zone1,
                               None, pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual('pause', self.sink._get_last_test_command())
