from zone_api.core.device import Device
from zone_api import platform_encapsulator as pe


class HumiditySensor(Device):
    """
    Represents a humidity sensor.
    """

    def __init__(self, humidity_item):
        """
        Ctor

        :param NumberItem humidity_item: the item to get the humidity reading
        :raise ValueError: if humidity_item is invalid
        """
        Device.__init__(self, humidity_item)

    def get_humidity(self):
        """
        :return: the current humidity level in percentage
        :rtype: int
        """
        return pe.get_number_value(self.get_item())

    def reset_value_states(self):
        """ Override. """
        pe.set_number_value(self.get_item(), -1)
