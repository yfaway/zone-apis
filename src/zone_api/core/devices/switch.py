import time
from random import randint
from threading import Timer
from typing import List

from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device
from zone_api import time_utilities


class Switch(Device):
    """
    Represents a light or fan switch. Each switch contains an internal timer.
    When the switch is turned on, the timer is started. As the timer expires,
    the switch is turned off (if it is not off already). If the
    switch is turned off not by the timer, the timer is cancelled.
    """

    # The maximum duration between the last turned-off time and the current turned-on time, during which the
    # turned-off timer will be set to 1.5 times longer than the initial value. This simulates the scenario when the
    # user is relatively immobile and thus no motion event was triggered to renew the timer. Once the previous timer is
    # triggered and turn off the light, the user manually reaches out to turn on the light again. This indicates that
    # the user is in the middle of something and as such we will increase the timer duration.
    STICKY_SWITCH_DURATION_IN_SECS = 30

    # Related to STICKY_SWITCH_DURATION_IN_SECS, how long should the default timer duration be extended.
    EXTENDED_TIMER_DURATION_FACTOR = 1.5

    def __init__(self, switch_item, duration_in_minutes: float):
        """
        Ctor

        :param SwitchItem switch_item:
        :param int duration_in_minutes: how long the switch will be kept on
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, switch_item)

        self.lastOffTimestampInSeconds = -1

        self.duration_in_minutes = duration_in_minutes
        self.timer = None

    def _start_timer(self, events):
        """
        Creates and returns the timer to turn off the switch.
        """

        def turn_off_switch():
            zone = self.get_zone_manager().get_containing_zone(self)

            (occupied, device) = zone.is_occupied([Switch], 60)
            if not occupied:
                events.send_command(self.get_item_name(), "OFF")
                pe.log_debug("{}: turning off {}.".format(
                    zone.get_name(), self.get_item_name()))
            else:
                self.timer = Timer(self.duration_in_minutes * 60, turn_off_switch)
                self.timer.start()

                pe.log_debug("{}: {} is in use by {}.".format(
                    zone.get_name(), self.get_item_name(), device))

        self._cancel_timer()  # cancel the previous timer, if any.

        duration = self.duration_in_minutes * 60
        if (time.time() - self.get_last_off_timestamp_in_seconds()) <= Switch.STICKY_SWITCH_DURATION_IN_SECS:
            duration = duration * Switch.EXTENDED_TIMER_DURATION_FACTOR

        self.timer = Timer(duration, turn_off_switch)
        self.timer.start()

    def _cancel_timer(self):
        """
        Cancel the turn-off-switch timer.
        """
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
            self.timer = None

    def _is_timer_active(self):
        return self.timer is not None and self.timer.is_alive()

    def turn_on(self, events):
        """
        Turns on this light, if it is not on yet. In either case, the associated
        timer item is also turned on.
        """
        if self.is_on():  # already on, renew timer
            self._start_timer(events)
        else:
            events.send_command(self.get_item_name(), "ON")

    def turn_off(self, events):
        """
        Turn off this light.
        """
        if self.is_on():
            events.send_command(self.get_item_name(), "OFF")

        self._cancel_timer()

    def is_on(self):
        """
        Returns true if the switch is turned on; false otherwise.
        """
        return pe.is_in_on_state(self.get_item())

    def on_switch_turned_on(self, events, item_name):
        """
        Invoked when a switch on event is triggered. Note that a switch can be
        turned on through this class' turnOn method, or through the event bus, or
        manually by the user.
        The following actions are done:
        - the on timestamp is set;
        - the timer is started or renewed.

        :param events:
        :param str item_name: the name of the item triggering the event
        :return True: if itemName refers to this switch; False otherwise
        """
        is_processed = (self.get_item_name() == item_name)
        if is_processed:
            self._handle_common_on_action(events)

        return is_processed

    def on_switch_turned_off(self, events, item_name):
        """
        Invoked when a switch off event is triggered. Note that a switch can be
        turned off through this class' turnOff method, or through the event bus,
        or manually by the user.
        The following actions are done:
        - the timer is cancelled.

        :param scope.events events: 
        :param string item_name: the name of the item triggering the event
        :return: True if itemName refers to this switch; False otherwise
        """
        is_processed = (self.get_item_name() == item_name)
        if is_processed:
            self.lastOffTimestampInSeconds = time.time()
            self._cancel_timer()

        return is_processed

    def get_last_off_timestamp_in_seconds(self):
        """
        Returns the timestamp in epoch seconds the switch was last turned off.

        :return: -1 if the timestamp is not available, or an integer presenting\
        the epoch seconds
        """
        return self.lastOffTimestampInSeconds

    # Misc common things to do when a switch is turned on.
    def _handle_common_on_action(self, events):
        self._start_timer(events)  # start or renew timer

    def is_low_illuminance(self, current_illuminance):
        """ Always return False.  """
        return False

    def __str__(self):
        """ @override """
        return u"{}, duration: {} minutes".format(
            super(Switch, self).__str__(), self.duration_in_minutes)


class Light(Switch):
    """ Represents a regular light.  """

    def __init__(self, switch_item, duration_in_minutes: float, illuminance_level: int = None,
                 no_premature_turn_off_time_range: str = None):
        """
        :param int illuminance_level: the illuminance level in LUX unit. The \
            light should only be turned on if the light level is below this unit.
        :param str no_premature_turn_off_time_range: optional parameter to define \
            the time range when the light should not be turned off before its \
            expiry time.
        """
        Switch.__init__(self, switch_item, duration_in_minutes)
        self.illuminance_level = illuminance_level
        self.no_premature_turn_off_time_range = no_premature_turn_off_time_range

    def get_illuminance_threshold(self):
        """
        Returns the illuminance level in LUX unit. Returns None if not applicable.

        :rtype: int or None
        """
        return self.illuminance_level

    def is_low_illuminance(self, current_illuminance):
        """
        Returns False if this light has no illuminance threshold or if 
        current_illuminance is less than 0. Otherwise returns True if the
        current_illuminance is less than threshold.
        @override
        """
        if self.get_illuminance_threshold() is None:
            return False

        if current_illuminance < 0:  # current illuminance not available
            return False

        return current_illuminance < self.get_illuminance_threshold()

    def can_be_turned_off_by_adjacent_zone(self):
        """
        Returns True if this light can be turned off when the light of an
        adjacent zone is turned on.
        A False value might be desired if movement in the adjacent zone causes
        the light to be turned off unexpectedly too often.

        :rtype: bool
        """
        if self.no_premature_turn_off_time_range is None:
            return True

        if time_utilities.is_in_time_range(self.no_premature_turn_off_time_range):
            return False

        return True

    def is_occupied(self, seconds_from_last_event=5 * 60):
        """
        Returns True if the device is on.
        @override

        :rtype: bool
        """
        return self.is_on()

    def __str__(self):
        """ @override """
        return u"{}, illuminance: {}{}".format(
            super(Light, self).__str__(), self.illuminance_level,
            ", no premature turn-off time range: {}".format(self.no_premature_turn_off_time_range)
            if self.no_premature_turn_off_time_range is not None else "")


class ColorLight(Light):
    """ Represents a color bulb (modeled as a light switch).  """

    def __init__(self, switch_item, color_item, duration_in_minutes: float, illuminance_level: int = None,
                 no_premature_turn_off_time_range: str = None):
        """
        :param color_item: the OpenHab item to change the color.
        :param int illuminance_level: the illuminance level in LUX unit. The \
            light should only be turned on if the light level is below this unit.
        :param str no_premature_turn_off_time_range: optional parameter to define \
            the time range when the light should not be turned off before its \
            expiry time.
        """
        Light.__init__(self, switch_item, duration_in_minutes, illuminance_level, no_premature_turn_off_time_range)
        self._color_item = color_item

    def turn_on(self, events):
        super(ColorLight, self).turn_on(events)

        self.change_color([randint(0, 255), randint(0, 255), randint(0, 255)])

    def change_color(self, rgb_color: List[int]):
        """
        :param rgb_color: a list of 3 integers representing the R, B, and G values, range from 0 to 255.
        """
        pe.set_color_value(self._color_item, rgb_color)

    def __str__(self):
        """ @override """
        return u"{}, color item: {}".format(
            super(ColorLight, self).__str__(), pe.get_item_name(self._color_item))


class Fan(Switch):
    """ Represents a fan switch.  """

    def __init__(self, switch_item, duration_in_minutes):
        Switch.__init__(self, switch_item, duration_in_minutes)
