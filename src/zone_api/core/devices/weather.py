from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device


class Weather(Device):
    """ Represents the outdoor weather condition. """

    def __init__(self, temperature_item, humidity_item, condition_item, alert_item):
        """
        Ctor

        :param NumberItem temperature_item:
        :param NumberItem humidity_item:
        :param StringItem condition_item:
        :param StringItem alert_item:
        :raise ValueError: if any parameter is invalid
        """

        Device.__init__(self, temperature_item, [humidity_item, condition_item, alert_item])

        self._temperature_item = temperature_item
        self._humidity_item = humidity_item
        self._condition_item = condition_item
        self._alert_item = alert_item

    def get_temperature(self) -> float:
        return pe.get_number_value(self._temperature_item)

    def get_humidity(self) -> float:
        return pe.get_number_value(self._humidity_item)

    def get_condition(self) -> str:
        return pe.get_string_value(self._condition_item)

    def get_alert(self) -> str:
        return pe.get_string_value(self._alert_item)

    def __str__(self):
        """ @override """
        return u"{}{}{}{}".format(
            super(Weather, self).__str__(),
            f", Temperature: {self.get_temperature()}°C",
            f", Humidity: {self.get_humidity()}%",
            f", Condition: {self.get_condition()}",
            f", Alert: {self.get_alert()}" if (self.get_alert() is not None and self.get_alert() != '') else "")
