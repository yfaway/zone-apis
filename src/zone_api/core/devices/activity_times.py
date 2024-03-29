from enum import unique, Enum

from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device
from zone_api import time_utilities


@unique
class ActivityType(Enum):
    """ A list of activity period types. """
    LUNCH = 'lunch'
    DINNER = 'dinner'
    SLEEP = 'sleep'
    QUIET = 'quiet'
    WAKE_UP = 'wakeup'
    AUTO_ARM_STAY = 'auto-arm-stay'
    TURN_OFF_PLUGS = 'turn-off-plugs'


class ActivityTimes(Device):
    """
    Represents a virtual device that represent the activities within the zone.
    This device has no real backed OpenHab item.
    """

    def __init__(self, time_range_map):
        """
        Ctor

        :param dictionary time_range_map: a map from activity ActivityType to time range string.
            A time range string can be a single or multiple
            ranges in the 24-hour format.
            Example: '10-12', or '6-9, 7-7, 8:30 - 14:45', or '19 - 8'
            (wrap around)
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, pe.create_string_item('ActivityTimesItem'))

        for key in time_range_map.keys():
            if isinstance(key, ActivityType):
                if key not in ActivityType:
                    raise ValueError('Invalid time range key {}'.format(key))
            else:
                raise TypeError('Invalid time range key {}'.format(key))

        self.timeRangeMap = time_range_map

    @property
    def number_of_activities(self) -> int:
        return len(self.timeRangeMap)

    def is_at_activity_time(self, activity_type: ActivityType, epoch_seconds=None):
        if activity_type == ActivityType.LUNCH:
            return self.is_lunch_time(epoch_seconds)
        elif activity_type == ActivityType.DINNER:
            return self.is_dinner_time(epoch_seconds)
        elif activity_type == ActivityType.SLEEP:
            return self.is_sleep_time(epoch_seconds)
        elif activity_type == ActivityType.QUIET:
            return self.is_quiet_time(epoch_seconds)
        elif activity_type == ActivityType.WAKE_UP:
            return self.is_wakeup_time(epoch_seconds)
        elif activity_type == ActivityType.AUTO_ARM_STAY:
            return self.is_auto_arm_stay_time(epoch_seconds)
        elif activity_type == ActivityType.TURN_OFF_PLUGS:
            return self.is_turn_off_plugs_time(epoch_seconds)
        else:
            raise ValueError(f"Invalid activity type {activity_type}")

    def is_lunch_time(self, epoch_seconds=None):
        return self._is_in_time_range(ActivityType.LUNCH, epoch_seconds)

    def is_dinner_time(self, epoch_seconds=None):
        return self._is_in_time_range(ActivityType.DINNER, epoch_seconds)

    def is_quiet_time(self, epoch_seconds=None):
        return self._is_in_time_range(ActivityType.QUIET, epoch_seconds)

    def is_sleep_time(self, epoch_seconds=None):
        return self._is_in_time_range(ActivityType.SLEEP, epoch_seconds)

    def is_wakeup_time(self, epoch_seconds=None):
        return self._is_in_time_range(ActivityType.WAKE_UP, epoch_seconds)

    def is_auto_arm_stay_time(self, epoch_seconds=None):
        return self._is_in_time_range(ActivityType.AUTO_ARM_STAY, epoch_seconds)

    def is_turn_off_plugs_time(self, epoch_seconds=None):
        return self._is_in_time_range(ActivityType.TURN_OFF_PLUGS, epoch_seconds)

    def _is_in_time_range(self, key, epoch_seconds):
        if key not in self.timeRangeMap.keys():
            return False

        time_range_string = self.timeRangeMap[key]
        return time_utilities.is_in_time_range(time_range_string, epoch_seconds)
