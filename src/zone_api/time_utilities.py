"""
Utility class containing a set of time related functions.
"""

import time


def is_in_time_range(time_ranges_string, epoch_seconds=None):
    """
    Determines if the current time is in the timeRange string.

    :param str time_ranges_string: one or multiple time range in 24-hour format.\
        Example: '10-12', or '6-9, 7-7, 8:30 - 14:45', or '19 - 8' (wrap around)
    :param int epoch_seconds: seconds since epoch, optional
    :rtype: boolean
    :raise: ValueError if the time range string is invalid
    """

    if time_ranges_string is None or 0 == len(time_ranges_string):
        raise ValueError('Must have at least one time range.')

    time_struct = time.localtime(epoch_seconds)
    hour = time_struct[3]
    minute = time_struct[4]

    for time_range in string_to_time_range_lists(time_ranges_string):
        start_hour, start_minute, end_hour, end_minute = time_range
        if start_hour <= end_hour:
            if hour < start_hour:
                continue
        else:  # wrap around scenario
            pass

        if hour == start_hour and minute < start_minute:
            continue

        if end_minute == 0:
            if start_hour <= end_hour:
                if hour >= end_hour:
                    continue
            else:  # wrap around
                if (hour < start_hour or hour > 23) and (hour < 0 or hour > end_hour):
                    continue
        else:  # minutes are > 0
            if hour > end_hour or minute > end_minute:
                continue

        return True

    return False


def string_to_time_range_lists(time_ranges_string):
    """
    Return a list of time ranges. Each list item is itself a list of 4 elements:
    startTime, startMinute, endTime, endMinute.

    :rtype: list
    :raise: ValueError if the time range string is invalid
    """
    if time_ranges_string is None or 0 == len(time_ranges_string):
        raise ValueError('Must have at least one time range.')

    time_ranges = []
    pairs = time_ranges_string.split(',')
    for pair in pairs:
        times = pair.split('-')
        if 1 == len(times):
            hour = int(times[0])
            if hour < 0 or hour > 23:
                raise ValueError('Hour must be between 0 and 23 inclusive.')
            time_ranges.append([int(hour), 0, int(hour), 59])
        elif 2 == len(times):
            this_range = []

            def parse_hour_and_minute(time_string):
                hour_minute = time_string.split(':')
                inner_hour = int(hour_minute[0])
                if inner_hour < 0 or inner_hour > 23:
                    raise ValueError('Hour must be between 0 and 23 inclusive.')

                if 1 == len(hour_minute):
                    return [int(inner_hour), 0]  # 0 minute
                elif 2 == len(hour_minute):
                    minute = int(hour_minute[1])
                    if minute < 0 or minute > 59:
                        raise ValueError('Minute must be between 0 and 59 inclusive.')
                    return [inner_hour, minute]
                else:
                    raise ValueError('Must be in format "HH" or "HH:MM".')

            this_range += parse_hour_and_minute(times[0])
            this_range += parse_hour_and_minute(times[1])

            time_ranges.append(this_range)
        else:
            raise ValueError('Must have either one or two time values.')

    return time_ranges
