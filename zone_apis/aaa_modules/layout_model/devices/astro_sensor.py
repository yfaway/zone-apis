from aaa_modules.layout_model.device import Device
from aaa_modules import platform_encapsulator as pe


class AstroSensor(Device):
    """
    A virtual sensor to determine the light on time; backed by a StringItem.
    """

    LIGHT_ON_TIMES = ["EVENING", "NIGHT", "BED"]

    def __init__(self, string_item):
        """
        Ctor

        :param StringItem string_item:
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, string_item)

    def is_light_on_time(self):
        """
        Returns True if it is evening time; returns False otherwise.

        :rtype: bool
        """
        value = pe.get_string_value(self.getItem())
        return any(s == value for s in self.LIGHT_ON_TIMES)
