from zone_api import platform_encapsulator as pe


class SecurityAwareMixin:
    def __init__(self, security_tripped_item, **kwargs):
        """
        Creates a cooperative mixin that provides functionality related to the security system.

        :param SwitchItem security_tripped_item: item to indicate if this sensor triggered the security system.
        :raise ValueError: if any parameter is invalid
        """
        super().__init__(**kwargs)
        self._security_tripped_item = security_tripped_item

    def is_connected_to_security_system(self):
        """ Returns True if this device is part of a security system. """
        return self._security_tripped_item is not None

    def is_tripped(self):
        """ Returns True if this device causes the security system to go into alarm mode. """
        if not self.is_connected_to_security_system():
            return False

        return pe.is_in_on_state(self._security_tripped_item)

    def __str__(self):
        """ @override """
        return u"{}{}".format(
            super(SecurityAwareMixin, self).__str__(),
            ", connected w. security system" if self.is_connected_to_security_system() else ""
            ", tripped" if self.is_tripped() else "")
