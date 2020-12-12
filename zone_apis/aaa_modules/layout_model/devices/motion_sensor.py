from aaa_modules import platform_encapsulator as PE
from aaa_modules.layout_model.device import Device


class MotionSensor(Device):
    """
    Represents a motion sensor; the underlying OpenHab object is a SwitchItem.
    """

    def __init__(self, switch_item, battery_powered=True):
        """
        :param SwitchItem switch_item:
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, switch_item, battery_powered)

    def is_on(self):
        """
        Returns true if the motion sensor's state is on; false otherwise.
        """
        return PE.is_in_on_state(self.getItem())

    def is_occupied(self, seconds_from_last_event=5 * 60):
        """
        Returns true if a motion event was triggered within the provided # of
        seconds. Returns false otherwise.
        @override

        :rtype: bool
        """
        if self.is_on():
            return True

        return self.wasRecentlyActivated(seconds_from_last_event)

    def on_triggered(self, event) -> None:
        """
        Handled the motion sensor ON event.
        """
        PE.log_error("*** triggered")

        self._update_last_activated_timestamp()
