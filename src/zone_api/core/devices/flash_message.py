from threading import Timer

from zone_api.core.device import Device
from zone_api import platform_encapsulator as pe


class FlashMessage(Device):
    """
    Set a message (which will get displayed on the UI) for a specific period of time. Once the time is expired, the
    messaged is removed.
    """

    def __init__(self, value_item):
        """
        Ctor

        :param NumberItem value_item: the in/out item to get/set the text value
        :raise ValueError: if value_item is invalid
        """
        Device.__init__(self, value_item, [], False, False, False)

        self.timer = None
        self.set_value("", 3)  # by default the value with OH would be UNDEF

    def get_value(self):
        """
        :return: the current sensor value.
        :rtype: int
        """
        return pe.get_string_value(self.get_item())

    def set_value(self, value: str, display_time_in_seconds: float):
        """
        Set the message and retain the value for the specified time, after which the message will be reset to an
        empty string.
        """
        pe.set_string_value(self.get_item(), value)

        def reset_message():
            pe.set_string_value(self.get_item(), '')

        self._cancel_timer()  # cancel the previous timer, if any.

        self.timer = Timer(display_time_in_seconds, reset_message)
        self.timer.start()

    def _cancel_timer(self):
        """
        Cancel the reset timer.
        """
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
            self.timer = None
