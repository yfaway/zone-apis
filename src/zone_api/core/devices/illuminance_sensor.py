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

    def get_illuminance_level(self) -> float:
        """
        Returns an positive integer representing the LUX value.
        """
        return pe.get_number_value(self.get_item())


class FixedValueIlluminanceSensor(IlluminanceSensor):
    """
    Always report a provided illuminance value.
    Use case: a zone doesn't have a light sensor, but tends to be always at specific illuminance level. For example,
    a basement doesn't have enough light source and is always dark.
    """

    def __init__(self, name_item, illuminance_value: float):
        IlluminanceSensor.__init__(self, name_item)
        self._illuminance_value = illuminance_value

    def get_illuminance_level(self) -> float:
        return self._illuminance_value
