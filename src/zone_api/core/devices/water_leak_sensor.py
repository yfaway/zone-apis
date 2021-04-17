from zone_api.core.device import Device
from zone_api import platform_encapsulator as pe


class WaterLeakSensor(Device):
    """
    Represents a generic water leak sensor.
    """

    def __init__(self, state_item):
        """
        Ctor

        :param SwitchItem state_item: indicates if there is a leak
        :raise ValueError: if value_item is invalid
        """
        Device.__init__(self, state_item)

    def is_water_detected(self):
        """
        :return: true if the sensor has detected a water leak.
        :rtype: bool
        """
        return pe.is_in_on_state(self.get_item())

    def reset_value_states(self):
        """ Override. """
        pe.set_switch_state(self.get_item(), False)
