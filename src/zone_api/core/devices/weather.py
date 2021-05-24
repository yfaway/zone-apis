from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device


class Weather(Device):
    """
    Represents the outdoor weather condition. The minimum items required are the temperature, humidity, and
    condition. All other parameters are optional.
    """

    def __init__(self, temperature_item, humidity_item, condition_item, alert_item=None,
                 forecast_min_temperature_item=None, forecast_max_temperature_item=None):
        """
        Ctor

        :param NumberItem temperature_item:
        :param NumberItem humidity_item:
        :param StringItem condition_item:
        :param StringItem alert_item:
        :param NumberItem forecast_min_temperature_item:
        :param NumberItem forecast_max_temperature_item:
        :raise ValueError: if any parameter is invalid
        """

        Device.__init__(self, temperature_item, [humidity_item, condition_item, alert_item,
                                                 forecast_min_temperature_item, forecast_max_temperature_item])

        self._temperature_item = temperature_item
        self._humidity_item = humidity_item
        self._condition_item = condition_item
        self._alert_item = alert_item
        self._forecast_min_temperature_item = forecast_min_temperature_item
        self._forecast_max_temperature_item = forecast_max_temperature_item

    def get_temperature(self) -> float:
        return pe.get_number_value(self._temperature_item)

    def get_humidity(self) -> float:
        return pe.get_number_value(self._humidity_item)

    def get_condition(self) -> str:
        return pe.get_string_value(self._condition_item)

    def support_alert(self):
        """ Returns true if the alert information is available. """
        return self._alert_item is not None

    def get_alert(self) -> str:
        if not self.support_alert():
            raise ValueError("alert is not available.")

        return pe.get_string_value(self._alert_item)

    def support_forecast_min_temperature(self):
        return self._forecast_min_temperature_item is not None

    def get_forecast_min_temperature(self) -> float:
        if not self.support_forecast_min_temperature():
            raise ValueError("forecast_min_temperature is not available.")

        return pe.get_number_value(self._forecast_min_temperature_item)

    def support_forecast_max_temperature(self):
        return self._forecast_max_temperature_item is not None

    def get_forecast_max_temperature(self) -> float:
        if not self.support_forecast_max_temperature():
            raise ValueError("forecast_max_temperature is not available.")

        return pe.get_number_value(self._forecast_max_temperature_item)

    def __str__(self):
        """ @override """
        return u"{}{}{}{}{}{}{}".format(
            super(Weather, self).__str__(),
            f", Temp.: {self.get_temperature()}°C",
            f", Humidity: {self.get_humidity()}%",
            f", Condition: {self.get_condition()}",
            f", Alert: {self.get_alert()}" if (
                    self.support_alert() and self.get_alert() is not None and self.get_alert() != '') else "",
            f", Min. Temp.: {self.get_forecast_min_temperature()}°C" if self.support_forecast_min_temperature() else "",
            f", Max. Temp.: {self.get_forecast_max_temperature()}°C" if self.support_forecast_max_temperature() else "")
