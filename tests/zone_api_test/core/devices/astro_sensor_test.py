from zone_api import platform_encapsulator as pe
from zone_api.core.devices.astro_sensor import AstroSensor
from zone_api_test.core.device_test import DeviceTest
from zone_api.models import StringItem


class AstroSensorTest(DeviceTest):
    """ Unit tests for astro_sensor.py. """

    def setUp(self):
        self.item = StringItem('AstroSensorName', None)
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
