from zone_api.core.device import Device
from zone_api import platform_encapsulator as pe


class TemperatureSensor(Device):
    """
    Represents a temperature sensor.
    """

    def __init__(self, temperature_item, battery_percentage_item=None, wifi=False, auto_report=True):
        """
        Ctor

        :param NumberItem temperature_item: the item to get the humidity reading
        :raise ValueError: if temperature_item is invalid
        """
        Device.__init__(self, openhab_item=temperature_item, battery_percentage_item=battery_percentage_item, wifi=wifi,
                        battery_powered=battery_percentage_item is not None, auto_report=auto_report)

    def get_temperature(self):
        """
        :return: the current temperature in degree.
        :rtype: int
        """
        return pe.get_number_value(self.get_item())

    def reset_value_states(self):
        """ Override. """
        pe.set_number_value(self.get_item(), -999)