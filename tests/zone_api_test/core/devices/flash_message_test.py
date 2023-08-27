import time
from zone_api import platform_encapsulator as pe
from zone_api.core.devices.flash_message import FlashMessage

from zone_api_test.core.device_test import DeviceTest


class FlashMessageTest(DeviceTest):
    """ Unit tests for flash_message.py. """

    def setUp(self):
        self.defaultTimerDurationInSec = 10

        items = [pe.create_string_item('TestMessageName')]
        self.set_items(items)
        super(FlashMessageTest, self).setUp()

        self.messageItem = items[0]
        self.flashMessage = FlashMessage(self.messageItem)

    def tearDown(self):
        self.flashMessage._cancel_timer()
        super(FlashMessageTest, self).tearDown()

    def testSetMessage_validParams_messageSetAndThenReset(self):
        value = 'hello world'
        self.flashMessage.set_value(value, 0.05)
        self.assertEqual(self.flashMessage.get_value(), value)
        time.sleep(0.07)
        self.assertEqual(self.flashMessage.get_value(), '')
