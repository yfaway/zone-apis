from zone_api import platform_encapsulator as pe
from zone_api.core.devices.illuminance_sensor import IlluminanceSensor

from zone_api_test.core.device_test import DeviceTest
from zone_api.models import NumberItem


class IlluminanceSensorTest(DeviceTest):
    """ Unit tests for illuminance_sensor.py. """

    def setUp(self):
        self.item = NumberItem('IlluminanceSensorName', 0)
        self.set_items([self.item])
        super(IlluminanceSensorTest, self).setUp()

        self.illuminanceSensor = IlluminanceSensor(self.item)

    def testGetIlluminanceLevel_noParams_returnsValidValue(self):
        self.assertEqual(0, self.illuminanceSensor.get_illuminance_level())

        self.item.set_value(50)
        self.assertEqual(50, self.illuminanceSensor.get_illuminance_level())
