from zone_api import platform_encapsulator as pe
from zone_api.core.devices.motion_sensor import MotionSensor

from zone_api_test.core.device_test import DeviceTest
from zone_api.models import SwitchItem


class MotionSensorTest(DeviceTest):
    def setUp(self):
        items = [SwitchItem('MotionSensorName', "OFF")]
        self.set_items(items)
        super(MotionSensorTest, self).setUp()

        self.motionSensor = MotionSensor(items[0])

    def test_is_on_various_returnsExpected(self):
        self.assertFalse(self.motionSensor.is_on())

        self.get_items()[0].on()
        self.assertTrue(self.motionSensor.is_on())

    def testIsOccupied_various_returnsExpected(self):
        self.assertFalse(self.motionSensor.is_occupied())

        self.motionSensor.update_last_activated_timestamp()
        self.assertTrue(self.motionSensor.is_occupied())

        self.get_items()[0].on()
        self.assertTrue(self.motionSensor.is_occupied())

    def testGetBatteryPercentage_none_returnsExpected(self):
        self.assertTrue(self.motionSensor.get_battery_percentage() is None)
