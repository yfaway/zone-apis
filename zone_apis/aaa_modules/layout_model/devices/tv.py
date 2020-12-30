from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.device import Device


class Tv(Device):
    """
    Represents a TV.
    """

    def __init__(self, power_status_item):
        """
        Ctor

        :param SwitchItem power_status_item:
        :raise ValueError: if any parameter is invalid
        """

        Device.__init__(self, power_status_item)

    def is_on(self):
        """
        Returns true if the TV is on; false otherwise.
        """
        return pe.is_in_on_state(self.getItem())

    def is_off(self):
        """
        Returns true if the contact is on; false otherwise.
        """
        return not self.is_on()

    def isOccupied(self, seconds_from_last_event=5 * 60):
        """
        Returns true if the TV is on; returns false otherwise.
        @override

        :rtype: bool
        """
        return self.is_on()
