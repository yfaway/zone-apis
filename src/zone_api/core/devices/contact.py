from typing import Union

from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device
from zone_api.core.devices.security_aware_mixin import SecurityAwareMixin
from zone_api.models import ContactItem, SwitchItem


class Contact(SecurityAwareMixin, Device):
    """
    Represents a contact such as a door or windows.
    """

    def __init__(self, contact_item: Union[ContactItem, SwitchItem], security_tripped_item=None):
        """
        Ctor

        :param SwitchItem contact_item:
        :param SwitchItem security_tripped_item: optional item to indicate if this sensor triggered the security system.
        :raise ValueError: if any parameter is invalid
        """

        additional_devices = [security_tripped_item] if security_tripped_item is not None else None
        super().__init__(openhab_item=contact_item, additional_items=additional_devices,
                         security_tripped_item=security_tripped_item)

    def is_open(self):
        """
        Returns true if the contact is open; false otherwise.
        """
        if isinstance(self.get_item(), ContactItem):
            return self.get_item().is_open()
        elif isinstance(self.get_item(), SwitchItem):
            return self.get_item().is_on()

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
