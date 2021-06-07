import typing
from typing import Any

from zone_api.core.zone_event import ZoneEvent

if typing.TYPE_CHECKING:
    from zone_api.core.device import Device
    from zone_api.core.zone import Zone
    from zone_api.core.immutable_zone_manager import ImmutableZoneManager


class EventInfo(object):
    """
    Represent an event such as switch turned on, switch turned off, or
    motion triggered.
    """

    def __init__(self, event_type: ZoneEvent, item, zone: 'Zone', zone_manager: 'ImmutableZoneManager', events,
                 owning_zone: 'Zone' = None, device: 'Device' = None, custom_parameter: Any = None):
        """
        Creates a new EventInfo object.

        :param ZoneEvent event_type: the type of the event
        :param Item item: the OpenHab Item
        :param Zone zone: the zone where the event was triggered
        :param ImmutableZoneManager zone_manager:
        :param Any events: the OpenHab events object to dispatch actions
        :param Zone owning_zone: the zone that contains the item; None if it is the same at the
            dispatched zone.
        :param Device device: the device containing the item triggered the event.
        """

        if event_type is None:
            raise ValueError('eventType must not be None')

        # The item field isn't available for several event types.
        if event_type not in [ZoneEvent.STARTUP, ZoneEvent.DESTROY, ZoneEvent.TIMER]:
            if item is None:
                raise ValueError('item must not be None')

        if zone is None:
            raise ValueError('zone must not be None')

        if events is None:
            raise ValueError('events must not be None')

        self.eventType = event_type
        self.device = device
        self.item = item
        self.zone = zone
        self.zoneManager = zone_manager
        self.events = events
        self._owning_zone = owning_zone
        self._custom_parameter = custom_parameter

    def get_event_type(self) -> 'ZoneEvent':
        """ :rtype: ZoneEvent"""
        return self.eventType

    def get_device(self) -> 'Device':
        """ :rtype: Device"""
        return self.device

    def get_item(self):
        """ :rtype: Item"""
        return self.item

    def get_zone(self) -> 'Zone':
        """ :rtype: Zone"""
        return self.zone

    def get_zone_manager(self) -> 'ImmutableZoneManager':
        """ :rtype: ImmutableZoneManager"""
        return self.zoneManager

    def get_event_dispatcher(self):
        """ :rtype: Event"""
        return self.events

    def get_owning_zone(self) -> 'Zone':
        """ Returns the zone that contains the item; returns None if it is the same at the dispatched zone."""
        return self._owning_zone

    def get_custom_parameter(self):
        """ :rtype: Any"""
        return self._custom_parameter
