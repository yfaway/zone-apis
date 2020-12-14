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

    PE.log_error(sensor.__unicode__())

    return sensor


def parse() -> list:
    mappings = {
        '.*MotionSensor$': create_motion_sensor
    }

    items = Items.get_all_items()
    for item in items:
        # PE.log_error("** i: {}".format(item))
        for pattern in mappings.keys():
            if re.match(pattern, item.name) is not None:
                sensor_item = mappings[pattern](item)
                # PE.log_error(sensor_item.getItemName())

    # items = HABApp.core.Items.get_all_items()
    # PE.log_error("count: {}".format(len(items)))

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
            item.name, "level, external, openSpaceNeighbors, displayIcon, displayOrder")
        metadata = item_def.metadata

        level = _get_zone_level(_get_meta_value(metadata, "level"))
        external = _get_meta_value(metadata, "external", False)
        display_icon = _get_meta_value(metadata, "displayIcon", '')
        display_order = int(_get_meta_value(metadata, "displayOrder", 9999))

        zone = Zone(zone_name, [], level, [], {}, external, display_icon, display_order)

        neighbor_str = _get_meta_value(metadata, "openSpaceNeighbors")
        if neighbor_str is not None:
            for neighbor_id in neighbor_str.split(','):
                neighbor_id = neighbor_id.strip()
                neighbor = Neighbor(neighbor_id, NeighborType.OPEN_SPACE)

                zone = zone.add_neighbor(neighbor)

        zones.append(zone)

    return zones


def _get_zone_level(level_string):
    """
    :rtype: Level
    :raise ValueError if level_string is invalid
    """
    if 'BM' == level_string or 'VT' == level_string:
        return Level.BASEMENT
    elif 'FF' == level_string:
        return Level.FIRST_FLOOR
    elif 'SF' == level_string:
        return Level.SECOND_FLOOR
    elif 'TF' == level_string:
        return Level.THIRD_FLOOR
    else:
        raise ValueError('The zone level must be specified as BM, FF, SF, or TF: {}'.format(level_string))


def _get_meta_value(metadata: Dict[str, Any], key, default_value=None) -> str:
    value = metadata.get(key)
    if value is None:
        return default_value
    else:
        return value['value']
