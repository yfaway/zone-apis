from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device
from zone_api.core.devices.security_aware_mixin import SecurityAwareMixin


class MotionSensor(SecurityAwareMixin, Device):
    """
    Represents a motion sensor; the underlying OpenHab object is a SwitchItem.
    """

    def __init__(self, switch_item, battery_powered=True, can_trigger_switches=True, security_tripped_item=None):
        """
        :param SwitchItem switch_item:
        :param SwitchItem security_tripped_item: optional item to indicate if this sensor triggered the security system.
        :raise ValueError: if any parameter is invalid
        """
        additional_devices = [security_tripped_item] if security_tripped_item is not None else None
        super().__init__(openhab_item=switch_item, additional_items=additional_devices,
                         battery_powered=battery_powered, security_tripped_item=security_tripped_item)

        self._can_trigger_switches = can_trigger_switches
        self._security_tripped_item = security_tripped_item

    def is_on(self):
        """
        Returns true if the motion sensor's state is on; false otherwise.
        """
        return pe.is_in_on_state(self.get_item())

    def is_occupied(self, seconds_from_last_event=5 * 60):
        """
        Returns true if a motion event was triggered within the provided # of
        seconds. Returns false otherwise.
        @override

        :rtype: bool
        """
        if self.is_on():
            return True

        return self.was_recently_activated(seconds_from_last_event)

    def can_trigger_switches(self) -> bool:
        """
        Returns true if this motion sensor can turn on associated switches in the same zone.
        """
        return self._can_trigger_switches

    def __str__(self):
        """ @override """
        return u"{}{}".format(
            super(MotionSensor, self).__str__(),
            ", disable triggering switches" if not self.can_trigger_switches() else "")
