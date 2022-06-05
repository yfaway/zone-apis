from unittest.mock import MagicMock

from zone_api import platform_encapsulator as pe
from zone_api.core.actions.randomize_light_bulb_color import RandomizeLightBulbColor
from zone_api.core.devices.switch import ColorLight
from zone_api.core.event_info import EventInfo
from zone_api.core.map_parameters import MapParameters
from zone_api.core.zone import Zone, Level
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class RandomizeLightBulbColorTest(DeviceTest):
    """ Unit tests for RandomizeLightBulbColor. """

    def setUp(self):
        items = [pe.create_switch_item('light_bulb_switch'), pe.create_color_item('light_bulb_color', True)]
        self.set_items(items)
        super(RandomizeLightBulbColorTest, self).setUp()

        self.action = RandomizeLightBulbColor(MapParameters({}))
        self.bulb = ColorLight(items[0], items[1], 5)

        self.zone1 = Zone('office', [], Level.FIRST_FLOOR) \
            .add_action(self.action) \
            .add_device(self.bulb)

        self.zm = create_zone_manager([self.zone1])

    def testOnAction_mockTerminate_terminateFunctionIsCalled(self):
        self.action._terminate = MagicMock(return_value=False)
        self.sendEvent()

        self.action._timer.cancel()
        self.action._terminate.assert_called()

    def testOnAction_lightIsOn_timerStartedAndColorChanged(self):
        pe.set_switch_state(self.get_items()[0], True)
        self.bulb.change_color = MagicMock()
        self.sendEvent()

        self.action._timer.cancel()
        self.bulb.change_color.assert_called()

    def testOnAction_lightIsOff_timerNotStartedAndColorNotChanged(self):
        pe.set_switch_state(self.get_items()[0], False)
        self.bulb.change_color = MagicMock()
        self.sendEvent()

        self.assertTrue(self.action._timer is None)
        self.bulb.change_color.assert_not_called()

    def sendEvent(self):
        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, self.get_items()[0], self.zone1, self.zm,
                               pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
