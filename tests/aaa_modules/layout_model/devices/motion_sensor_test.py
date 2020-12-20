from ..device_test import DeviceTest
from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor


class MotionSensorTest(DeviceTest):
    def setUp(self):
        items = [pe.create_switch_item('MotionSensorName')]
        self.set_items(items)
        super(MotionSensorTest, self).setUp()

        self.motionSensor = MotionSensor(items[0])

    def test_is_on_various_returnsExpected(self):
        self.assertFalse(self.motionSensor.is_on())

        pe.set_switch_state(self.get_items()[0], True, True)
        self.assertTrue(self.motionSensor.is_on())

    def testIsOccupied_various_returnsExpected(self):
        self.assertFalse(self.motionSensor.is_occupied())

        self.motionSensor.on_triggered(None)
        self.assertTrue(self.motionSensor.is_occupied())

        pe.set_switch_state(self.get_items()[0], True, True)
        self.assertTrue(self.motionSensor.is_occupied())
