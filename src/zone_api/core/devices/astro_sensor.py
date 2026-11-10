from zone_api.core.device import Device


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
            value = self.get_item().get_value()

        return any(s == value for s in self.LIGHT_ON_TIMES)

    def is_bed_time(self, value=None):
        """
        Returns True if it is bed time; returns False otherwise.

        :param str value: the current time period. if is None, retrieve the value from the item.
        :rtype: bool
        """
        if value is None:
            value = self.get_item().get_value()

        return value == self.BED_TIME

    def current_period(self) -> str:
        return self.get_item().get_value()

    def _set_current_period(self, value: str) -> None:
        """
        Sets the current period of the day. This method is meant for an internal action, and shall not be invoked
        in the public context.
        """
        self.get_item().set_value(value)

    def __str__(self):
        """
        @override
        """
        return u"{}, {}".format(super(AstroSensor, self).__str__(), self.current_period())