from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.tell_kids_to_go_to_bed import TellKidsToGoToBed
from aaa_modules.layout_model.devices.switch import Light

from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone, Level
from aaa_modules.layout_model.zone_event import ZoneEvent


class TellKidsToGoToBedTest(DeviceTest):
    """ Unit tests for TellKidsToGoToBed. """

    def setUp(self):
        self.sink, items = self.create_audio_sink()

        items.append(pe.create_switch_item('Light1'))
        items.append(pe.create_switch_item('Light2'))
        self.light1_item = items[-2]
        self.light2_item = items[-1]

        self.set_items(items)
        super(TellKidsToGoToBedTest, self).setUp()

        self.kitchen_light = Light(self.light1_item, 5)
        self.foyer_light = Light(self.light2_item, 5)

        self.action = TellKidsToGoToBed()

        self.foyer = Zone('Foyer', [self.foyer_light], Level.FIRST_FLOOR)
        self.kitchen = Zone('kitchen', [self.kitchen_light, self.sink], Level.FIRST_FLOOR).add_action(self.action)
        self.zm = create_zone_manager([self.foyer, self.kitchen])

    def tearDown(self):
        self.foyer_light._cancel_timer()
        self.kitchen_light._cancel_timer()

        super(TellKidsToGoToBedTest, self).tearDown()

    def testOnAction_firstNotice_returnsTrue(self):
        event_info = EventInfo(ZoneEvent.TIMER, None, self.kitchen, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(
            self.action.create_timer_event_info(event_info, TellKidsToGoToBed.Type.FIRST_NOTICE))
        self.assertTrue(value)

        self.assertTrue('put away everything' in self.sink.get_last_tts_message())

    def testOnAction_secondNotice_returnsTrue(self):
        pe.set_switch_state(self.foyer_light.get_item(), False)
        pe.set_switch_state(self.kitchen_light.get_item(), True)

        event_info = EventInfo(ZoneEvent.TIMER, None, self.kitchen, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(
            self.action.create_timer_event_info(event_info, TellKidsToGoToBed.Type.SECOND_NOTICE))
        self.assertTrue(value)

        self.assertTrue('go upstairs now' in self.sink.get_last_tts_message())
        self.assertFalse(self.kitchen_light.is_on())
        self.assertTrue(self.foyer_light.is_on())
