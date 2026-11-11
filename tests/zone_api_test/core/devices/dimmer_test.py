from unittest.mock import patch

from zone_api import platform_encapsulator as pe
from zone_api.core.devices.dimmer import Dimmer

from zone_api_test.core.device_test import DeviceTest
from zone_api.models import DimmerItem


class DimmerTest(DeviceTest):

    MOCKED_ACTIVITY_TIMES_PATH = "zone_api.core.devices.activity_times.ActivityTimes"
    MOCKED_ZONE_MANAGER_PATH = "zone_api.core.immutable_zone_manager.ImmutableZoneManager"

    def setUp(self):
        items = [DimmerItem('TestDimmerName', 0)]
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
                self.assertEqual(100, self.dimmerItem.percentage())
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
                self.assertEqual(dim_level, self.dimmerItem.percentage())
                self.assertTrue(self.dimmer._is_timer_active())

    def testTurnOn_lightWasAlreadyOn_timerIsRenewed(self):
        self.dimmerItem.set_percentage(100)

        self.dimmer.turn_on(pe.get_event_dispatcher())
        self.assertTrue(self.dimmer.is_on())
        self.assertTrue(self.dimmer._is_timer_active())

    def testTurnOff_bothLightAndTimerOn_timerIsRenewed(self):
        self.dimmerItem.set_percentage(0)

        self.dimmer.turn_off(pe.get_event_dispatcher())
        self.assertFalse(self.dimmer.is_on())
