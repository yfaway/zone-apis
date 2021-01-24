from typing import Union

from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition, AlarmState
from aaa_modules.layout_model.immutable_zone_manager import ImmutableZoneManager

"""
Provide quick access to the alarm partition of the zones.
"""


def is_armed_away(zm: ImmutableZoneManager):
    """
    :return: True if at least one zone is armed-away
    """
    partition = _get_partition(zm)
    if partition is not None:
        return AlarmState.ARM_AWAY == partition.get_arm_mode()

    return False


def is_armed_stay(zm: ImmutableZoneManager):
    """
    :return: True if at least one zone is armed-stay
    """
    partition = _get_partition(zm)
    if partition is not None:
        return AlarmState.ARM_STAY == partition.get_arm_mode()

    return False


def is_unarmed(zm: ImmutableZoneManager):
    """
    :return: True if at least one zone is unarmed.
    """
    partition = _get_partition(zm)
    if partition is not None:
        return AlarmState.UNARMED == partition.get_arm_mode()

    return False


def arm_away(zm: ImmutableZoneManager, events):
    """ Arms the security system in 'away' mode. """
    partition = _get_partition(zm)
    if partition is None:
        raise ValueError('Missing security partition.')

    partition.arm_away(events)


def arm_stay(zm: ImmutableZoneManager, events):
    """ Arms the security system in 'stay' mode. """
    partition = _get_partition(zm)
    if partition is None:
        raise ValueError('Missing security partition.')

    partition.arm_stay(events)


def disarm(zm: ImmutableZoneManager, events):
    """ Disarms the security system. """
    partition = _get_partition(zm)
    if partition is None:
        raise ValueError('Missing security partition.')

    partition.disarm(events)


def _get_partition(zm: ImmutableZoneManager) -> Union[AlarmPartition, None]:
    security_partitions = zm.get_devices_by_type(AlarmPartition)
    if len(security_partitions) > 0:
        return security_partitions[0]
    else:
        return None
