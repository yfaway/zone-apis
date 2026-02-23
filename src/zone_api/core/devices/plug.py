from zone_api.core.device import Device
from zone_api import platform_encapsulator as pe


class Plug(Device):
    """
    Represents a smart plug with optional power reading in Watt.
    """

    POWER_USAGE_THRESHOLD_IN_WATT = 30
    """
    The plug power usage threshold; if it is above this value, the zone containing this plug is considered to be
    occupied. The value is high to allow for always-on devices such as humidifier in the winter.
    """

    def __init__(self, plug_item, power_reading_item=None, always_on=False, reversed_security_control=False):
        """
        Ctor

        :param SwitchItem plug_item:
        :param NumberItem power_reading_item: the optional item to get the wattage reading
        :param Bool always_on: indicates if the plug should be on all the time
        :param Bool reversed_security_control: normally a plug is turned off when the house is armed. When this value is
            set to 'true' the plug is turned on when the house is armed, and off when the house is disarmed. This is
            suitable for indoor camera control.
        :raise ValueError: if plug_item is invalid
        """
        Device.__init__(self, plug_item)

        self.power_reading_item = power_reading_item
        self.always_on = always_on
        self.reverse_security_control = reversed_security_control

    def is_on(self):
        """
        :return: True if the partition is in alarm; False otherwise
        :rtype: bool
        """
        return pe.is_in_on_state(self.get_item())

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

    def is_always_on(self) -> bool:
        """ Returns true if this plug should not be turned off automatically. """
        return self.always_on

    def is_reversed(self) -> bool:
        """
        Returns true if this plug is controlled to turn on / off reversedly with respect to the security system.
        I.e. it is turned on when the house is armed and off when the house is disarmed.
        """
        return self.reverse_security_control

    def is_occupied(self, seconds_from_last_event=5 * 60):
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
            events.send_command(self.get_item_name(), "ON")

    def turn_off(self, events):
        """
        Turn off this plug.
        """
        if self.is_on():
            events.send_command(self.get_item_name(), "OFF")

    def __str__(self):
        """ @override """
        return u"{}{}{}".format(
            super(Plug, self).__str__(),
            ", always on" if self.is_always_on() else "",
            ", reversed control" if self.is_reversed() else "")
