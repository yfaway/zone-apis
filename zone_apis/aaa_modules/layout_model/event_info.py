class EventInfo(object):
    """
    Represent an event such as switch turned on, switch turned off, or
    motion triggered.
    """

    def __init__(self, event_type, item, zone, zone_manager, events):
        """
        Creates a new EventInfo object.

        :param ZoneEvent event_type: the type of the event
        :param Item item: the OpenHab Item
        :param Zone zone: the zone where the event was triggered
        :param ImmutableZoneManager zone_manager:
        :param scope.events events: the OpenHab events object to dispatch actions
        """

        if event_type is None:
            raise ValueError('eventType must not be None')

        if item is None:
            raise ValueError('item must not be None')

        if zone is None:
            raise ValueError('zone must not be None')

        if events is None:
            raise ValueError('events must not be None')

        self.eventType = event_type
        self.item = item
        self.zone = zone
        self.zoneManager = zone_manager
        self.events = events

    def getEventType(self):
        """ :rtype: ZoneEvent"""
        return self.eventType

    def getItem(self):
        """ :rtype: Item"""
        return self.item

    def getZone(self):
        """ :rtype: Zone"""
        return self.zone

    def getZoneManager(self):
        """ :rtype: ImmutableZoneManager"""
        return self.zoneManager

    def getEventDispatcher(self):
        """ :rtype: Event"""
        return self.events
