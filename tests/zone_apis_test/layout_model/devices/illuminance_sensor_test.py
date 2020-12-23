from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.devices.illuminance_sensor import IlluminanceSensor

from zone_apis_test.layout_model.device_test import DeviceTest


class IlluminanceSensorTest(DeviceTest):
    """ Unit tests for illuminance_sensor.py. """

    def setUp(self):
        self.item = pe.create_number_item('IlluminanceSensorName')
        self.set_items([self.item])
        super(IlluminanceSensorTest, self).setUp()

        self.illuminanceSensor = IlluminanceSensor(self.item)

    def testGetIlluminanceLevel_noParams_returnsValidValue(self):
        self.assertEqual(0, self.illuminanceSensor.get_illuminance_level())

        pe.set_number_value(self.item, 50, True)
        self.assertEqual(50, self.illuminanceSensor.get_illuminance_level())
