from aaa_modules import platform_encapsulator as pe
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone, ZoneEvent
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition
from aaa_modules.layout_model.devices.switch import Light
from aaa_modules.layout_model.devices.chromecast_audio_sink import ChromeCastAudioSink
from aaa_modules.layout_model.actions.turn_off_devices_on_alarm_mode_change import TurnOffDevicesOnAlarmModeChange


class TurnOffDevicesOnAlarmModeChangeTest(DeviceTest):
    """ Unit tests for turn-off-devices-on-alarm-mode-change.py. """

    def setUp(self):
        self.audioSink, sink_items = self.create_audio_sink()

        items = [pe.create_switch_item('_testMotion'),
                 pe.create_switch_item('_testAlarmStatus'),
                 pe.create_number_item('_testArmMode'),
                 pe.create_switch_item('_testLight1'),
                 pe.create_switch_item('_testLight2'),
                 ]

        for item in sink_items:
            items.append(item)

        self.set_items(items)
        super(TurnOffDevicesOnAlarmModeChangeTest, self).setUp()

        self.partition = AlarmPartition(items[1], items[2])
        self.light1 = Light(items[3], 4)
        self.light2 = Light(items[4], 4)

        self.action = TurnOffDevicesOnAlarmModeChange()

        self.audioSink._set_test_mode()
        self.audioSink.play_stream("http://stream")
        self.light1.turnOn(pe.get_event_dispatcher())
        self.light2.turnOn(pe.get_event_dispatcher())
        self.partition.disarm(pe.get_event_dispatcher())

    def testOnAction_armedAwayEvent_turnOffDevicesAndReturnsTrue(self):
        (zone, zm, event_info) = self.createTestData(ZoneEvent.PARTITION_ARMED_AWAY)
        self.assertTrue(zone.isLightOn())

        self.invokeActionAndAssertDevicesTurnedOff(zone, event_info, zm)

    def testOnAction_disarmEvent_turnOffDevicesAndReturnsTrue(self):
        (zone, zm, event_info) = self.createTestData(ZoneEvent.PARTITION_DISARMED_FROM_AWAY)
        self.assertTrue(zone.isLightOn())

        self.invokeActionAndAssertDevicesTurnedOff(zone, event_info, zm)

    def invokeActionAndAssertDevicesTurnedOff(self, zone, event_info, zm):
        value = self.action.onAction(event_info)
        self.assertTrue(value)

        for z in zm.get_zones():
            if z is not zone:
                self.assertFalse(z.isLightOn())

        if event_info.getEventType() == ZoneEvent.PARTITION_DISARMED_FROM_AWAY:
            self.assertTrue(zone.isLightOn())
        else:
            self.assertFalse(zone.isLightOn())

        self.assertEqual("pause", self.audioSink._get_last_test_command())

    def createTestData(self, zone_event):
        """
        :return: a list of two zones, the mocked zone manager, and the event dispatcher
        :rtype: list
        """

        self.partition.arm_away(pe.get_event_dispatcher())

        porch = Zone('porch', [self.partition, self.light1, self.audioSink]).add_action(self.action)
        great_room = Zone('great room', [self.light2])
        zm = create_zone_manager([porch, great_room])
        event_info = EventInfo(zone_event, self.get_items()[1], porch, zm, pe.get_event_dispatcher())

        return [porch, zm, event_info]
