import re


class Action(object):
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

    """
    The base class for all zone actions. An action is invoked when an event is
    triggered (e.g. when a motion sensor is turned on).
    
    An action may rely on the states of one or more sensors in the zone.
    """

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

    def get_first_device(self, event_info):
        """
        Returns the first applicable device that might have generated the
        event.
        """
        if len(self.get_required_devices()) == 0:
            return None
        else:
            devices = event_info.getZone().getDevicesByType(self.get_required_devices()[0])
            return devices[0]

    def must_be_unique_instance(self):
        """
        Returns true if the action must be an unique instance for each zone. This must be the case
        when the action is stateful.
        """
        return self._unique_instance

    def is_filtering_disabled(self):
        """ Returns true if no filtering shall be performed before the action is invoked. """
        return self._filtering_disabled

    def disable_filtering(self):
        self._filtering_disabled = True
        return self

    # noinspection PyUnusedLocal
    def onAction(self, event_info):
        """
        Subclass must override this method with its own handling.

        :param EventInfo event_info:
        :return: True if the event is processed; False otherwise.
        """
        return True


def action(devices=None, events=None, internal=True, external=False, levels=None,
           unique_instance=False, zone_name_pattern: str = None, external_events=None):
    """
    A decorator that accepts an action class and do the followings:
      - Create a subclass that extends the decorated class and Action.
      - Wrap the Action::onAction to perform various validations before
        invoking onAction.
    
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

        subclass = type(clazz.__name__, (clazz, Action), dict(__init__=init))
        subclass.onAction = validate(clazz.onAction)
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
        zone = event_info.getZone()

        if obj.is_filtering_disabled():
            return function(*args, **kwargs)

        if zone.has_action(obj):
            if len(obj.get_required_events()) > 0 \
                    and not any(e == event_info.getEventType() for e in obj.get_required_events()):

                return False
            elif len(obj.get_required_devices()) > 0 \
                    and not any(len(zone.getDevicesByType(cls)) > 0 for cls in obj.get_required_devices()):

                return False
            elif zone.isInternal() and not obj.is_applicable_to_internal_zone():
                return False
            elif zone.isExternal() and not obj.is_applicable_to_external_zone():
                return False
            elif len(obj.get_applicable_levels()) > 0 \
                    and not any(zone.getLevel() == level for level in obj.get_applicable_levels()):

                return False
            elif obj.get_applicable_zone_name_pattern() is not None:
                pattern = obj.get_applicable_zone_name_pattern()
                match = re.search(pattern, zone.getName())
                if not match:
                    return False
        else:  # event from other zones
            if event_info.getEventType() not in obj.get_external_events():
                return False

        return function(*args, **kwargs)

    return wrapper
