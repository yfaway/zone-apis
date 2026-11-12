from zone_api_test.core.device_test import DeviceTest

from zone_api.core.devices.plug import Plug
from zone_api import platform_encapsulator as pe
from zone_api.models import NumberItem, SwitchItem


class PlugTest(DeviceTest):
    """ Unit tests for plug.py. """

    def setUp(self):
        items = [SwitchItem('_Plug', "OFF"), NumberItem('_Power', None)]
        self.set_items(items)
        super(PlugTest, self).setUp()

        self.plug = Plug(items[0], items[1])

    def testIsOn_notOn_returnsFalse(self):
        self.assertFalse(self.plug.is_on())

    def testTurnOn_withScopeEvents_returnsTrue(self):
        self.plug.turn_on(pe.get_event_dispatcher())
        self.get_items()[1].set_value(100)

        self.assertTrue(self.plug.is_on())
        self.assertEqual(100, self.plug.get_wattage())

    def testTurnOff_withScopeEvents_returnsTrue(self):
        self.plug.get_item().on()
        self.assertTrue(self.plug.is_on())

        self.plug.turn_off(pe.get_event_dispatcher())
        self.assertFalse(self.plug.is_on())
