from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.devices.astro_sensor import AstroSensor
from zone_apis_test.layout_model.device_test import DeviceTest


class AstroSensorTest(DeviceTest):
    """ Unit tests for astro_sensor.py. """

    def setUp(self):
        self.item = pe.create_string_item('AstroSensorName')
        self.set_items([self.item])
        super(AstroSensorTest, self).setUp()

        self.astroSensor = AstroSensor(self.item)

    def testIsLightOnTime_eveningTime_returnsTrue(self):
        for value in AstroSensor.LIGHT_ON_TIMES:
            pe.set_string_value(self.item, value)
            self.assertTrue(self.astroSensor.is_light_on_time())

    def testIsLightOnTime_dayTime_returnsFalse(self):
        invalid_values = ["MORNING", "DAY", "AFTERNOON"]
        for value in invalid_values:
            pe.set_string_value(self.item, value)
            self.assertFalse(self.astroSensor.is_light_on_time())
