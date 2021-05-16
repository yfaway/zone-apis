from zone_api.core.device import Device
from zone_api import platform_encapsulator as pe


class GasSensor(Device):
    """
    Represents a generic gas sensor.
    """

    def __init__(self, value_item, state_item, battery_powered=False, wifi=True, auto_report=True):
        """
        Ctor

        :param NumberItem value_item: the item to get the value reading
        :param SwitchItem state_item: the item to get the state reading
        :param bool battery_powered: indicates if the device is powered by battery.
        :param bool wifi: indicate if the sensor communicates by WI-FI
        :param bool auto_report: indicate if the sensor reports periodically
        :raise ValueError: if value_item is invalid
        """
        Device.__init__(self, value_item, [state_item], battery_powered, wifi, auto_report)

        if state_item is None:
            raise ValueError('state_item must not be None')

        self._state_item = state_item

    def get_value(self):
        """
        :return: the current sensor value.
        :rtype: int
        """
        return pe.get_number_value(self.get_item())

    def is_triggered(self):
        """
        :return: true if the gas sensor has detected a high level of
             concentration
        :rtype: bool
        """
        return pe.is_in_on_state(self._state_item)

    def reset_value_states(self):
        """ Override. """
        pe.set_number_value(self.get_item(), -1)
        pe.set_switch_state(self._state_item, False)


class Co2GasSensor(GasSensor):
    """ Represents a CO2 sensor.  """

    def __init__(self, value_item, state_item):
        GasSensor.__init__(self, value_item, state_item)


class NaturalGasSensor(GasSensor):
    """ Represents a natural gas sensor.  """

    def __init__(self, value_item, state_item):
        GasSensor.__init__(self, value_item, state_item)


class SmokeSensor(GasSensor):
    """ Represents a smoke sensor.  """

    def __init__(self, value_item, state_item):
        GasSensor.__init__(self, value_item, state_item)
