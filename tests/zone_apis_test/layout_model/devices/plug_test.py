from zone_apis_test.layout_model.device_test import DeviceTest

from aaa_modules.layout_model.devices.plug import Plug
from aaa_modules import platform_encapsulator as pe


class PlugTest(DeviceTest):
    """ Unit tests for plug.py. """

    def setUp(self):
        items = [pe.create_switch_item('_Plug'), pe.create_number_item('_Power')]
        self.set_items(items)
        super(PlugTest, self).setUp()

        self.plug = Plug(items[0], items[1])

    def testIsOn_notOn_returnsFalse(self):
        self.assertFalse(self.plug.is_on())

    def testTurnOn_withScopeEvents_returnsTrue(self):
        self.plug.turn_on(pe.get_event_dispatcher())
        pe.set_number_value(self.get_items()[1], 100)

        self.assertTrue(self.plug.is_on())
        self.assertEqual(100, self.plug.get_wattage())

    def testTurnOff_withScopeEvents_returnsTrue(self):
        pe.set_switch_state(self.plug.get_item(), True)
        self.assertTrue(self.plug.is_on())

        self.plug.turn_off(pe.get_event_dispatcher())
        self.assertFalse(self.plug.is_on())
