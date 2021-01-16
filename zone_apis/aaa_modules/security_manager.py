from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition, AlarmState
from aaa_modules.layout_model.immutable_zone_manager import ImmutableZoneManager

"""
Provide quick access to the alarm partition of the zones.
"""


def is_armed_away(zm: ImmutableZoneManager):
    """
    :return: True if at least one zone is armed-away
    """
    security_partitions = zm.get_devices_by_type(AlarmPartition)
    if len(security_partitions) > 0:
        if AlarmState.ARM_AWAY == security_partitions[0].get_arm_mode():
            return True

    return False


def is_armed_stay(zm: ImmutableZoneManager):
    """
    :return: True if at least one zone is armed-stay
    """
    security_partitions = zm.get_devices_by_type(AlarmPartition)
    if len(security_partitions) > 0:
        if AlarmState.ARM_STAY == security_partitions[0].get_arm_mode():
            return True

    return False
