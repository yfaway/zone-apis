import re
from typing import Tuple, List, Union, Dict, Any

import HABApp
from HABApp.core import Items
from HABApp.core.events import ValueChangeEvent
from HABApp.openhab.items import ContactItem, StringItem, SwitchItem

from aaa_modules import platform_encapsulator as PE
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.zone import Zone, Level
from aaa_modules.layout_model.neighbor import NeighborType, Neighbor


def create_motion_sensor(item) -> MotionSensor:
    """
    Creates a MotionSensor and register for change event.
    :param item: SwitchItem
    :return: MotionSensor
    """
    sensor = MotionSensor(item)

    def handler(event: ValueChangeEvent):
        if PE.is_in_on_state(item):
            sensor.on_triggered(event)

    item.listen_event(handler, ValueChangeEvent)

    return sensor


def parse() -> list:
    mappings = {
        '.*MotionSensor$': create_motion_sensor
    }

    zone_mappings = {}
    for zone in parse_zones():
        zone_mappings[zone.getId()] = zone

    items = Items.get_all_items()
    for item in items:
        for pattern in mappings.keys():

            device = None
            if re.match(pattern, item.name) is not None:
                device = mappings[pattern](item)
                # PE.log_error(sensor_item.getItemName())

            if device is not None:
                zone_id = _get_zone_id_from_item_name(item.name)
                if zone_id is None:
                    PE.log_warning("Can't get zone id from item name '{}'".format(item.name))
                    continue

                if zone_id not in zone_mappings.keys():
                    PE.log_warning("Invalid zone id '{}'".format(zone_id))
                    continue

                zone = zone_mappings[zone_id].addDevice(device)
                zone_mappings[zone_id] = zone

    for z in zone_mappings.values():
        PE.log_error(z)

    return items


def parse_zones() -> List[Zone]:
    """
    Parses items with the zone pattern in the name and constructs the associated Zone objects.
    :return: List[Zone]
    """
    pattern = 'Zone_([^_]+)'
    zones = []

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
