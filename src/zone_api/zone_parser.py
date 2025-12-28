import re
from typing import List, Dict, Type, Hashable, Any
import pkgutil
import inspect
import importlib

import HABApp
from HABApp.core import Items
from HABApp.core.internals.item_registry import ItemRegistryItem

import zone_api.core.actions as actions
from zone_api import platform_encapsulator as pe
from zone_api import device_factory as df
from zone_api.alert_manager import AlertManager
from zone_api.core.action import Action
from zone_api.core.devices.gas_sensor import NaturalGasSensor, SmokeSensor, Co2GasSensor, RadonGasSensor
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.map_parameters import MapParameters
from zone_api.core.parameters import Parameters
from zone_api.core.zone import Zone, Level
from zone_api.core.zone_event import ZoneEvent
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


def parse(config: dict[Hashable, Any], actions_package: str = "zone_api.core.actions",
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
        '.*_MpdChromeCast$': df.create_mpd_chrome_cast,
        '.*Door$': df.create_door,
        '[^g].*_Window$': df.create_window,
        '.*_Camera$': df.create_camera,
        '[^g].*MotionSensor$': df.create_motion_sensor,
        '[^g].*LightSwitch.*': df.create_switches,
        '.*FanSwitch.*': df.create_switches,
        '.*Wled_MasterControls.*': df.create_switches,
        '[^g].*_Illuminance.*': df.create_illuminance_sensor,
        '[^g](?!.*Weather).*Humidity$': df.create_humidity_sensor,
        '[^g].*_IkeaControl$': df.create_ikea_remote_control(
            brightness_up_hold_event=ZoneEvent.MANUALLY_TRIGGER_FIRE_ALARM,
            brightness_down_hold_event=ZoneEvent.CANCEL_PANIC_ALARM),
        '[^g].*_NetworkPresence.*': df.create_network_presence_device,
        '[^g].*_.*Plug(\\d*)$': df.create_plug,
        '[^g].*_Co2$': df.create_gas_sensor(Co2GasSensor),
        '[^g].*_NaturalGas$': df.create_gas_sensor(NaturalGasSensor),
        '[^g].*_RadonGas$': df.create_gas_sensor(RadonGasSensor),
        '[^g].*_Smoke$': df.create_gas_sensor(SmokeSensor),
        '.*_Tv$': df.create_television_device,
        '.*_Thermostat_EcobeeName$': df.create_ecobee_thermostat,
        # not matching "FF_Office_Computer_Dell_GpuTemperature"
        '[^g](?!.*Computer)(?!.*Weather).*Temperature$': df.create_temperature_sensor,
        '[^g].*WaterLeakState$': df.create_water_leak_sensor,
        '[^g].*_TimeOfDay$': df.create_astro_sensor,
        '.*_Computer_[^_]+$': df.create_computer,
        '.*_Weather_Temperature$': df.create_weather,
        '[^g].*_AutoReportDeviceName$': df.create_auto_report_notification_setting,
        '^FF_Virtual_FlashMessage$': df.create_flash_message,
        '^FF_Virtual_MpdController': df.create_mpd_controller,
    }

    action_parameters: Parameters = _read_zone_api_configurations(config)

    zm: ZoneManager = ZoneManager()
    immutable_zm = zm.get_immutable_instance()
    immutable_zm = immutable_zm.set_system_config(config)
    immutable_zm = immutable_zm.set_alert_manager(AlertManager(config))

    zone_mappings = {}
    for zone in _parse_zones():
        zone_mappings[zone.get_id()] = zone

    items: tuple[ItemRegistryItem] = Items.get_items()
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
        zone = zone.add_device(immutable_zm.activity_times)
        zone_mappings[zone.get_id()] = zone

    action_classes = get_action_classes(actions_package, actions_path)
    zone_mappings = add_actions(zone_mappings, action_classes, action_parameters)

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

    items = Items.get_items()
    for item in items:
        match = re.search(pattern, item.name)
        if not match:
            continue

        zone_name = match.group(1)
        item_def = HABApp.openhab.interface_sync.get_item(item.name)
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


def add_actions(zone_mappings: Dict, action_classes: List[Type], parameters: Parameters) -> Dict:
    """
    Create action instances from action_classes and add them to the zones.
    A set of filters are applied to ensure that only the application actions are added to each zone.
    As the Zone class is immutable, a new Zone instance is created after adding an action. As such, a zone_mappings
    dictionary must be provided.

    :param str zone_mappings: mappings from zone_id string to a Zone instance.
    :param str action_classes: the list of action types.
    :param Parameters parameters: the Parameter implementation
    :raise ValueError: if there are invalid parameters
    """
    (validated, errors) = parameters.validate(action_classes)
    if not validated:
        raise ValueError("\n".join(errors))

    for clazz in action_classes:
        action: Action = clazz(parameters)

        if action.get_parameter('disabled', False):
            continue

        for zone in zone_mappings.values():
            if not _can_add_action_to_zone(zone, action):
                continue

            if action.must_be_unique_instance:
                local_action: Action = clazz(parameters)
                zone = zone.add_action(local_action)
            else:
                zone = zone.add_action(action)

            zone_mappings[zone.get_id()] = zone

    return zone_mappings


def _can_add_action_to_zone(zone: Zone, action: Action) -> bool:
    satisfied = True  # must have all devices
    for device_type in action.required_devices:
        if len(zone.get_devices_by_type(device_type)) == 0:
            satisfied = False
            break

    if not satisfied:
        return False

    if zone.is_internal() and not action.applicable_to_internal_zone:
        return False

    if zone.is_external() and not action.applicable_to_external_zone:
        return False

    if len(action.applicable_levels) > 0 and (zone.get_level() not in action.applicable_levels):
        return False

    zone_name_pattern = action.applicable_zone_name_pattern
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
                    obj = clazz(MapParameters({}))
                    if isinstance(obj, Action):
                        classes.append(clazz)
                except AttributeError:
                    pass
                except TypeError:
                    pass

    return classes


def _read_zone_api_configurations(config: dict[Hashable, Any]) -> MapParameters:
    flat_map = {}

    all_action_params = config['action-parameters']
    for action_name in all_action_params.keys():
        action_params = all_action_params[action_name]
        for key in action_params.keys():
            flat_key = f"{action_name}.{key}"
            flat_map[flat_key] = action_params[key]

    return MapParameters(flat_map)
