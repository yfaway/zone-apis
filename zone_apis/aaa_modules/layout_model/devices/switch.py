import time
from threading import Timer

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.device import Device
from aaa_modules import time_utilities


class Switch(Device):
    """
    Represents a light or fan switch. Each switch contains an internal timer.
    When the switch is turned on, the timer is started. As the timer expires,
    the switch is turned off (if it is not off already). If the
    switch is turned off not by the timer, the timer is cancelled.
    """

    def __init__(self, switch_item, duration_in_minutes: float,
                 disable_triggering_from_motion_sensor: bool = False):
        """
        Ctor

        :param SwitchItem switch_item:
        :param int duration_in_minutes: how long the switch will be kept on
        :param bool disable_triggering_from_motion_sensor: a flag to indicate whether \
            the switch should be turned on when motion sensor is triggered.\
            There is no logic associate with this value in this class; it is \
            used by external classes through the getter.
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, switch_item)

        self.disable_triggering_from_motion_sensor = disable_triggering_from_motion_sensor
        self.lastOffTimestampInSeconds = -1

        self.duration_in_minutes = duration_in_minutes
        self.timer = None

    def _start_timer(self, events):
        """
        Creates and returns the timer to turn off the switch.
        """

        def turn_off_switch():
            zone = self.getZoneManager().get_containing_zone(self)

            (occupied, device) = zone.isOccupied([Fan, Light], 60)
            if not occupied:
                events.send_command(self.getItemName(), "OFF")
                pe.log_debug("{}: turning off {}.".format(
                    zone.getName(), self.getItemName()))
            else:
                self.timer = Timer(self.duration_in_minutes * 60, turn_off_switch)
                self.timer.start()

                pe.log_debug("{}: {} is in use by {}.".format(
                    zone.getName(), self.getItemName(), device))

        self._cancel_timer()  # cancel the previous timer, if any.

        self.timer = Timer(self.duration_in_minutes * 60, turn_off_switch)
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

    def turnOn(self, events):
        """
        Turns on this light, if it is not on yet. In either case, the associated
        timer item is also turned on.
        """
        if self.isOn():  # already on, renew timer
            self._start_timer(events)
        else:
            events.send_command(self.getItemName(), "ON")

    def turnOff(self, events):
        """
        Turn off this light.
        """
        if self.isOn():
            events.send_command(self.getItemName(), "OFF")

        self._cancel_timer()

    def isOn(self):
        """
        Returns true if the switch is turned on; false otherwise.
        """
        return pe.is_in_on_state(self.getItem())

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
        isProcessed = (self.getItemName() == item_name)
        if isProcessed:
            self._handle_common_on_action(events)

        return isProcessed

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
        is_processed = (self.getItemName() == item_name)
        if is_processed:
            self.lastOffTimestampInSeconds = time.time()
            self._cancel_timer()

        return is_processed

    def getLastOffTimestampInSeconds(self):
        """
        Returns the timestamp in epoch seconds the switch was last turned off.

        :return: -1 if the timestamp is not available, or an integer presenting\
        the epoch seconds
        """
        return self.lastOffTimestampInSeconds

    def canBeTriggeredByMotionSensor(self):
        """
        Returns True if this switch can be turned on when a motion sensor is
        triggered.
        A False value might be desired if two switches share the same motion
        sensor, and only one switch shall be turned on when the motion sensor is
        triggered.

        :rtype: bool
        """
        return not self.disable_triggering_from_motion_sensor

    # Misc common things to do when a switch is turned on.
    def _handle_common_on_action(self, events):
        self.lastLightOnSecondSinceEpoch = time.time()

        self._start_timer(events)  # start or renew timer

    def isLowIlluminance(self, current_illuminance):
        """ Always return False.  """
        return False

    def __str__(self):
        """ @override """
        return u"{}, duration: {} mins{}".format(
            super(Switch, self).__str__(), self.duration_in_minutes,
            ", disable triggering by motion" if self.disable_triggering_from_motion_sensor else "")


class Light(Switch):
    """ Represents a regular light.  """

    def __init__(self, switch_item, duration_in_minutes: float, illuminance_level: int = None,
                 disable_triggering_from_motion_sensor=False,
                 no_premature_turn_off_time_range: str = None):
        """
        :param int illuminance_level: the illuminance level in LUX unit. The \
            light should only be turned on if the light level is below this unit.
        :param str no_premature_turn_off_time_range: optional parameter to define \
            the time range when the light should not be turned off before its \
            expiry time.
        """
        Switch.__init__(self, switch_item, duration_in_minutes,
                        disable_triggering_from_motion_sensor)
        self.illuminance_level = illuminance_level
        self.no_premature_turn_off_time_range = no_premature_turn_off_time_range

    def getIlluminanceThreshold(self):
        """
        Returns the illuminance level in LUX unit. Returns None if not applicable.

        :rtype: int or None
        """
        return self.illuminance_level

    def isLowIlluminance(self, current_illuminance):
        """
        Returns False if this light has no illuminance threshold or if 
        current_illuminance is less than 0. Otherwise returns True if the
        current_illuminance is less than threshold.
        @override
        """
        if self.getIlluminanceThreshold() is None:
            return False

        if current_illuminance < 0:  # current illuminance not available
            return False

        return current_illuminance < self.getIlluminanceThreshold()

    def canBeTurnedOffByAdjacentZone(self):
        """
        Returns True if this light can be turned off when the light of an
        adjacent zone is turned on.
        A False value might be desired if movement in the adjacent zone causes
        the light to be turned off unexpectedly too often.

        :rtype: bool
        """
        if self.no_premature_turn_off_time_range is None:
            return True

        if time_utilities.isInTimeRange(self.no_premature_turn_off_time_range):
            return False

        return True

    def isOccupied(self, seconds_from_last_event=5 * 60):
        """
        Returns True if the device is on.
        @override

        :rtype: bool
        """
        return self.isOn()

    def __str__(self):
        """
        @override
        """
        return u"{}, illuminance: {}{}".format(
            super(Light, self).__str__(), self.illuminance_level,
            ", no premature turn-off time range: {}".format(self.no_premature_turn_off_time_range)
            if self.no_premature_turn_off_time_range is not None else "")


class Fan(Switch):
    """ Represents a fan switch.  """

    def __init__(self, switch_item, duration_in_minutes):
        Switch.__init__(self, switch_item, duration_in_minutes)
