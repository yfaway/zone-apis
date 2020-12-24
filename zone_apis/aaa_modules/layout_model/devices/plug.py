from aaa_modules.layout_model.device import Device
from aaa_modules import platform_encapsulator as pe


class Plug(Device):
    """
    Represents a smart plug with optional power reading in Watt.
    """

    POWER_USAGE_THRESHOLD_IN_WATT = 8
    """
    The plug power usage threshold; if it is above this value, the zone 
    containing this plug is considered to be occupied.
    """

    def __init__(self, plug_item, power_reading_item=None):
        """
        Ctor

        :param SwitchItem plug_item:
        :param NumberItem power_reading_item: the optional item to get the wattage reading
        :raise ValueError: if plugItem is invalid
        """
        Device.__init__(self, plug_item)

        self.power_reading_item = power_reading_item

    def is_on(self):
        """
        :return: True if the partition is in alarm; False otherwise
        :rtype: bool
        """
        return pe.is_in_on_state(self.getItem())

    def has_power_reading(self):
        """
        :return: True if the plug can read the current wattage.
        :rtype: bool
        """
        return self.power_reading_item is not None

    def get_wattage(self):
        """
        :return: the current wattage of the plug
        :rtype: int or 0 if the plug has no power reading
        """
        if self.power_reading_item is None:
            raise ValueError("Plug has no power reading capability")

        return pe.get_number_value(self.power_reading_item)

    def isOccupied(self, seconds_from_last_event=5 * 60):
        """
        Returns True if the power reading is above the threshold.
        @override

        :rtype: bool
        """

        return self.has_power_reading() and self.get_wattage() > Plug.POWER_USAGE_THRESHOLD_IN_WATT

    def turn_on(self, events):
        """
        Turns on this plug, if it is not on yet.
        """
        if not self.is_on():
            events.send_command(self.getItemName(), "ON")

    def turn_off(self, events):
        """
        Turn off this plug.
        """
        if self.is_on():
            events.send_command(self.getItemName(), "OFF")
