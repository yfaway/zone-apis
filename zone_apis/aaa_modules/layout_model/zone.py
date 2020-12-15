from enum import Enum, unique
from typing import Tuple, List, Union, Dict, Any

from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.device import Device

# from aaa_modules.layout_model.devices.astro_sensor import AstroSensor
# from aaa_modules.layout_model.devices.illuminance_sensor import IlluminanceSensor
# from aaa_modules.layout_model.devices.switch import Light, Switch
from aaa_modules.layout_model.neighbor import Neighbor

from aaa_modules.platform_encapsulator import PlatformEncapsulator as PE


@unique
class Level(Enum):
    """ An enum of the vertical levels."""

    UNDEFINED = "UD"  #: Undefined
    BASEMENT = "BM"  #: The basement
    FIRST_FLOOR = "FF"  #: The first floor
    SECOND_FLOOR = "SF"  #: The second floor
    THIRD_FLOOR = "TF"  #: The third floor
    VIRTUAL = "VT"  #: The third floor


class ZoneEvent:
    """ An enum of triggering zone events. """

    UNDEFINED = -1  # Undefined
    MOTION = 1  # A motion triggered event
    SWITCH_TURNED_ON = 2  # A switch turned-on event
    SWITCH_TURNED_OFF = 3  # A switch turned-on event
    CONTACT_OPEN = 4  # A contact (doors/windows) is open
    CONTACT_CLOSED = 5  # A contact (doors/windows) is close
    PARTITION_ARMED_AWAY = 6  # Changed to armed away
    PARTITION_ARMED_STAY = 7  # Changed to armed stay
    PARTITION_DISARMED_FROM_AWAY = 8  # Changed from armed away to disarm
    PARTITION_DISARMED_FROM_STAY = 9  # Changed from armed stay to disarm
    HUMIDITY_CHANGED = 10  # The humidity percentage changed
    TEMPERATURE_CHANGED = 11  # The temperature changed
    GAS_TRIGGER_STATE_CHANGED = 12  # The gas sensor triggering boolean changed
    GAS_VALUE_CHANGED = 13  # The gas sensor value changed


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
    device/sensor is not (the state changes).  See :meth:`addDevice`, 
    :meth:`removeDevice`, :meth:`add_neighbor()`

    The zone itself doesn't know how to operate a device/sensor. The sensors
    themselves (all sensors derive from Device class) exposes the possible
    operations. Generally, the zone needs not know about the exact types of 
    sensors it contains. However, controlling the light is a very common case
    for home automation; thus it does references to several virtual/physical
    sensors to determine the astro time, the illuminance, and the motion sensor.  
    See :meth:`getDevices()`, :meth:`getDevicesByType()`.

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
        self.neighbors = list(neighbors) # type : List[Neighbor]
        self.actions = dict(actions)  # shallow copy
        self.external = external
        self.displayIcon = display_icon
        self.displayOrder = display_order

    def addDevice(self, device):
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

    def removeDevice(self, device):
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

    def hasDevice(self, device):
        """
        Determine if the zone contains the specified device.

        :rtype: Boolean
        """
        return device in self.devices

    def getDevices(self):
        """
        Returns a copy of the list of devices.

        :rtype: list(Device)
        """
        return [d for d in self.devices]

    def getDevicesByType(self, cls: type):
        """
        Returns a list of devices matching the given type.

        :param type cls: the device type
        :rtype: list(Device)
        """
        if cls is None:
            raise ValueError('cls must not be None')
        return [d for d in self.devices if isinstance(d, cls)]

    def getDeviceByEvent(self, event_info):
        """
        Returns the device that generates the provided event.

        :param EventInfo event_info:
        :rtype: Device
        """

        if event_info is None:
            raise ValueError('eventInfo must not be None')

        return next((d for d in self.devices
                     if d.containsItem(event_info.getItem())), None)

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

        :param Action action:
        :return: A NEW object.
        :rtype: Zone 
        """
        if len(action.getRequiredEvents()) == 0:
            raise ValueError('Action must define at least one triggering event')

        new_actions = dict(self.actions)

        for zone_event in action.getRequiredEvents():
            if zone_event in new_actions:
                new_actions[zone_event].append(action)
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

    def getId(self):
        """ :rtype: str """
        return self.getLevel().value + '_' + self.getName()

    def getName(self):
        """ :rtype: str """
        return self.name

    def isInternal(self):
        """
        :return: True if the this is an internal zone
        :rtype: bool
        """
        return not self.isExternal()

    def isExternal(self):
        """
        :return: True if the this is an external zone
        :rtype: bool
        """
        return self.external

    def getLevel(self):
        """ :rtype: zone.Level"""
        return self.level

    def getDisplayIcon(self):
        """ :rtype: str or None if not available"""
        return self.displayIcon

    def getDisplayOrder(self):
        """ :rtype: int"""
        return self.displayOrder

    def getNeighbors(self):
        """
        :return: a copy of the list of neighboring zones.
        :rtype: list(Neighbor)
        """
        return list(self.neighbors)

    def getNeighborZones(self, zone_manager, neighbor_types=None):
        """
        :param zone_manager:
        :param list(NeighborType) neighbor_types: optional
        :return: a list of neighboring zones for the provided neighbor type (optional).
        :rtype: list(Zone)
        """
        if neighbor_types is None:
            neighbor_types = []

        if None == zone_manager:
            raise ValueError('zoneManager must not be None')

        if None == neighbor_types or len(neighbor_types) == 0:
            zones = [zone_manager.getZoneById(n.getZoneId()) \
                     for n in self.neighbors]
        else:
            zones = [zone_manager.getZoneById(n.getZoneId()) \
                     for n in self.neighbors \
                     if any(n.getType() == t for t in neighbor_types)]

        return zones

    def containsOpenHabItem(self, item, sensor_type: type = None):
        """
        Returns True if this zone contains the given itemName; returns False 
        otherwise.

        :param Item item:
        :param Device sensor_type: an optional sub-class of Device. If specified,\
            will search for itemName for those device types only. Otherwise,\
            search for all devices/sensors.
        :rtype: bool
        """
        sensors = self.getDevices() if sensor_type is None \
            else self.getDevicesByType(sensor_type)
        return any(s.containsItem(item) for s in sensors)

    def getIlluminanceLevel(self):
        """
        Retrieves the maximum illuminance level from one or more IlluminanceSensor.
        If no sensor is available, return -1.

        :rtype: int
        """
        illuminances = [s.getIlluminanceLevel() for s in self.getDevicesByType(
            IlluminanceSensor)]
        zone_illuminance = -1
        if len(illuminances) > 0:
            zone_illuminance = max(illuminances)

        return zone_illuminance

    def isLightOnTime(self):
        """
        Returns True if it is light-on time; returns false if it is no. Returns
        None if there is no AstroSensor to determine the time.

        :rtype: bool or None
        """
        astro_sensors = self.getDevicesByType(AstroSensor)
        if len(astro_sensors) == 0:
            return None
        else:
            return any(s.isLightOnTime() for s in astro_sensors)

    def isOccupied(self, ignored_device_types=None, seconds_from_last_event=5 * 60):
        """
        Returns an array of two items. The first item is True if - at least one switch turned on, or - a motion event
        was triggered within the provided # of seconds, or - a network device was active in the local network within
        the provided # of seconds. If the first item is True, the item is a Device that indicates occupancy.
        Otherwise it is None.

        :param seconds_from_last_event:
        :param list(Device) ignored_device_types: the devices not to be
            considered for the occupancy check.
        :rtype: list(bool, Device)
        """
        if ignored_device_types is None:
            ignored_device_types = []

        for device in self.getDevices():
            if not any(isinstance(device, deviceType) for deviceType in ignored_device_types):
                if device.isOccupied(seconds_from_last_event):
                    return True, device

        return False, None

    def isLightOn(self):
        """
        Returns True if at least one light is on; returns False otherwise.

        :rtype: bool
        """
        return any(l.isOn() for l in self.getDevicesByType(Light))

    def shareSensorWith(self, zone, sensor_type):
        """
        Returns True if this zone shares at least one sensor of the given
        sensor_type with the provider zone.
        Two sensors are considered the same if they link to the same channel.

        See :meth:`.Device.getChannel`

        :rtype: bool
        """
        our_sensor_channels = [s.getChannel()
                               for s in self.getDevicesByType(sensor_type)
                               if s.getChannel() is not None]

        their_sensor_channels = [s.getChannel()
                                 for s in zone.getDevicesByType(sensor_type)
                                 if s.getChannel() is not None]

        intersection = set(our_sensor_channels).intersection(their_sensor_channels)
        return len(intersection) > 0

    def turnOffLights(self, events):
        """
        Turn off all the lights in the zone.

        :param scope.events events:
        """
        for light in self.getDevicesByType(Light):
            if light.isOn():
                light.turnOff(events)

    def onTimerExpired(self, events, item):
        """
        Determines if the timer item is associated with a switch in this
        zone; if yes, turns off the switch and returns True. Otherwise returns
        False.
        """
        return False

    def onSwitchTurnedOn(self, events, item, immutable_zone_manager):
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

        switches = self.getDevicesByType(Switch)
        for switch in switches:
            if switch.onSwitchTurnedOn(events, item.getName()):
                for a in actions:
                    a.onAction(event_info)

                is_processed = True

        return is_processed

    def onSwitchTurnedOff(self, events, item, immutable_zone_manager):
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

        switches = self.getDevicesByType(Switch)
        for switch in switches:
            if switch.onSwitchTurnedOff(events, item.getName()):
                for a in actions:
                    a.onAction(event_info)

                is_processed = True

        return is_processed

    def dispatchEvent(self, zone_event, open_hab_events, item,
                      immutable_zone_manager, enforce_item_in_zone):
        """
        :param item: the item that received the event
        :param ZoneEvent zone_event:
        :param scope.events open_hab_events:
        :param ImmutableZoneManager immutable_zone_manager:
        :param bool enforce_item_in_zone: if set to true, the actions won't be
            triggered if the zone doesn't contain the item.
        :rtype: boolean
        """
        if enforce_item_in_zone and not self.containsOpenHabItem(item):
            return False

        return self._invoke_actions(zone_event, open_hab_events, item,
                                    immutable_zone_manager)

    def _invoke_actions(self, zone_event_type, event_dispatcher, item,
                        immutable_zone_manager):
        """
        Helper method to invoke actions associated with the event.
        :return: True if event is processed. 
        :rtype: boolean
        """
        event_info = EventInfo(zone_event_type, item, self,
                               immutable_zone_manager, event_dispatcher)

        processed = False
        for a in self.get_actions(zone_event_type):
            if a.onAction(event_info):
                processed = True

        return processed

    def __str__(self):
        value = u"Zone: {}, floor: {}, {}, displayIcon: {}, displayOrder: {}, {} devices".format(
            self.name,
            self.level.name,
            ('external' if self.isExternal() else 'internal'),
            self.displayIcon,
            self.displayOrder,
            len(self.devices))
        for d in self.devices:
            value += u"\n  {}".format(str(d))

        if len(self.actions) > 0:
            value += u"\n"
            for key in self.actions.keys():
                action_list = self.actions[key]
                for action in action_list:
                    value += u"\n  Action: {} -> {}".format(key, str(type(action).__name__))

        if len(self.neighbors) > 0:
            value += u"\n"
            for n in self.neighbors:
                value += u"\n  Neighbor: {}, {}".format(
                    n.getZoneId(), n.get_type().name)

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


def createSecondFloorZone(name):
    """
    Creates an internal second floor zone with the given name.
    :rtype: Zone
    """
    params = {'name': name, 'level': Level.SECOND_FLOOR}
    return Zone(**params)


def createFirstFloorZone(name):
    """
    Creates an internal first floor zone with the given name.
    :rtype: Zone
    """
    params = {'name': name, 'level': Level.FIRST_FLOOR}
    return Zone(**params)


def createExternalZone(name, level=Level.FIRST_FLOOR):
    """
    Creates an external zone with the given name.
    :rtype: Zone
    """
    params = {'name': name, 'level': level, 'external': True}
    return Zone(**params)
