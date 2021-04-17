from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device


class Contact(Device):
    """
    Represents a contact such as a door or windows.
    """

    def __init__(self, contact_item):
        """
        Ctor

        :param SwitchItem contact_item:
        :raise ValueError: if any parameter is invalid
        """

        Device.__init__(self, contact_item)

    def is_open(self):
        """
        Returns true if the contact is open; false otherwise.
        """
        return pe.is_in_open_state(self.get_item()) or pe.is_in_on_state(self.get_item())

    def is_closed(self):
        """
        Returns true if the contact is closed; false otherwise.
        """
        return not self.is_open()


class Door(Contact):
    """ Represents a door. """
    pass


class GarageDoor(Door):
    """ Represents a garage door. """
    pass


class Window(Contact):
    """ Represents a window. """
    pass
