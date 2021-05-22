from zone_api import platform_encapsulator as pe
from zone_api.core.devices.switch import Fan

from zone_api_test.core.device_test import DeviceTest, create_zone_manager
from zone_api.core.event_info import EventInfo
from zone_api.core.neighbor import Neighbor, NeighborType
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.actions.play_music_during_shower import PlayMusicDuringShower


class PlayMusicDuringShowerTest(DeviceTest):
    """ Unit tests for play_music_during_shower.py. """

    def setUp(self):
        self.sink, items = self.create_audio_sink()

        items.append(pe.create_switch_item('Fan1'))
        self.fan_item = items[-1]

        self.set_items(items)
        super(PlayMusicDuringShowerTest, self).setUp()

        self.fan = Fan(self.fan_item, 2)
        self.action = PlayMusicDuringShower()

    def testOnAction_wrongEventType_returnsFalse(self):
        self.zone = Zone('innerZone').add_action(self.action)
        event_info = EventInfo(ZoneEvent.DOOR_OPEN, self.fan_item, self.zone,
                               create_zone_manager([self.zone]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_noAudioSink_returnsFalse(self):
        self.zone = Zone('innerZone').add_action(self.action)
        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.fan_item, self.zone,
                               create_zone_manager([self.zone]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_switchOnEventAndAudioSinkInZone_playsStreamAndReturnsTrue(self):
        zone1 = Zone('shower').add_device(self.sink).add_device(self.fan).add_action(self.action)

        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.fan_item, zone1,
                               None, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

    def testOnAction_switchOnEventAndAudioSinkInNeighborZone_playsStreamAndReturnsTrue(self):
        zone1 = Zone('shower').add_device(self.fan).add_action(self.action)
        zone2 = Zone('washroom').add_device(self.sink)

        zone1 = zone1.add_neighbor(Neighbor(zone2.get_id(), NeighborType.OPEN_SPACE))

        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.fan_item, zone1,
                               create_zone_manager([zone1, zone2]), pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('playStream', self.sink._get_last_test_command())

    def testOnAction_switchOffEvent_pauseStreamAndReturnsTrue(self):
        zone1 = Zone('shower').add_device(self.sink).add_device(self.fan).add_action(self.action)

        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_OFF, self.fan_item, zone1,
                               None, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertEqual('pause', self.sink._get_last_test_command())
