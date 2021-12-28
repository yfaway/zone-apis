from enum import Enum, unique

from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device


@unique
class AlarmState(Enum):
    """ An enum of possible alarm states."""
    UNARMED = 0
    """ The value for the unarmed state.  """

    ARM_AWAY = 1
    """ The value for the arm away state.  """

    ARM_STAY = 2
    """ The value for the arm stay state.  """


class AlarmPartition(Device):
    """
    Represents a security control. Exposes methods to arm the security system,
    and provide the alarm status.

    The current implementation is for DSC Alarm system.

    @see http://forum.eyez-on.com/FORUM/download/file.php?id=223&sid=e146abb17dbccca14f19d6b50cbe8379o
    @see https://cms.dsc.com/media/documents/user-manuals/pc1616/PC1616-1832-1864_UM_ENG_V4-7_R001.pdf
    """

    def __init__(self, alarm_status_item, arm_mode_item, send_command_item=None):
        """
        Ctor

        :param SwitchItem alarm_status_item: the item to indicate if the system is in alarm
        :param NumberItem arm_mode_item: the item to set the arming/disarming mode
        :param StringItem send_command_item: the item to send DSC commands.
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, alarm_status_item, [arm_mode_item, send_command_item])

        if arm_mode_item is None:
            raise ValueError('armModeItem must not be None')

        self.arm_mode_item = arm_mode_item
        self.send_command_item = send_command_item

    def is_in_alarm(self):
        """
        :return: True if the partition is in alarm; False otherwise
        :rtype: bool
        """
        return pe.is_in_on_state(self.get_item())

    def get_arm_mode(self) -> AlarmState:
        """
        :return: one of STATE_UNARMED, STATE_ARM_AWAY, STATE_ARM_STAY
        :rtype: int
        """
        return AlarmState(pe.get_number_value(self.arm_mode_item))

    def is_armed_away(self):
        """
        :rtype: boolean
        """
        return AlarmState.ARM_AWAY == self.get_arm_mode()

    def is_armed_stay(self):
        """
        :rtype: boolean
        """
        return AlarmState.ARM_STAY == self.get_arm_mode()

    def is_unarmed(self):
        """
        :rtype: boolean
        """
        return AlarmState.UNARMED == self.get_arm_mode()

    def arm_away(self, events):
        """
        Arm-away the partition.

        :param events:
        """
        events.send_command(pe.get_item_name(self.arm_mode_item), str(AlarmState.ARM_AWAY.value))

    def arm_stay(self, events):
        """
        Arm-stay the partition.

        :param events:
        """
        events.send_command(pe.get_item_name(self.arm_mode_item), str(AlarmState.ARM_STAY.value))

    def disarm(self, events):
        """
        Disarm the partition.

        :param events:
        """
        events.send_command(pe.get_item_name(self.arm_mode_item), str(AlarmState.UNARMED.value))

    def trigger_fire_alarm(self, events):
        """
        Trigger a fire alarm. For the DSC board, a restore event will be sent immediately. This is a known
        limitation.
        """
        events.send_command(pe.get_item_name(self.send_command_item), "060,1")

    def trigger_ambulance_alarm(self, events):
        """ Trigger a ambulance alarm (may not be supported by the panel). """
        events.send_command(pe.get_item_name(self.send_command_item), "060,2")

    def trigger_police_alarm(self, events):
        """ Trigger a ambulance alarm (may not be supported by the panel). """
        events.send_command(pe.get_item_name(self.send_command_item), "060,3")

    def get_arm_mode_item(self):
        return self.arm_mode_item

    def __str__(self):
        """
        @override
        """
        return u"{}, armMode: {}".format(
            super(AlarmPartition, self).__str__(), self.get_arm_mode().name)
