from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.device import Device
from aaa_modules.layout_model.devices.vacation import Vacation


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


class EcobeeThermostat(Thermostat, Vacation):
    VACATION_EVENT_TYPE = 'vacation'

    def __init__(self, name_item, event_type_item):
        """
        Ctor

        :param StringItem name_item:
        :param StringItem event_type_item: the top most event type in the thermostat (i.e. #events[0].type).
        :raise ValueError: if any parameter is invalid
        """

        Thermostat.__init__(self, name_item)

        self.event_type_item = event_type_item

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

    def is_in_vacation(self):
        """ @Override """
        return pe.get_string_value(self.event_type_item) == EcobeeThermostat.VACATION_EVENT_TYPE

    def contains_item(self, item):
        """ Override. """
        return super(Thermostat, self).contains_item(item) or pe.get_item_name(self.event_type_item) == pe.get_item_name(item)

    def __str__(self):
        return f"{super(Thermostat, self).__str__()}, {pe.get_string_value(self.get_item())}, " \
               f"{pe.get_string_value(self.event_type_item)}"
