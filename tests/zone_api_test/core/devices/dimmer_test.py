import time

from zone_api import platform_encapsulator as pe
from zone_api.core.devices.dimmer import Dimmer

from zone_api_test.core.device_test import DeviceTest


class DimmerTest(DeviceTest):

    def setUp(self):
        items = [pe.create_dimmer_item('TestDimmerName')]
        self.set_items(items)
        super(DimmerTest, self).setUp()

        self.dimmerItem = items[0]
        self.dimmer = Dimmer(self.dimmerItem, 10, 100, "0-23:59")

    def tearDown(self):
        self.dimmer._cancel_timer()
        super(DimmerTest, self).tearDown()

    def testTurnOn_lightWasOffOutsideDimTimeRange_returnsExpected(self):
        time_struct = time.localtime()
        hour_of_day = time_struct[3]

        if hour_of_day >= 22:  # handle 24-hour wrapping
            hour_of_day = 0

        dim_level = 5
        time_ranges = "{}-{}".format(hour_of_day + 2, hour_of_day + 2)
        self.dimmer = Dimmer(self.dimmerItem, 10, dim_level, time_ranges)

        self.dimmer.turn_on(pe.get_event_dispatcher())
        self.assertTrue(self.dimmer.is_on())
        self.assertEqual(100, pe.get_dimmer_percentage(self.dimmerItem))
        self.assertTrue(self.dimmer._is_timer_active())

    def testTurnOn_lightWasOffWithinDimTimeRange_returnsExpected(self):
        time_struct = time.localtime()
        hour_of_day = time_struct[3]

        dim_level = 5
        next_hour = 0 if hour_of_day == 23 else hour_of_day + 1  # 24-hour wrapping
        time_ranges = "{}-{}".format(hour_of_day, next_hour)
        self.dimmer = Dimmer(self.dimmerItem, 10, dim_level, time_ranges)

        self.dimmer.turn_on(pe.get_event_dispatcher())
        self.assertTrue(self.dimmer.is_on())
        self.assertEqual(dim_level, pe.get_dimmer_percentage(self.dimmerItem))
        self.assertTrue(self.dimmer._is_timer_active())

    def testTurnOn_lightWasAlreadyOn_timerIsRenewed(self):
        pe.set_dimmer_value(self.dimmerItem, 100)

        self.dimmer.turn_on(pe.get_event_dispatcher())
        self.assertTrue(self.dimmer.is_on())
        self.assertTrue(self.dimmer._is_timer_active())

    def testTurnOff_bothLightAndTimerOn_timerIsRenewed(self):
        pe.set_dimmer_value(self.dimmerItem, 0)

        self.dimmer.turn_off(pe.get_event_dispatcher())
        self.assertFalse(self.dimmer.is_on())
