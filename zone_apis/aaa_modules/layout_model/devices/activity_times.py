from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.device import Device

from aaa_modules import time_utilities


class ActivityTimes(Device):
    """
    Represents a virtual device that represent the activities within the zone.
    This device has no real backed OpenHab item.
    """

    def __init__(self, time_range_map):
        """
        Ctor

        :param dictionary time_range_map: a map from activity string to time range string.
            The supported activities are 'lunch', 'dinner', 'sleep', 'quiet',
            'wakeup'.
            A time range string can be a single or multiple
            ranges in the 24-hour format.
            Example: '10-12', or '6-9, 7-7, 8:30 - 14:45', or '19 - 8'
            (wrap around)
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, pe.create_string_item('ActivityTimesItem'))

        acceptable_keys = ['lunch', 'dinner', 'sleep', 'quiet', 'wakeup']
        for key in time_range_map.keys():
            if key not in acceptable_keys:
                raise ValueError('Invalid time range key {}'.format(key))

        self.timeRangeMap = time_range_map

    def is_lunch_time(self, epoch_seconds=None):
        return self._is_in_time_range('lunch', epoch_seconds)

    def is_dinner_time(self, epoch_seconds=None):
        return self._is_in_time_range('dinner', epoch_seconds)

    def is_quiet_time(self, epoch_seconds=None):
        return self._is_in_time_range('quiet', epoch_seconds)

    def is_sleep_time(self, epoch_seconds=None):
        return self._is_in_time_range('sleep', epoch_seconds)

    def is_wakeup_time(self, epoch_seconds=None):
        return self._is_in_time_range('wakeup', epoch_seconds)

    def _is_in_time_range(self, key, epoch_seconds):
        if key not in self.timeRangeMap.keys():
            return False

        time_range_string = self.timeRangeMap[key]
        return time_utilities.is_in_time_range(time_range_string, epoch_seconds)
