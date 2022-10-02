from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device


class DeferredAutoReportNotification(Device):
    """
    A data object containing the device name, and the deferred notification duration in hours.
    """

    def __init__(self, name_item, duration_in_hour_item):
        """
        Ctor

        :param NumberItem name_item: the device name to defer notification.
        :param NumberItem duration_in_hour_item: the deferred duration in hours.
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, name_item, [duration_in_hour_item])

        self._duration_in_hour_item = duration_in_hour_item

    @property
    def device_name(self) -> str:
        return pe.get_string_value(self.get_item())

    @property
    def deferred_duration_in_hours(self) -> float:
        return pe.get_number_value(self._duration_in_hour_item)

    @property
    def duration_in_hour_item_name(self) -> str:
        return pe.get_item_name(self._duration_in_hour_item)
