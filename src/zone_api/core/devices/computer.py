from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device


class Computer(Device):
    """ Represents a computer. """

    def __init__(self, name: str, cpu_temperature_item=None, gpu_temperature_item=None, gpu_fan_speed_item=None,
                 always_on=False):
        """
        Ctor

        :param str name: the computer name.
        :param NumberItem cpu_temperature_item:
        :param NumberItem gpu_temperature_item:
        :param NumberItem gpu_fan_speed_item: fan speed in percentage.
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, pe.create_string_item(f'Computer: {name}'))

        self._name = name

        self._cpu_temperature_item = cpu_temperature_item
        self._gpu_temperature_item = gpu_temperature_item
        self._gpu_fan_speed_item = gpu_fan_speed_item
        self._always_on = always_on

    def is_always_on(self):
        return self._always_on

    def has_cpu_temperature(self):
        return self._cpu_temperature_item is not None

    def get_cpu_temperature(self) -> float:
        if self._cpu_temperature_item is None:
            raise ValueError("CPU temperature not available.")

        return pe.get_number_value(self._cpu_temperature_item)

    def has_gpu_temperature(self):
        return self._gpu_temperature_item is not None

    def get_gpu_temperature(self) -> float:
        if self._gpu_temperature_item is None:
            raise ValueError("GPU temperature not available.")

        return pe.get_number_value(self._gpu_temperature_item)

    def has_gpu_fan_speed(self):
        return self._gpu_fan_speed_item is not None

    def get_gpu_fan_speed(self) -> float:
        if self._gpu_fan_speed_item is None:
            raise ValueError("GPU Fan Speed not available.")

        return pe.get_number_value(self._gpu_fan_speed_item)

    def __str__(self):
        """ @override """
        return u"{}{}{}{}{}".format(
            super(Computer, self).__str__(),
            ", always on" if self._always_on else "",
            f", CPU Temp.: {self.get_cpu_temperature()} °C" if self.has_cpu_temperature() else "",
            f", GPU Temp.: {self.get_gpu_temperature()} °C" if self.has_gpu_temperature() else "",
            f", GPU Fan Speed: {self.get_gpu_fan_speed()} %" if self.has_gpu_fan_speed() else "")

    def contains_item(self, item):
        """ Override. """
        return super(Computer, self).contains_item(item) \
               or (self._cpu_temperature_item is not None and pe.get_item_name(
            self._cpu_temperature_item) == pe.get_item_name(item)) \
               or (self._gpu_temperature_item is not None and pe.get_item_name(
            self._gpu_temperature_item) == pe.get_item_name(item)) \
               or (self._gpu_fan_speed_item is not None and pe.get_item_name(
            self._gpu_fan_speed_item) == pe.get_item_name(item))
