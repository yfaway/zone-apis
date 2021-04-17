from zone_api import platform_encapsulator as pe
from zone_api.core.devices.switch import Light
from zone_api import time_utilities


class Dimmer(Light):
    """
    Represents a light dimmer with the dim level value ranges from 1 to 100.
    """

    def __init__(self, switch_item, duration_in_minutes: int, dim_level: int = 5, time_ranges: str = None,
                 illuminance_level: int = None, no_premature_turn_off_time_range=None):
        """
        Constructs a new object.

        :raise ValueError: if any parameter is invalid
        """
        Light.__init__(self, switch_item, duration_in_minutes, illuminance_level, no_premature_turn_off_time_range)

        if dim_level < 0 or dim_level > 100:
            raise ValueError('dimLevel must be between 0 and 100 inclusive')

        time_utilities.string_to_time_range_lists(time_ranges)  # validate

        self.dim_level = dim_level
        self.time_ranges = time_ranges

    def turn_on(self, events):
        """
        Turn on this light if it is not on yet.
        If the light is dimmable, and if the current time falls into the
        specified time ranges, it will be dimmed; otherwise it is turned on at
        100%. The associated timer item is also turned on.

        @override
        """
        if not pe.is_in_on_state(self.get_item()):
            if time_utilities.is_in_time_range(self.time_ranges):
                events.send_command(self.get_item_name(),
                                    str(self.dim_level))
            else:
                events.send_command(self.get_item_name(), "100")

        self._handle_common_on_action(events)

    def is_on(self):
        """
        Returns true if the dimmer is turned on; false otherwise.

        @override
        """
        return pe.get_dimmer_percentage(self.get_item()) > 0

    def __str__(self):
        """
        @override
        """
        return u"{}, dimLevel: {}, timeRanges: {}".format(
            super(Dimmer, self).__str__(), self.dim_level, self.time_ranges)
