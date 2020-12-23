import time
from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.zone import Zone
from aaa_modules.layout_model.zone_manager import ZoneManager
from aaa_modules.layout_model.devices.switch import Light

from zone_apis_test.layout_model.device_test import DeviceTest


class LightTest(DeviceTest):
    """ Unit tests for switch.py. """
    def setUp(self):
        items = [pe.create_switch_item('TestLightName')]
        self.set_items(items)
        super(LightTest, self).setUp()

        self.lightItem = items[0]
        self.light = Light(self.lightItem, 10)

    def tearDown(self):
        self.light._cancel_timer()
        super(LightTest, self).tearDown()

    def testTurnOn_lightWasOff_returnsExpected(self):
        self.light.turnOn(pe.get_test_event_dispatcher())
        self.assertTrue(pe.is_in_on_state(self.lightItem))

    def testTurnOn_lightWasAlreadyOn_timerIsRenewed(self):
        pe.set_switch_state(self.lightItem, True, True)
        self.assertFalse(self.light._is_timer_active())

        self.light.turnOn(pe.get_test_event_dispatcher())
        self.assertTrue(pe.is_in_on_state(self.lightItem))
        self.assertTrue(self.light._is_timer_active())

    def testOnSwitchTurnedOn_validParams_timerIsTurnedOn(self):
        pe.set_switch_state(self.lightItem, True, True)

        is_processed = self.light.on_switch_turned_on(
            pe.get_test_event_dispatcher(), self.light.getItemName())
        self.assertTrue(is_processed)
        self.assertTrue(self.light._is_timer_active())

    def testOnSwitchTurnedOn_invalidItemName_returnsFalse(self):
        is_processed = self.light.on_switch_turned_on(
            pe.get_test_event_dispatcher(), "wrong name")
        self.assertFalse(is_processed)

    def testTurnOff_bothLightAndTimerOn_timerIsRenewed(self):
        pe.set_switch_state(self.lightItem, True, True)
        self.light._start_timer(pe.get_test_event_dispatcher())
        self.assertTrue(self.light._is_timer_active())

        self.light.turnOff(pe.get_test_event_dispatcher())
        self.assertFalse(self.light._is_timer_active())

    def testOnSwitchTurnedOff_validParams_timerIsTurnedOn(self):
        pe.set_switch_state(self.lightItem, True, True)
        self.light._start_timer(pe.get_test_event_dispatcher())

        is_processed = self.light.on_switch_turned_off(
            pe.get_test_event_dispatcher(), self.light.getItemName())
        self.assertTrue(is_processed)
        self.assertFalse(self.light._is_timer_active())

    def testOnSwitchTurnedOff_invalidItemName_returnsFalse(self):
        is_processed = self.light.on_switch_turned_off(
            pe.get_test_event_dispatcher(), "wrong name")
        self.assertFalse(is_processed)

    def testIsLowIlluminance_noThresholdSet_returnsFalse(self):
        self.assertFalse(self.light.isLowIlluminance(10))

    def testIsLowIlluminance_currentIlluminanceNotAvailable_returnsFalse(self):
        self.light = Light(self.lightItem, 10, 50)
        self.assertFalse(self.light.isLowIlluminance(-1))

    def testIsLowIlluminance_currentIlluminanceAboveThreshold_returnsFalse(self):
        self.light = Light(self.lightItem, 10, 50)
        self.assertFalse(self.light.isLowIlluminance(60))

    def testIsLowIlluminance_currentIlluminanceBelowThreshold_returnsTrue(self):
        self.light = Light(self.lightItem, 10, 50)
        self.assertTrue(self.light.isLowIlluminance(10))

    def testTimerTurnedOff_validParams_switchIsOff(self):
        zm = ZoneManager()
        self.light = Light(self.lightItem, 0.004)  # makes it 0.24 sec
        self.light = self.light.setZoneManager(zm.get_immutable_instance())

        zone = Zone('ff', [self.light])
        zm.add_zone(zone)

        pe.set_switch_state(self.lightItem, True, True)
        self.light._start_timer(pe.get_test_event_dispatcher())
        self.assertTrue(self.light._is_timer_active())

        time.sleep(0.3)
        self.assertFalse(self.light._is_timer_active())
        self.assertFalse(self.light.isOn())
