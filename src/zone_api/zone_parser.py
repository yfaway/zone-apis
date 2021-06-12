import re
from typing import List, Dict, Type
import pkgutil
import inspect
import importlib

import HABApp
from HABApp.core import Items
from HABApp.core.items.base_item import BaseItem

import zone_api.core.actions as actions
from zone_api import platform_encapsulator as pe
from zone_api import device_factory as df
from zone_api.alert_manager import AlertManager
from zone_api.core.action import Action
from zone_api.core.devices.activity_times import ActivityTimes
from zone_api.core.devices.gas_sensor import NaturalGasSensor, SmokeSensor, Co2GasSensor
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.zone import Zone, Level
from zone_api.core.zone_manager import ZoneManager
from zone_api.core.neighbor import NeighborType, Neighbor

"""
This module contains functions to construct an ImmutableZoneManager using the following convention
for the OpenHab items.

 1. The zones are defined as a String item with this pattern Zone_{name}:
        String Zone_GreatRoom                                                           
            { level="FF", displayIcon="player", displayOrder="1",                         
              openSpaceSlaveNeighbors="FF_Kitchen" } 
      - The levels are the reversed mapping of the enums in Zone::Level.
      - Here are the list of supported attributes: level, external, openSpaceNeighbors,
        openSpaceMasterNeighbors, openSpaceSlaveNeighbors, displayIcon, displayOrder.
       
 2. The individual OpenHab items are named after this convention:
        {zone_id}_{device_type}_{device_name}.
    Here's an example:
        Switch FF_Office_LightSwitch "Office Light" (gWallSwitch, gLightSwitch, gFirstFloorLightSwitch)
            [shared-motion-sensor]                                                        
            { channel="zwave:device:9e4ce05e:node8:switch_binary", durationInMinutes="15" }                                                    
"""


def parse(activity_times: ActivityTimes, actions_package: str = "zone_api.core.actions",
          actions_path: List[str] = actions.__path__) -> ImmutableZoneManager:
    """
    - Parses the zones and devices from the remote OpenHab items (via the REST API).
    - Adds devices to the zones.
    - Adds default actions to the zones.
    - For each action, invoke Action::on_startup method.
    - Start the scheduler service.

    :return:
    """
    mappings = {
        '.*AlarmPartition$': df.create_alarm_partition,
        '.*_ChromeCast$': df.create_chrome_cast,
        '.*Door$': df.create_door,
        '[^g].*_Window$': df.create_window,
        '.*_Camera$': df.create_camera,
        '[^g].*MotionSensor$': df.create_motion_sensor,
        '[^g].*LightSwitch.*': df.create_switches,
        '.*FanSwitch.*': df.create_switches,
        '.*Wled_MasterControls.*': df.create_switches,
        '[^g].*_Illuminance.*': df.create_illuminance_sensor,
        '[^g](?!.*Weather).*Humidity$': df.create_humidity_sensor,
        '[^g].*_NetworkPresence.*': df.create_network_presence_device,
        '[^g].*_Plug$': df.create_plug,
        '[^g].*_Co2$': df.create_gas_sensor(Co2GasSensor),
        '[^g].*_NaturalGas$': df.create_gas_sensor(NaturalGasSensor),
        '[^g].*_Smoke$': df.create_gas_sensor(SmokeSensor),
        '.*_Tv$': df.create_television_device,
        '.*_Thermostat_EcobeeName$': df.create_ecobee_thermostat,
        # not matching "FF_Office_Computer_Dell_GpuTemperature"
        '[^g](?!.*Computer)(?!.*Weather).*Temperature$': df.create_temperature_sensor,
        '[^g].*WaterLeakState$': df.create_water_leak_sensor,
        '[^g].*_TimeOfDay$': df.create_astro_sensor,
        '.*_Computer_[^_]+$': df.create_computer,
        '.*_Weather_Temperature$': df.create_weather,
    }

    zm: ZoneManager = ZoneManager()
    immutable_zm = zm.get_immutable_instance()
    immutable_zm = immutable_zm.set_alert_manager(AlertManager())

    zone_mappings = {}
    for zone in _parse_zones():
        zone_mappings[zone.get_id()] = zone

    items: List[BaseItem] = Items.get_all_items()
    for item in items:
        for pattern in mappings.keys():

            device = None
            if re.match(pattern, item.name) is not None:
                device = mappings[pattern](immutable_zm, item)

            if device is not None:
                zone_id = df.get_zone_id_from_item_name(item.name)
                if zone_id is None:
                    pe.log_warning("Can't get zone id from item name '{}'".format(item.name))
                    continue

                if zone_id not in zone_mappings.keys():
                    pe.log_warning("Invalid zone id '{}'".format(zone_id))
                    continue

                zone = zone_mappings[zone_id].add_device(device)
                zone_mappings[zone_id] = zone

    # Add specific devices to the Virtual Zone
    zone = next((z for z in zone_mappings.values() if z.get_name() == 'Virtual'), None)
    if zone is not None:
        zone = zone.add_device(activity_times)
        zone_mappings[zone.get_id()] = zone

    action_classes = get_action_classes(actions_package, actions_path)
    zone_mappings = add_actions(zone_mappings, action_classes)

    for z in zone_mappings.values():
        zm.add_zone(z)

    immutable_zm.start()

    return immutable_zm


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

        level = Level(df.get_meta_value(metadata, "level"))
        external = df.get_meta_value(metadata, "external", False)
        display_icon = df.get_meta_value(metadata, "displayIcon", '')
        display_order = int(df.get_meta_value(metadata, "displayOrder", 9999))

        zone = Zone(zone_name, [], level, [], {}, external, display_icon, display_order)

        neighbor_type_mappings = {
            'closeSpaceNeighbors': NeighborType.CLOSED_SPACE,
            'openSpaceNeighbors': NeighborType.OPEN_SPACE,
            'openSpaceMasterNeighbors': NeighborType.OPEN_SPACE_MASTER,
            'openSpaceSlaveNeighbors': NeighborType.OPEN_SPACE_SLAVE,
        }
        for neighbor_type_str in neighbor_type_mappings.keys():
            neighbor_str = df.get_meta_value(metadata, neighbor_type_str)
            if neighbor_str is not None:
                for neighbor_id in neighbor_str.split(','):
                    neighbor_id = neighbor_id.strip()
                    neighbor = Neighbor(neighbor_id, neighbor_type_mappings[neighbor_type_str])

                    zone = zone.add_neighbor(neighbor)

        zones.append(zone)

    return zones


def add_actions(zone_mappings: Dict, action_classes: List[Type]) -> Dict:
    """
    Create action instances from action_classes and add them to the zones.
    A set of filters are applied to ensure that only the application actions are added to each zone.
    As the Zone class is immutable, a new Zone instance is created after adding an action. As such, a zone_mappings
    dictionary must be provided.

    :param str zone_mappings: mappings from zone_id string to a Zone instance.
    :param str action_classes: the list of action types.
    """

    for clazz in action_classes:
        action: Action = clazz()

        for zone in zone_mappings.values():
            if not _can_add_action_to_zone(zone, action):
                continue

            if action.must_be_unique_instance():
                zone = zone.add_action(clazz())
            else:
                zone = zone.add_action(action)

            zone_mappings[zone.get_id()] = zone

    return zone_mappings


def _can_add_action_to_zone(zone: Zone, action: Action) -> bool:
    satisfied = True  # must have all devices
    for device_type in action.get_required_devices():
        if len(zone.get_devices_by_type(device_type)) == 0:
            satisfied = False
            break

    if not satisfied:
        return False

    if zone.is_internal() and not action.is_applicable_to_internal_zone():
        return False

    if zone.is_external() and not action.is_applicable_to_external_zone():
        return False

    if len(action.get_applicable_levels()) > 0 and (zone.get_level() not in action.get_applicable_levels()):
        return False

    zone_name_pattern = action.get_applicable_zone_name_pattern()
    if zone_name_pattern is not None:
        match = re.search(zone_name_pattern, zone.get_name())
        if not match:
            return False

    return True


def get_action_classes(actions_package: str = "zone_api.core.actions",
                       actions_path: List[str] = actions.__path__) -> List[Type]:
    """
    Retrieve a list of action class types defined in the actions_path with the given actions_package.

    To avoid loading the non-action classes (the package might contain helper modules), the following restrictions
    are used:
      1. The normalized action name must be the same as the normalized module name.
         e.g. action 'ManagePlugs' is defined in the file 'manage_plugs.py'.
      2. The class defined in the module must be an instance of 'Action'.

    :param str actions_package: the package of the action classes.
    :param str actions_path: the absolute path to the action classes.
    """
    classes = []

    for importer, module_name, is_pkg in pkgutil.iter_modules(actions_path):
        module = importlib.import_module(f"{actions_package}.{module_name}")

        for (name, value) in inspect.getmembers(module, lambda member: inspect.isclass(member)):
            normalized_module_name = module_name.replace('_', '').lower()
            if name.lower() == normalized_module_name:
                try:
                    clazz = getattr(module, name)
                    obj = clazz()
                    if isinstance(obj, Action):
                        classes.append(clazz)
                except AttributeError:
                    pass
                except TypeError:
                    pass

    return classes
