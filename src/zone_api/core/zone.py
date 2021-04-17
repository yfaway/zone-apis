from enum import Enum, unique
from typing import List, Union

from zone_api.core.action import Action
from zone_api.core.event_info import EventInfo
from zone_api.core.device import Device

from zone_api.core.devices.illuminance_sensor import IlluminanceSensor
from zone_api.core.devices.switch import Light, Switch
from zone_api.core.neighbor import Neighbor

from zone_api import platform_encapsulator as pe
from zone_api.core.zone_event import ZoneEvent


@unique
class Level(Enum):
    """ An enum of the vertical levels."""

    UNDEFINED = "UD"  #: Undefined
    BASEMENT = "BM"  #: The basement
    FIRST_FLOOR = "FF"  #: The first floor
    SECOND_FLOOR = "SF"  #: The second floor
    THIRD_FLOOR = "TF"  #: The third floor
    VIRTUAL = "VT"  #: The third floor


class Zone:
    """
    Represent a zone such as a room, foyer, porch, or lobby. 
    Each zone holds a number of devices/sensors such as switches, motion sensors,
    or temperature sensors.

    A zone might have zero, one or multiple adjacent zones. The adjacent zones
    can be further classified into closed space (i.e. a wall exists between the
    two zones, open space, open space slave (the neighbor is a less important
    zone), and open space master. This layout-like structure is useful for
    certain scenario such as light control.

    Each zone instance is IMMUTABLE. The various add/remove methods return a new
    Zone object. Note however that the OpenHab item underlying each
    device/sensor is not (the state changes).  See :meth:`add_device`,
    :meth:`remove_device`, :meth:`add_neighbor()`

    The zone itself doesn't know how to operate a device/sensor. The sensors
    themselves (all sensors derive from Device class) exposes the possible
    operations. Generally, the zone needs not know about the exact types of 
    sensors it contains. However, controlling the light is a very common case
    for home automation; thus it does references to several virtual/physical
    sensors to determine the astro time, the illuminance, and the motion sensor.  
    See :meth:`get_devices()`, :meth:`get_devices_by_type()`.

    There are two sets of operation on each zone:
      1. Active operations such as turn on a light/fan in a zone. These are\
         represented by common functions such as #turnOnLights(),\
         #turnOffLights(); and
      2. Passive operations triggered by events such onTimerExpired(),\
         onSwitchTurnedOn(), and so on.
    The passive triggering is needed because the interaction with the devices or
    sensors might happen outside the interface exposed by this class. It could
    be a manually action on the switch by the user, or a direct send command 
    through the OpenHab event bus.
    All the onXxx methods accept two parameters: the core.jsr223.scope.events
    object and the string itemName. The zone will perform appropriate actions
    for each of these events. For example, a motion event will turn on the light
    if it is dark or if it is evening time; a timer expiry event will turn off
    the associated light if it is currently on.

    @Immutable (the Zone object only)
    """

    @classmethod
    def create_second_floor_zone(cls, name):
        """
        Creates an internal second floor zone with the given name.
        :rtype: Zone
        """
        params = {'name': name, 'level': Level.SECOND_FLOOR}
        return Zone(**params)

    @classmethod
    def create_first_floor_zone(cls, name):
        """
        Creates an internal first floor zone with the given name.
        :rtype: Zone
        """
        params = {'name': name, 'level': Level.FIRST_FLOOR}
        return Zone(**params)

    @classmethod
    def create_external_zone(cls, name, level=Level.FIRST_FLOOR):
        """
        Creates an external zone with the given name.
        :rtype: Zone
        """
        params = {'name': name, 'level': level, 'external': True}
        return Zone(**params)

    def __init__(self, name, devices: List[Device] = None, level=Level.UNDEFINED,
                 neighbors: List[Neighbor] = None, actions=None, external=False,
                 display_icon=None, display_order=9999):
        """
        Creates a new zone.

        :param str name: the zone name
        :param list(Device) devices: the list of Device objects
        :param zone.Level level: the zone's physical level
        :param list(Neighbor) neighbors: the list of optional neighbor zones.
        :param dict(ZoneEvent -> list(Action)) actions: the optional \
            dictionary from :class:`.ZoneEvent` to :class:`.Action`
        :param Bool external: indicates if the zone is external
        :param str display_icon: the icon associated with the zone, useful
            for displaying in sitemap.
        :param int display_order: the order with respective to the other zones,
            useful for arranging in sitemap.
        """

        if actions is None:
            actions = {}
        if devices is None:
            devices = []
        if neighbors is None:
            neighbors = []

        self.name = name
        self.level = level
        self.devices = [d for d in devices]
        self.neighbors = list(neighbors)  # type : List[Neighbor]
        self.actions = dict(actions)  # shallow copy
        self.external = external
        self.displayIcon = display_icon
        self.displayOrder = display_order

    def add_device(self, device):
        """
        Creates a new zone that is an exact copy of this one, but has the
        additional device.

        :return: A NEW object.
        :rtype: Zone
        :raise ValueError: if device is None or is not a subclass of :class:`.Device`
        """
        if device is None:
            raise ValueError('device must not be None')

        if not isinstance(device, Device):
            raise ValueError('device must be an instance of Device')

        new_devices = list(self.devices)
        new_devices.append(device)

        params = self._create_ctor_param_dictionary('devices', new_devices)
        return Zone(**params)

    def remove_device(self, device):
        """
        Creates a new zone that is an exact copy of this one less the given
        device

        :return: A NEW object.
        :rtype: Zone 
        :raise ValueError: if device is None or is not a subclass of :class:`.Device`
        """
        if device is None:
            raise ValueError('device must not be None')

        if not isinstance(device, Device):
            raise ValueError('device must be an instance of Device')

        new_devices = list(self.devices)
        new_devices.remove(device)

        params = self._create_ctor_param_dictionary('devices', new_devices)
        return Zone(**params)

    def has_device(self, device):
        """
        Determine if the zone contains the specified device.

        :rtype: Boolean
        """
        return device in self.devices

    def get_devices(self):
        """
        Returns a copy of the list of devices.

        :rtype: list(Device)
        """
        return [d for d in self.devices]

    def get_devices_by_type(self, cls: type):
        """
        Returns a list of devices matching the given type.

        :param type cls: the device type
        :rtype: list(Device)
        """
        if cls is None:
            raise ValueError('cls must not be None')
        return [d for d in self.devices if isinstance(d, cls)]

    def get_first_device_by_type(self, cls: type):
        """
        Returns the first device matching the given type, or None if there is no device.

        :param type cls: the device type
        :rtype: Device or None
        """
        devices = self.get_devices_by_type(cls)
        return devices[0] if len(devices) > 0 else None

    def get_device_by_event(self, event_info):
        """
        Returns the device that generates the provided event.

        :param EventInfo event_info:
        :rtype: Device
        """

        if event_info is None:
            raise ValueError('eventInfo must not be None')

        return next((d for d in self.devices
                     if d.contains_item(event_info.get_item())), None)

    def add_neighbor(self, neighbor):
        """
        Creates a new zone that is an exact copy of this one, but has the
        additional neighbor.

        :return: A NEW object.
        :rtype: Zone 
        """
        if neighbor is None:
            raise ValueError('neighbor must not be None')

        new_neighbors = list(self.neighbors)
        new_neighbors.append(neighbor)

        params = self._create_ctor_param_dictionary('neighbors', new_neighbors)
        return Zone(**params)

    def add_action(self, action):
        """
        Creates a new zone that is an exact copy of this one, but has the
        additional action mapping.
        The actions are sorted by its priority in ascending order.

        :param Any action:
        :return: A NEW object.
        :rtype: Zone 
        """
        if len(action.get_required_events()) == 0:
            raise ValueError('Action must define at least one triggering event')

        new_actions = dict(self.actions)

        events = set(action.get_required_events() + action.get_external_events())
        for zone_event in events:
            if zone_event in new_actions:
                new_actions[zone_event].append(action)
                new_actions[zone_event].sort(key=lambda a: a.get_priority())
            else:
                new_actions[zone_event] = [action]

        params = self._create_ctor_param_dictionary('actions', new_actions)
        return Zone(**params)

    def get_actions(self, zone_event):
        """
        :return: the list of actions for the provided zoneEvent
        :rtype: list(Action)
        """
        if zone_event in self.actions:
            return self.actions[zone_event]
        else:
            return []

    def has_action(self, action: Action):
        """
        Determine if the zone contains the specified action.

        :rtype: Boolean
        """
        for action_list in self.actions.values():
            if action in action_list:
                return True

        return False

    def get_id(self):
        """ :rtype: str """
        return self.get_level().value + '_' + self.get_name()

    def get_name(self):
        """ :rtype: str """
        return self.name

    def is_internal(self):
        """
        :return: True if the this is an internal zone
        :rtype: bool
        """
        return not self.is_external()

    def is_external(self):
        """
        :return: True if the this is an external zone
        :rtype: bool
        """
        return self.external

    def get_level(self):
        """ :rtype: zone.Level"""
        return self.level

    def get_display_icon(self):
        """ :rtype: str or None if not available"""
        return self.displayIcon

    def get_display_order(self):
        """ :rtype: int"""
        return self.displayOrder

    def get_neighbors(self):
        """
        :return: a copy of the list of neighboring zones.
        :rtype: list(Neighbor)
        """
        return list(self.neighbors)

    def get_neighbor_zones(self, zone_manager, neighbor_types=None):
        """
        :param zone_manager:
        :param list(NeighborType) neighbor_types: optional
        :return: a list of neighboring zones for the provided neighbor type (optional).
        :rtype: list(Zone)
        """
        if neighbor_types is None:
            neighbor_types = []

        if zone_manager is None:
            raise ValueError('zoneManager must not be None')

        if neighbor_types is None or len(neighbor_types) == 0:
            zones = [zone_manager.get_zone_by_id(n.get_zone_id())
                     for n in self.neighbors]
        else:
            zones = [zone_manager.get_zone_by_id(n.get_zone_id())
                     for n in self.neighbors
                     if any(n.get_type() == t for t in neighbor_types)]

        return zones

    def contains_open_hab_item(self, item, sensor_type: type = None):
        """
        Returns True if this zone contains the given item; returns False
        otherwise.

        :param Item item:
        :param Device sensor_type: an optional sub-class of Device. If specified,\
            will search for itemName for those device types only. Otherwise,\
            search for all devices/sensors.
        :rtype: bool
        """
        sensors = self.get_devices() if sensor_type is None \
            else self.get_devices_by_type(sensor_type)
        return any(s.contains_item(item) for s in sensors)

    def get_illuminance_level(self):
        """
        Retrieves the maximum illuminance level from one or more IlluminanceSensor.
        If no sensor is available, return -1.

        :rtype: int
        """
        illuminances = [s.get_illuminance_level() for s in self.get_devices_by_type(
            IlluminanceSensor)]
        zone_illuminance = -1
        if len(illuminances) > 0:
            zone_illuminance = max(illuminances)

        return zone_illuminance

    def is_occupied(self, ignored_device_types=None, seconds_from_last_event=5 * 60):
        """
        Returns a list of two value.
        The first value is True if at least one device's is_occupied() method returns true (i.e. at least one device was
        triggered within the provided # of seconds); otherwise it is False.
        If the first list item is True, then the second value is the Device that indicates occupancy; otherwise it i
        None.

        :param seconds_from_last_event:
        :param list(Device) ignored_device_types: the devices not to be
            considered for the occupancy check.
        :rtype: list(bool, Device)
        """
        if ignored_device_types is None:
            ignored_device_types = []

        for device in self.get_devices():
            if not any(isinstance(device, deviceType) for deviceType in ignored_device_types):
                if device.is_occupied(seconds_from_last_event):
                    return True, device

        return False, None

    def is_light_on(self):
        """
        Returns True if at least one light is on; returns False otherwise.

        :rtype: bool
        """
        return any(light.is_on() for light in self.get_devices_by_type(Light))

    def share_sensor_with(self, zone, sensor_type):
        """
        Returns True if this zone shares at least one sensor of the given
        sensor_type with the provider zone.
        Two sensors are considered the same if they link to the same channel.

        See :meth:`.Device.getChannel`

        :rtype: bool
        """
        our_sensor_channels = [s.get_channel()
                               for s in self.get_devices_by_type(sensor_type)
                               if s.get_channel() is not None]

        their_sensor_channels = [s.get_channel()
                                 for s in zone.get_devices_by_type(sensor_type)
                                 if s.get_channel() is not None]

        intersection = set(our_sensor_channels).intersection(their_sensor_channels)
        return len(intersection) > 0

    def turn_off_lights(self, events):
        """
        Turn off all the lights in the zone.

        :param scope.events events:
        """
        for light in self.get_devices_by_type(Light):
            if light.is_on():
                light.turn_off(events)

    def on_switch_turned_on(self, events, item, immutable_zone_manager):
        """
        If item belongs to this zone, dispatches the event to the associated
        Switch object, execute the associated actions, and returns True.
        Otherwise return False.

        See :meth:`.Switch.onSwitchTurnedOn`

        :param item:
        :param events:
        :param ImmutableZoneManager immutable_zone_manager: a function that \
            returns a Zone object given a zone id string
        :rtype: boolean
        """
        is_processed = False
        actions = self.get_actions(ZoneEvent.SWITCH_TURNED_ON)

        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_ON, item, self,
                               immutable_zone_manager, events)

        switches = self.get_devices_by_type(Switch)
        for switch in switches:
            if switch.on_switch_turned_on(events, pe.get_item_name(item)):
                for a in actions:
                    a.on_action(event_info)

                is_processed = True

        return is_processed

    def on_switch_turned_off(self, events, item, immutable_zone_manager):
        """
        If item belongs to this zone, dispatches the event to the associated
        Switch object, execute the associated actions, and returns True.
        Otherwise return False.

        See :meth:`.Switch.onSwitchTurnedOff`

        :rtype: boolean
        """
        event_info = EventInfo(ZoneEvent.SWITCH_TURNED_OFF, item, self,
                               immutable_zone_manager, events)

        is_processed = False
        actions = self.get_actions(ZoneEvent.SWITCH_TURNED_OFF)

        switches = self.get_devices_by_type(Switch)
        for switch in switches:
            if switch.on_switch_turned_off(events, pe.get_item_name(item)):
                for a in actions:
                    a.on_action(event_info)

                is_processed = True

        return is_processed

    def dispatch_event(self, zone_event, event_dispatcher, device: Union[Device, None], item,
                       immutable_zone_manager, owning_zone=None):
        """
        :param Device device: the device containing the item that received the event.
        :param Any item: the OpenHab item that received the event
        :param ZoneEvent zone_event:
        :param events event_dispatcher:
        :param ImmutableZoneManager immutable_zone_manager:
        :param Any owning_zone: the zone that contains the item; None if the current zone contains
            the item.
        :rtype: boolean
        """
        processed = False
        event_info = EventInfo(zone_event, item, self,
                               immutable_zone_manager, event_dispatcher, owning_zone, device)

        if zone_event == ZoneEvent.STARTUP:
            for action_list in self.actions.values():
                for action in action_list:
                    action.on_startup(event_info)

            processed = True
        elif zone_event == ZoneEvent.DESTROY:
            for action_list in self.actions.values():
                for action in action_list:
                    action.on_destroy(event_info)

            processed = True
        else:
            for a in self.get_actions(zone_event):
                if a.on_action(event_info):
                    processed = True

        return processed

    def __str__(self):
        value = u"Zone: {}, floor: {}, {}, displayIcon: {}, displayOrder: {}, {} devices".format(
            self.name,
            self.level.name,
            ('external' if self.is_external() else 'internal'),
            self.displayIcon,
            self.displayOrder,
            len(self.devices))
        for d in sorted(self.devices, key=lambda item: item.__class__.__name__):
            value += u"\n  {}".format(str(d))

        if len(self.actions) > 0:
            value += u"\n"
            for key in sorted(self.actions.keys(), key=lambda item: item.name):
                action_list = self.actions[key]
                for action in action_list:
                    value += u"\n  Action: {} -> {}".format(key.name, type(action).__name__)

        if len(self.neighbors) > 0:
            value += u"\n"
            for n in self.neighbors:
                value += u"\n  Neighbor: {}, {}".format(
                    n.get_zone_id(), n.get_type().name)

        return value

    def _create_ctor_param_dictionary(self, key_to_replace: str, new_value):
        """
        A helper method to return a list of ctor parameters.
        
        :param str key_to_replace: the key to override
        :param any new_value: the new value to replace
        :rtype: dict
        """

        params = {'name': self.name, 'devices': self.devices, 'level': self.level, 'neighbors': self.neighbors,
                  'actions': self.actions, 'external': self.external, 'display_icon': self.displayIcon,
                  'display_order': self.displayOrder, key_to_replace: new_value}

        return params
