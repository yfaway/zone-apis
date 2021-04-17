from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device


class NetworkPresence(Device):
    """
    Represents a network device. An ON state indicates that the device is
    connected to the local network and thus imply someone is present in the
    zone.
    """

    def __init__(self, switch_item):
        """
        :param SwitchItem switch_item:
        :raise ValueError: if any parameter is invalid
        """

        Device.__init__(self, switch_item)

    def is_presence(self):
        """
        Returns True if the device is connected to the local network; False
        otherwise.
        """

        return pe.is_in_on_state(self.get_item())

    def is_occupied(self, seconds_from_last_event=5 * 60):
        """
        Returns True if the device is on.
        @override

        :rtype: bool
        """
        return self.is_presence() or self.was_recently_activated(seconds_from_last_event)
