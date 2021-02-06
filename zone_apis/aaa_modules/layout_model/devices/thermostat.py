from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.device import Device


class Thermostat(Device):
    """ Represents a thermostat. """

    def __init__(self, name_item):
        """
        Ctor

        :param StringItem name_item:
        :raise ValueError: if any parameter is invalid
        """

        Device.__init__(self, name_item)

    def set_away_mode(self):
        """ Change the thermostat to the AWAY mode. """
        pass

    def resume(self):
        """ Resumes the thermostat to the regular schedule. """
        pass


class EcobeeThermostat(Thermostat):
    # noinspection PyMethodMayBeStatic
    def set_away_mode(self):
        """
        Change the thermostat to the AWAY mode.
        @Override
        """
        pe.change_ecobee_thermostat_hold_mode('away')

    # noinspection PyMethodMayBeStatic
    def resume(self):
        """
        Resumes the thermostat to the regular schedule.
        @Override
        """
        pe.resume_ecobee_thermostat_program()
