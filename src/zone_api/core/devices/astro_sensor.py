from zone_api.core.device import Device
from zone_api import platform_encapsulator as pe


class AstroSensor(Device):
    """
    A virtual sensor to determine the light on time; backed by a StringItem.
    """

    BED_TIME = "BED"

    LIGHT_ON_TIMES = ["EVENING", "NIGHT", BED_TIME]

    def __init__(self, string_item):
        """
        Ctor

        :param StringItem string_item:
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, string_item)

    def is_light_on_time(self, value=None):
        """
        Returns True if it is evening time; returns False otherwise.

        :param str value: the current time period. if is None, retrieve the value from the item.
        :rtype: bool
        """
        if value is None:
            value = pe.get_string_value(self.get_item())

        return any(s == value for s in self.LIGHT_ON_TIMES)

    def is_bed_time(self, value=None):
        """
        Returns True if it is bed time; returns False otherwise.

        :param str value: the current time period. if is None, retrieve the value from the item.
        :rtype: bool
        """
        if value is None:
            value = pe.get_string_value(self.get_item())

        return value == self.BED_TIME

    def current_period(self) -> str:
        return pe.get_string_value(self.get_item())

    def _set_current_period(self, value: str) -> None:
        """
        Sets the current period of the day. This method is meant for an internal action, and shall not be invoked
        in the public context.
        """
        pe.set_string_value(self.get_item(), value)
