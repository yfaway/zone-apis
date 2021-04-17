from zone_api.core.device import Device
from zone_api import platform_encapsulator as pe


class IlluminanceSensor(Device):
    """
    Represents a light/illuminance sensor; the underlying OpenHab object is a
    NumberItem.
    """

    def __init__(self, number_item):
        """
        Ctor

        :param NumberItem number_item:
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, number_item)

    def get_illuminance_level(self):
        """
        Returns an positive integer representing the LUX value.
        """
        return pe.get_number_value(self.get_item())
