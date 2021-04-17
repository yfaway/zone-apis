
class Vacation:
    """
    An abstract class to indicate vacation status.
    This is not a device.
    """

    def is_in_vacation(self):
        """ Returns true if the house is in vacation mode. """
        raise NotImplementedError("Should have implemented this")
