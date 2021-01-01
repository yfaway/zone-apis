class Action(object):
    """
    The base class for all zone actions. An action is invoked when an event is
    triggered (e.g. when a motion sensor is turned on).
    
    An action may rely on the states of one or more sensors in the zone.
    """

    def getRequiredDevices(self):
        """
        :return: list of devices that would generate the events
        :rtype: list(Device)
        """
        return self.devices

    def getRequiredEvents(self):
        """
        :return: list of triggering events this action process.
        :rtype: list(ZoneEvent)
        """
        return self.triggeringEvents

    def isApplicableToInternalZone(self):
        """
        :return: true if the action can be invoked on an internal zone.
        :rtype: bool
        """
        return self.internal

    def isApplicableToExternalZone(self):
        """
        :return: true if the action can be invoked on an external zone.
        :rtype: bool
        """
        return self.external

    def getApplicableLevels(self):
        """
        :return: list of applicable zone levels
        :rtype: list(int) 
        """
        return self.levels

    def getFirstDevice(self, eventInfo):
        """
        Returns the first applicable device that might have generated the
        event.
        """
        if len(self.getRequiredDevices()) == 0:
            return None
        else:
            devices = eventInfo.getZone().getDevicesByType(self.getRequiredDevices()[0])
            return devices[0]

    # noinspection PyUnusedLocal
    def onAction(self, event_info):
        """
        Subclass must override this method with its own handling.

        :param EventInfo event_info:
        :return: True if the event is processed; False otherwise.
        """
        return True


def action(devices=None, events=None, internal=True, external=False,
           levels=None):
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
        the empty list default value indicates applicale to all zone levels.
    """

    if levels is None:
        levels = []
    if events is None:
        events = []
    if devices is None:
        devices = []

    def action_decorator(clazz):
        def init(self, *args, **kwargs):
            clazz.__init__(self, *args, **kwargs)

            self.triggeringEvents = events
            self.devices = devices
            self.internal = internal
            self.external = external
            self.levels = levels

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

        if len(obj.getRequiredEvents()) > 0 \
                and not any(e == event_info.getEventType() for e in obj.getRequiredEvents()):

            return False
        elif len(obj.getRequiredDevices()) > 0 \
                and not any(len(zone.getDevicesByType(cls)) > 0 for cls in obj.getRequiredDevices()):

            return False
        elif zone.isInternal() and not obj.isApplicableToInternalZone():
            return False
        elif zone.isExternal() and not obj.isApplicableToExternalZone():
            return False
        elif len(obj.getApplicableLevels()) > 0 \
                and not any(zone.getLevel() == level for level in obj.getApplicableLevels()):

            return False
        else:
            return function(*args, **kwargs)

    return wrapper
