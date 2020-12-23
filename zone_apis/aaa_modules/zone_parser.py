import re
from typing import List, Union, Dict, Any

import HABApp
from HABApp.core import Items
from HABApp.core.events import ValueChangeEvent
from HABApp.core.items import BaseValueItem
from HABApp.core.items.base_item import BaseItem
from HABApp.openhab.items import SwitchItem

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.turn_off_adjacent_zones import TurnOffAdjacentZones
from aaa_modules.layout_model.actions.turn_on_switch import TurnOnSwitch
from aaa_modules.layout_model.devices.astro_sensor import AstroSensor
from aaa_modules.layout_model.devices.dimmer import Dimmer
from aaa_modules.layout_model.devices.illuminance_sensor import IlluminanceSensor
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.devices.switch import Fan, Light, Switch
from aaa_modules.layout_model.immutable_zone_manager import ImmutableZoneManager
from aaa_modules.layout_model.zone import Zone, Level, ZoneEvent
from aaa_modules.layout_model.zone_manager import ZoneManager
from aaa_modules.layout_model.neighbor import NeighborType, Neighbor

switchActions = [TurnOnSwitch(), TurnOffAdjacentZones()]


def parse() -> ImmutableZoneManager:
    """
    Parses the zones and devices.
    :return:
    """
    mappings = {
        '[^g].*MotionSensor$': _create_motion_sensor,
        '[^g].*LightSwitch.*': _create_switches,
        '.*FanSwitch.*': _create_switches,
        '[^g].*_Illuminance.*': _create_illuminance_sensor,
    }

    zm: ZoneManager = ZoneManager()

    zone_mappings = {}
    for zone in _parse_zones():
        zone_mappings[zone.getId()] = zone

    items: List[BaseItem] = Items.get_all_items()
    for item in items:
        for pattern in mappings.keys():

            device = None
            if re.match(pattern, item.name) is not None:
                device = mappings[pattern](zm, item)
                # PE.log_error(sensor_item.getItemName())

            if device is not None:
                zone_id = _get_zone_id_from_item_name(item.name)
                if zone_id is None:
                    pe.log_warning("Can't get zone id from item name '{}'".format(item.name))
                    continue

                if zone_id not in zone_mappings.keys():
                    pe.log_warning("Invalid zone id '{}'".format(zone_id))
                    continue

                zone = zone_mappings[zone_id].addDevice(device)
                zone_mappings[zone_id] = zone

    # Add the AstroSensor to any zone that has a Light device.
    astro_sensor = AstroSensor(Items.get_item('VT_Time_Of_Day'))
    for zone in zone_mappings.values():
        if len(zone.getDevicesByType(Light)) > 0 or len(zone.getDevicesByType(Dimmer)) > 0:
            zone = zone.addDevice(astro_sensor)
            zone_mappings[zone.getId()] = zone

    for z in zone_mappings.values():
        z = _add_actions(z)
        zone_mappings[z.getId()] = z

    for z in zone_mappings.values():
        zm.add_zone(z)

    return zm.get_immutable_instance()


def _parse_zones() -> List[Zone]:
    """
    Parses items with the zone pattern in the name and constructs the associated Zone objects.
    :return: List[Zone]
    """
    pattern = 'Zone_([^_]+)'
    zones: List[Zone] = []

    items = Items.get_all_items()
    for item in items:
        match = re.search(pattern, item.name)
        if not match:
            continue

        zone_name = match.group(1)
        item_def = HABApp.openhab.interface.get_item(
            item.name,
            "level, external, openSpaceNeighbors, openSpaceMasterNeighbors, openSpaceSlaveNeighbors, displayIcon, "
            "displayOrder")
        metadata = item_def.metadata

        level = Level(_get_meta_value(metadata, "level"))
        external = _get_meta_value(metadata, "external", False)
        display_icon = _get_meta_value(metadata, "displayIcon", '')
        display_order = int(_get_meta_value(metadata, "displayOrder", 9999))

        zone = Zone(zone_name, [], level, [], {}, external, display_icon, display_order)

        neighbor_type_mappings = {
            'closeSpaceNeighbors': NeighborType.CLOSED_SPACE,
            'openSpaceNeighbors': NeighborType.OPEN_SPACE,
            'openSpaceMasterNeighbors': NeighborType.OPEN_SPACE_MASTER,
            'openSpaceSlaveNeighbors': NeighborType.OPEN_SPACE_SLAVE,
        }
        for neighbor_type_str in neighbor_type_mappings.keys():
            neighbor_str = _get_meta_value(metadata, neighbor_type_str)
            if neighbor_str is not None:
                for neighbor_id in neighbor_str.split(','):
                    neighbor_id = neighbor_id.strip()
                    neighbor = Neighbor(neighbor_id, neighbor_type_mappings[neighbor_type_str])

                    zone = zone.add_neighbor(neighbor)

        zones.append(zone)

    return zones


def _add_actions(zone: Zone) -> Zone:
    if len(zone.getDevicesByType(Switch)) > 0:
        for a in switchActions:
            zone = zone.add_action(a)

    return zone


def _get_meta_value(metadata: Dict[str, Any], key, default_value=None) -> str:
    """ Helper method to get the metadata value. """
    value = metadata.get(key)
    if value is None:
        return default_value
    else:
        return value['value']


def _get_zone_id_from_item_name(item_name: str) -> Union[str, None]:
    """ Extract and return the zone id from the the item name. """
    pattern = '([^_]+)_([^_]+)_(.+)'

    match = re.search(pattern, item_name)
    if not match:
        return None

    level_string = match.group(1)
    location = match.group(2)

    return level_string + '_' + location


def _create_motion_sensor(zm: ZoneManager, item) -> MotionSensor:
    """
    Creates a MotionSensor and register for change event.
    :param item: SwitchItem
    :return: MotionSensor
    """
    sensor = MotionSensor(item)

    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item):
            zm.update_device_last_activated_time(item)
            dispatch_event(zm, ZoneEvent.MOTION, item)

    item.listen_event(handler, ValueChangeEvent)

    return sensor


def _create_illuminance_sensor(zm: ZoneManager, item) -> IlluminanceSensor:
    """
    Creates an illuminance sensor
    :param item: NumberItem
    :return: IlluminanceSensor
    """
    return IlluminanceSensor(item)


def _create_switches(zm: ZoneManager, item: SwitchItem) -> Union[None, Dimmer, Light, Fan]:
    """
    Parses and creates Dimmer, Fan or Light device.
    :param item: SwitchItem
    :return: Union[None, Dimmer, Light, Fan]
    """
    device_name_pattern = '([^_]+)_([^_]+)_(.+)'  # level_location_deviceName
    item_name = item.name
    illuminance_threshold_in_lux = 8

    match = re.search(device_name_pattern, item_name)
    if not match:
        return None

    device_name = match.group(3)

    dimmable_key = 'dimmable'
    duration_in_minutes_key = 'durationInMinutes'
    disable_triggering_key = "disableTriggeringFromMotionSensor"

    item_def = HABApp.openhab.interface.get_item(
        item.name, f"noPrematureTurnOffTimeRange, {duration_in_minutes_key}, {dimmable_key}, {disable_triggering_key}")
    metadata = item_def.metadata

    if 'LightSwitch' == device_name or 'FanSwitch' == device_name:
        duration_in_minutes = int(_get_meta_value(metadata, duration_in_minutes_key, -1))
        if duration_in_minutes == -1:
            raise ValueError(f"Missing durationInMinutes value for {item_name}'")
    else:
        duration_in_minutes = None

    device = None
    if 'LightSwitch' == device_name:
        no_premature_turn_off_time_range = _get_meta_value(metadata, "noPrematureTurnOffTimeRange", None)

        disable_triggering = True if "true" == _get_meta_value(metadata, disable_triggering_key) else False

        if dimmable_key in metadata:
            config = metadata.get(dimmable_key).get('config')
            level = int(config.get('level'))
            time_ranges = config.get('timeRanges')

            device = Dimmer(item, duration_in_minutes, level, time_ranges,
                            illuminance_threshold_in_lux,
                            disable_triggering,
                            no_premature_turn_off_time_range)
        else:
            device = Light(item, duration_in_minutes,
                           illuminance_threshold_in_lux,
                           disable_triggering,
                           no_premature_turn_off_time_range)

    elif 'FanSwitch' == device_name:
        device = Fan(item, duration_in_minutes)

    if device is not None:
        def handler(event: ValueChangeEvent):
            if pe.is_in_on_state(item):
                if not zm.on_switch_turned_on(pe.get_event_dispatcher(), item):
                    pe.log_debug(f'Switch on event for {item.name} is not processed.')
            else:
                if not zm.on_switch_turned_off(pe.get_event_dispatcher(), item):
                    pe.log_debug(f'Switch off event for {item.name} is not processed.')

        item.listen_event(handler, ValueChangeEvent)

    return device


def dispatch_event(zm: ZoneManager, zone_event: ZoneEvent, item: BaseValueItem, enforce_item_in_zone=True):
    """
    Dispatches an event to the ZoneManager. If the event is not processed,
    create a debug log.
    """
    if not zm.dispatch_event(zone_event, pe.get_event_dispatcher(), item, enforce_item_in_zone):
        pe.log_debug(f'Event {zone_event} for item {item.name} is not processed.')
