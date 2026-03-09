from unittest.mock import patch

from zone_api import platform_encapsulator as pe
from zone_api.core.devices.dimmer import Dimmer

from zone_api_test.core.device_test import DeviceTest


class DimmerTest(DeviceTest):

    MOCKED_ACTIVITY_TIMES_PATH = "zone_api.core.devices.activity_times.ActivityTimes"
    MOCKED_ZONE_MANAGER_PATH = "zone_api.core.immutable_zone_manager.ImmutableZoneManager"

    def setUp(self):
        items = [pe.create_dimmer_item('TestDimmerName')]
        self.set_items(items)
        super(DimmerTest, self).setUp()

        self.dimmerItem = items[0]
        self.dimmer = Dimmer(self.dimmerItem, 10, 100)

    def tearDown(self):
        self.dimmer._cancel_timer()
        super(DimmerTest, self).tearDown()

    def testTurnOn_lightWasOffOutsideDimTimeRange_returnsExpected(self):
        with patch(DimmerTest.MOCKED_ACTIVITY_TIMES_PATH) as mock_activity:
            mock_activity.is_sleep_time.return_value = False

            with patch(DimmerTest.MOCKED_ZONE_MANAGER_PATH) as mock_zm:
                mock_zm.get_first_device_by_type.return_value = mock_activity
                pe.add_zone_manager_to_context(mock_zm)

                dim_level = 7
                self.dimmer = Dimmer(self.dimmerItem, 10, dim_level)

                self.dimmer.turn_on(pe.get_event_dispatcher())
                self.assertTrue(self.dimmer.is_on())
                self.assertEqual(100, pe.get_dimmer_percentage(self.dimmerItem))
                self.assertTrue(self.dimmer._is_timer_active())

    def testTurnOn_lightWasOffWithinDimTimeRange_returnsExpected(self):
        with patch(DimmerTest.MOCKED_ACTIVITY_TIMES_PATH) as mock_activity:
            mock_activity.is_sleep_time.return_value = True

            with patch(DimmerTest.MOCKED_ZONE_MANAGER_PATH) as mock_zm:
                mock_zm.get_first_device_by_type.return_value = mock_activity
                pe.add_zone_manager_to_context(mock_zm)

                dim_level = 5
                self.dimmer = Dimmer(self.dimmerItem, 10, dim_level)

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
