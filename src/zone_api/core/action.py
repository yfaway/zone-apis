import re
from typing import Any

from zone_api import platform_encapsulator as pe
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent


class Action(object):
    """
    The base class for all zone actions. An action is invoked when an event is triggered (e.g. when
    a motion sensor is turned on).

    An action may rely on the states of one or more sensors in the zone.

    Here is the action life cycle:
      1. Object creation.
      2. Action::on_startup is invoked with ZoneEvent::STARTUP.
      3. Action::on_action is invoked when the specified event is triggered.
      4. Action::on_destroy is invoked with ZoneEvent::DESTROY.
    """

    def __init__(self):
        self._triggering_events = None
        self._external_events = None
        self._devices = None
        self._internal = None
        self._external = None
        self._levels = None
        self._unique_instance = False
        self._zone_name_pattern = None
        self._filtering_disabled = False
        self._priority = 10

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def on_action(self, event_info: EventInfo) -> bool:
        """
        Invoked when an event is triggered.
        Subclass must override this method with its own handling.

        :param EventInfo event_info:
        :return: True if the event is processed; False otherwise.
        """
        return True

    def on_startup(self, event_info: EventInfo):
        """
        Invoked when the system has been fully initialized, and the action is ready to accept event.
        Action should perform any initialization actions such as starting the timer here.
        """
        pass

    def on_destroy(self, event_info: EventInfo):
        """
        Invoked when the system is about to be shutdown.
        Action should perform any necessary destruction such as cancelling the timer here.
        """
        pass

    def get_containing_zone(self, zm):
        """
        :param ImmutableZoneManager zm:
        :return: the first zone containing this action or None.
        :rtype: Zone
        """
        for z in zm.get_zones():
            if z.has_action(self):
                return z

        return None

    def create_timer_event_info(self, event_info: EventInfo, custom_parameter: Any = None):
        """ Helper method to return the TIMER event info. """
        return EventInfo(ZoneEvent.TIMER, self.get_containing_zone(event_info.get_zone_manager()),
                         event_info.get_zone(), event_info.get_zone_manager(),
                         event_info.get_event_dispatcher(), None, None, custom_parameter)

    def get_required_devices(self):
        """
        :return: list of devices that would generate the events
        :rtype: list(Device)
        """
        return self._devices

    def get_required_events(self):
        """
        :return: list of triggering events this action processes. External events aren't filtered
            through the normal mechanism as they come from different zones.
        :rtype: list(ZoneEvent)
        """
        return self._triggering_events

    def get_external_events(self):
        """
        :return: list of external events that this action processes.
        """
        return self._external_events

    def is_applicable_to_internal_zone(self):
        """
        :return: true if the action can be invoked on an internal zone.
        :rtype: bool
        """
        return self._internal

    def is_applicable_to_external_zone(self):
        """
        :return: true if the action can be invoked on an external zone.
        :rtype: bool
        """
        return self._external

    def get_applicable_levels(self):
        """
        :return: list of applicable zone levels
        :rtype: list(int) 
        """
        return self._levels

    def get_applicable_zone_name_pattern(self):
        """
        :return: the zone name pattern that is applicable for this action.
        :rtype: str
        """
        return self._zone_name_pattern

    def must_be_unique_instance(self):
        """
        Returns true if the action must be an unique instance for each zone. This must be the case
        when the action is stateful.
        """
        return self._unique_instance

    def is_filtering_disabled(self):
        """ Returns true if no filtering shall be performed before the action is invoked. """
        return self._filtering_disabled

    def get_priority(self) -> int:
        """ Returns the specified priority order. Actions with lower order value is executed first. """
        return self._priority

    def disable_filtering(self):
        self._filtering_disabled = True
        return self

    def log_info(self, message: str):
        """ Log an info message with the action name prefix. """
        pe.log_info(f"{self.__class__.__name__}: {message}")

    def log_warning(self, message: str):
        """ Log a warning with the action name prefix. """
        pe.log_warning(f"{self.__class__.__name__}: {message}")

    def log_error(self, message: str):
        """ Log an error message with the action name prefix. """
        pe.log_error(f"{self.__class__.__name__}: {message}")


def action(devices=None, events=None, internal=True, external=False, levels=None,
           unique_instance=False, zone_name_pattern: str = None, external_events=None,
           priority: int = 10):
    """
    A decorator that accepts an action class and do the followings:
      - Create a subclass that extends the decorated class and Action.
      - Wrap the Action::on_action to perform various validations before
        invoking on_action.
    
    :param list(Device) devices: the list of devices the zone must have
        in order to invoke the action.
    :param list(ZoneEvent) events: the list of events for which the action
        will response to.
    :param boolean internal: if set, this action is only applicable for internal zone
    :param boolean external: if set, this action is only applicable for external zone
    :param list(int) levels: the zone levels that this action is applicable to.
        the empty list default value indicates that the action is applicable to all zone levels.
    :param boolean unique_instance: if set, do not share the same action instance across zones.
        This is the case when the action is stateful.
    :param str zone_name_pattern: if set, the zone name regular expression that is applicable to
        this action.
    :param list(ZoneEvent) external_events: the list of events from other zones that this action
        processes. These events won't be filtered using the same mechanism as the internal
        events as they come from other zones.
    :param int priority: the action priority with respect to other actions within the same zone.
        Actions with lower priority values are executed first.
    """

    if levels is None:
        levels = []
    if events is None:
        events = []
    if external_events is None:
        external_events = []
    if devices is None:
        devices = []

    def action_decorator(clazz):
        def init(self, *args, **kwargs):
            clazz.__init__(self, *args, **kwargs)

            self._triggering_events = events
            self._devices = devices
            self._internal = internal
            self._external = external
            self._levels = levels
            self._unique_instance = unique_instance
            self._zone_name_pattern = zone_name_pattern
            self._external_events = external_events
            self._filtering_disabled = False
            self._priority = priority

        subclass = type(clazz.__name__, (clazz, Action), dict(__init__=init))
        subclass.on_action = validate(clazz.on_action)
        return subclass

    return action_decorator


def validate(function):
    """
    Returns a function that validates the followings:
      - The generated event matched the action's applicable events.
      - The zone contains the expected device.
      - The zone's internal or external attributes matches the action's specification.
      - The zone's level matches the action's specification.
    """

    def wrapper(*args, **kwargs):
        obj = args[0]
        event_info = args[1]
        zone = event_info.get_zone()

        if obj.is_filtering_disabled() or event_info.get_event_type() == ZoneEvent.TIMER:
            return function(*args, **kwargs)

        if zone.contains_open_hab_item(event_info.get_item()):
            if len(obj.get_required_events()) > 0 \
                    and not any(e == event_info.get_event_type() for e in obj.get_required_events()):

                return False
            elif len(obj.get_required_devices()) > 0 \
                    and not any(len(zone.get_devices_by_type(cls)) > 0 for cls in obj.get_required_devices()):

                return False
            elif zone.is_internal() and not obj.is_applicable_to_internal_zone():
                return False
            elif zone.is_external() and not obj.is_applicable_to_external_zone():
                return False
            elif len(obj.get_applicable_levels()) > 0 \
                    and not any(zone.get_level() == level for level in obj.get_applicable_levels()):

                return False
            elif obj.get_applicable_zone_name_pattern() is not None:
                pattern = obj.get_applicable_zone_name_pattern()
                match = re.search(pattern, zone.get_name())
                if not match:
                    return False
        else:  # event from other zones
            if event_info.get_event_type() not in obj.get_external_events():
                return False

        return function(*args, **kwargs)

    return wrapper
