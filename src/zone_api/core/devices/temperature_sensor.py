from zone_api.core.device import Device
from zone_api import platform_encapsulator as pe


class TemperatureSensor(Device):
    """
    Represents a temperature sensor.
    """

    def __init__(self, temperature_item, battery_powered=False, wifi=True, auto_report=True):
        """
        Ctor

        :param NumberItem temperature_item: the item to get the humidity reading
        :raise ValueError: if temperature_item is invalid
        """
        Device.__init__(self, temperature_item, [], battery_powered, wifi, auto_report)

    def get_temperature(self):
        """
        :return: the current temperature in degree.
        :rtype: int
        """
        return pe.get_number_value(self.get_item())

    def reset_value_states(self):
        """ Override. """
        pe.set_number_value(self.get_item(), -999)
