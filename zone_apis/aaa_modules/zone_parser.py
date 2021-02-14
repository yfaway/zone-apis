import re
from typing import List, Union, Dict, Any, Type
import pkgutil
import inspect
import importlib

import HABApp
from HABApp.core import Items
from HABApp.core.events import ValueChangeEvent
from HABApp.core.items import BaseValueItem
from HABApp.core.items.base_item import BaseItem
from HABApp.openhab.items import ColorItem, DimmerItem, SwitchItem, StringItem, NumberItem

from aaa_modules import platform_encapsulator as pe
from aaa_modules.alert_manager import AlertManager
from aaa_modules.layout_model.action import Action
from aaa_modules.layout_model.devices.activity_times import ActivityTimes, ActivityType
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition, AlarmState
from aaa_modules.layout_model.devices.astro_sensor import AstroSensor
from aaa_modules.layout_model.devices.camera import Camera
from aaa_modules.layout_model.devices.chromecast_audio_sink import ChromeCastAudioSink
from aaa_modules.layout_model.devices.contact import Door, GarageDoor
from aaa_modules.layout_model.devices.dimmer import Dimmer
from aaa_modules.layout_model.devices.gas_sensor import GasSensor, NaturalGasSensor, SmokeSensor, Co2GasSensor
from aaa_modules.layout_model.devices.humidity_sensor import HumiditySensor
from aaa_modules.layout_model.devices.illuminance_sensor import IlluminanceSensor
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.devices.network_presence import NetworkPresence
from aaa_modules.layout_model.devices.plug import Plug
from aaa_modules.layout_model.devices.switch import Fan, Light
from aaa_modules.layout_model.devices.temperature_sensor import TemperatureSensor
from aaa_modules.layout_model.devices.thermostat import EcobeeThermostat
from aaa_modules.layout_model.devices.tv import Tv
from aaa_modules.layout_model.devices.wled import Wled
from aaa_modules.layout_model.immutable_zone_manager import ImmutableZoneManager
from aaa_modules.layout_model.zone import Zone, Level
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.zone_manager import ZoneManager
from aaa_modules.layout_model.neighbor import NeighborType, Neighbor


def parse() -> ImmutableZoneManager:
    """
    - Parses the zones and devices from the remote OpenHab items (via the REST API).
    - Adds devices to the zones.
    - Adds default actions to the zones.
    - For each action, invoke Action::on_startup method.
    - Start the scheduler service.

    :return:
    """
    mappings = {
        '.*AlarmPartition$': _create_alarm_partition,
        '.*_ChromeCast$': _create_chrome_cast,
        '.*Door$': _create_door,
        '.*_Camera$': _create_camera,
        '[^g].*MotionSensor$': _create_motion_sensor,
        '[^g].*LightSwitch.*': _create_switches,
        '.*FanSwitch.*': _create_switches,
        '.*Wled_MasterControls.*': _create_switches,
        '[^g].*_Illuminance.*': lambda zone_manager, an_item: IlluminanceSensor(an_item),
        '[^g].*Humidity$': _create_humidity_sensor,
        '[^g].*_NetworkPresence.*': lambda zone_manager, an_item: NetworkPresence(an_item),
        '[^g].*_Plug$': _create_plug,
        '[^g].*_Co2$': _create_gas_sensor(Co2GasSensor),
        '[^g].*_NaturalGas$': _create_gas_sensor(NaturalGasSensor),
        '[^g].*_Smoke$': _create_gas_sensor(SmokeSensor),
        '.*_Tv$': lambda zone_manager, an_item: Tv(an_item),
        '.*_Thermostat_EcobeeName$': lambda zone_manager, an_item: EcobeeThermostat(an_item),
        '[^g].*Temperature$': _create_temperature_sensor,
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
                zone_id = _get_zone_id_from_item_name(item.name)
                if zone_id is None:
                    pe.log_warning("Can't get zone id from item name '{}'".format(item.name))
                    continue

                if zone_id not in zone_mappings.keys():
                    pe.log_warning("Invalid zone id '{}'".format(zone_id))
                    continue

                device = device.set_channel(pe.get_channel(device.get_item()))
                device = device.set_zone_manager(immutable_zm)

                zone = zone_mappings[zone_id].add_device(device)
                zone_mappings[zone_id] = zone

    # Add the AstroSensor to any zone that has a Light device.
    astro_sensor = AstroSensor(Items.get_item('VT_Time_Of_Day')).set_zone_manager(immutable_zm)
    for zone in zone_mappings.values():
        if len(zone.get_devices_by_type(Light)) > 0 or len(zone.get_devices_by_type(Dimmer)) > 0:
            zone = zone.add_device(astro_sensor)
            zone_mappings[zone.get_id()] = zone

    # Add specific devices to the Virtual Zone
    zone = next((z for z in zone_mappings.values() if z.get_name() == 'Virtual'), None)
    if zone is not None:
        time_map = {
            ActivityType.WAKE_UP: '6 - 9',
            ActivityType.LUNCH: '12:00 - 13:30',
            ActivityType.QUIET: '14:00 - 16:00, 20:00 - 22:59',
            ActivityType.DINNER: '17:50 - 20:00',
            ActivityType.SLEEP: '23:00 - 7:00',
            ActivityType.AUTO_ARM_STAY: '20:00 - 2:00',
            ActivityType.TURN_OFF_PLUGS: '23:00 - 2:00',
        }
        zone = zone.add_device(ActivityTimes(time_map))
        zone_mappings[zone.get_id()] = zone

    zone_mappings = _add_actions(zone_mappings)

    for z in zone_mappings.values():
        zm.add_zone(z)

    for z in zm.get_zones():
        z.dispatch_event(ZoneEvent.STARTUP, pe.get_event_dispatcher(), None, immutable_zm)

    immutable_zm.start_scheduler()

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


def _add_actions(zone_mappings: Dict) -> Dict:
    """
    Programmatically add default actions defined in 'layout_model.actions' to each zone based on various criteria.
    """
    action_classes = _get_default_action_classes()

    for clazz in action_classes:
        action: Action = clazz()

        for zone in zone_mappings.values():
            satisfied = True  # must have all devices
            for device_type in action.get_required_devices():
                if len(zone.get_devices_by_type(device_type)) == 0:
                    satisfied = False
                    break

            if not satisfied:
                continue

            if zone.is_internal() and not action.is_applicable_to_internal_zone():
                continue

            if zone.is_external() and not action.is_applicable_to_external_zone():
                continue

            if len(action.get_applicable_levels()) > 0 and (zone.get_level() not in action.get_applicable_levels()):
                continue

            zone_name_pattern = action.get_applicable_zone_name_pattern()
            if zone_name_pattern is not None:
                match = re.search(zone_name_pattern, zone.get_name())
                if not match:
                    continue

            if action.must_be_unique_instance():
                zone = zone.add_action(clazz())
            else:
                zone = zone.add_action(action)

            zone_mappings[zone.get_id()] = zone

    return zone_mappings


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


# noinspection PyUnusedLocal
def _create_camera(zm: ImmutableZoneManager, item: StringItem) -> Camera:
    """
    Creates a Camera.
    :param item: SwitchItem
    """
    zone_name = _get_zone_id_from_item_name(item.name)

    camera = Camera(item, zone_name)

    return camera


def _create_door(zm: ImmutableZoneManager, item) -> Door:
    if 'garage' in pe.get_item_name(item).lower():
        sensor = GarageDoor(item)
    else:
        sensor = Door(item)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item) or pe.is_in_open_state(item):
            dispatch_event(zm, ZoneEvent.CONTACT_OPEN, item)
        else:
            dispatch_event(zm, ZoneEvent.CONTACT_CLOSED, item)

    item.listen_event(handler, ValueChangeEvent)

    return sensor


def _create_motion_sensor(zm: ImmutableZoneManager, item) -> MotionSensor:
    """
    Creates a MotionSensor and register for change event.
    :param item: SwitchItem
    :return: MotionSensor
    """
    sensor = MotionSensor(item)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item):
            zm.update_device_last_activated_time(item)
            dispatch_event(zm, ZoneEvent.MOTION, item)

    item.listen_event(handler, ValueChangeEvent)

    return sensor


def _create_humidity_sensor(zm: ImmutableZoneManager, item) -> HumiditySensor:
    """
    Creates a MotionSensor and register for change event.
    :param item: SwitchItem
    """
    sensor = HumiditySensor(item)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        dispatch_event(zm, ZoneEvent.HUMIDITY_CHANGED, item)

    item.listen_event(handler, ValueChangeEvent)

    return sensor


def _create_network_presence_device(zm: ImmutableZoneManager, item) -> NetworkPresence:
    """
    Creates a MotionSensor and register for change event.
    :param item: SwitchItem
    """
    sensor = NetworkPresence(item)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item):
            zm.on_network_device_connected(pe.get_event_dispatcher(), item)

    item.listen_event(handler, ValueChangeEvent)

    return sensor


def _create_temperature_sensor(zm: ImmutableZoneManager, item) -> TemperatureSensor:
    """
    Creates a MotionSensor and register for change event.
    :param item: SwitchItem
    """
    sensor = TemperatureSensor(item)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        dispatch_event(zm, ZoneEvent.TEMPERATURE_CHANGED, item)

    item.listen_event(handler, ValueChangeEvent)

    return sensor


# noinspection PyUnusedLocal
def _create_plug(zm: ImmutableZoneManager, item) -> Plug:
    """
    Creates a smart plug.
    :param item: SwitchItem
    :return: Plug
    """
    power_item_name = item.name + '_Power'
    if Items.item_exists(power_item_name):
        power_item = Items.get_item(power_item_name)
    else:
        power_item = None

    item_def = HABApp.openhab.interface.get_item(item.name, "alwaysOn")
    metadata = item_def.metadata
    always_on = True if "true" == _get_meta_value(metadata, "alwaysOn") else False

    return Plug(item, power_item, always_on)


def _create_gas_sensor(cls):
    """
    :return: a function that create the specific gas sensor type.
    """

    # noinspection PyUnusedLocal
    def inner_fcn(zm: ImmutableZoneManager, item) -> GasSensor:
        # noinspection PyUnusedLocal
        def state_change_handler(event: ValueChangeEvent):
            dispatch_event(zm, ZoneEvent.GAS_TRIGGER_STATE_CHANGED, item)

        # noinspection PyUnusedLocal
        def value_change_handler(event: ValueChangeEvent):
            dispatch_event(zm, ZoneEvent.GAS_VALUE_CHANGED, item)

        item.listen_event(value_change_handler, ValueChangeEvent)

        state_item = Items.get_item(item.name + 'State')
        state_item.listen_event(state_change_handler, ValueChangeEvent)

        return cls(item, state_item)

    return inner_fcn


def _create_alarm_partition(zm: ImmutableZoneManager, item: SwitchItem) -> AlarmPartition:
    """
    Creates an alarm partition.
    :param item: SwitchItem
    :return: AlarmPartition
    """
    arm_mode_item = Items.get_item(item.name + '_ArmMode')

    def handler(event: ValueChangeEvent):
        if AlarmState.ARM_AWAY == AlarmState(int(event.value)):
            dispatch_event(zm, ZoneEvent.PARTITION_ARMED_AWAY, item)
        elif AlarmState.UNARMED == AlarmState(int(event.value)) \
                and AlarmState.ARM_AWAY == AlarmState(int(event.old_value)):
            dispatch_event(zm, ZoneEvent.PARTITION_DISARMED_FROM_AWAY, item)

    arm_mode_item.listen_event(handler, ValueChangeEvent)

    return AlarmPartition(item, arm_mode_item)


# noinspection PyUnusedLocal
def _create_chrome_cast(zm: ImmutableZoneManager, item: StringItem) -> ChromeCastAudioSink:
    item_def = HABApp.openhab.interface.get_item(item.name, "sinkName")
    metadata = item_def.metadata

    sink_name = _get_meta_value(metadata, "sinkName", None)
    player_item = Items.get_item(item.name + "Player")
    volume_item = Items.get_item(item.name + "Volume")
    title_item = Items.get_item(item.name + "Title")
    idling_item = Items.get_item(item.name + "Idling")

    return ChromeCastAudioSink(sink_name, player_item, volume_item, title_item, idling_item)


def _create_switches(zm: ImmutableZoneManager,
                     item: Union[ColorItem, DimmerItem, NumberItem, SwitchItem]) \
        -> Union[None, Dimmer, Light, Fan, Wled]:
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

    if 'LightSwitch' == device_name or 'FanSwitch' == device_name or 'Wled_MasterControls' in device_name:
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
    elif 'Wled_MasterControls' in device_name:
        effect_item = Items.get_item(item.name.replace('MasterControls', 'FX'))
        primary_color_item = Items.get_item(item.name.replace('MasterControls', 'Primary'))
        secondary_color_item = Items.get_item(item.name.replace('MasterControls', 'Secondary'))

        device = Wled(item, effect_item, primary_color_item, secondary_color_item, duration_in_minutes)

    if device is not None:
        def handler(event: ValueChangeEvent):
            is_on = False
            is_off = False

            if isinstance(item, SwitchItem):
                is_on = pe.is_in_on_state(item)
                is_off = not is_on
            elif isinstance(item, DimmerItem):
                is_off = pe.get_number_value(item) == 0
                is_on = not is_off and event.old_value == 0
            elif isinstance(item, ColorItem):
                was_on = (event.old_value[2] > 0)  # index 2 for brightness
                was_off = int(event.old_value[2]) == 0  
                is_on = was_off and event.value[2] > 0
                is_off = was_on and int(event.value[2]) == 0

            if is_on:
                if not zm.on_switch_turned_on(pe.get_event_dispatcher(), item):
                    pe.log_debug(f'Switch on event for {item.name} is not processed.')
            elif is_off:
                if not zm.on_switch_turned_off(pe.get_event_dispatcher(), item):
                    pe.log_debug(f'Switch off event for {item.name} is not processed.')

        item.listen_event(handler, ValueChangeEvent)

    return device


def dispatch_event(zm: ImmutableZoneManager, zone_event: ZoneEvent, item: BaseValueItem):
    """
    Dispatches an event to the ZoneManager. If the event is not processed,
    create a debug log.
    """
    # pe.log_info(f"Dispatching event {zone_event.name} for {item.name}")
    if not zm.dispatch_event(zone_event, pe.get_event_dispatcher(), item):
        pe.log_debug(f'Event {zone_event} for item {item.name} is not processed.')


def _get_default_action_classes() -> List[Type]:
    """
    Retrieve a list of action class types defined in "aaa_modules.layout_model.actions".
    """
    classes = []

    import aaa_modules.layout_model.actions as actions

    for importer, module_name, is_pkg in pkgutil.iter_modules(actions.__path__):
        actions_package = "aaa_modules.layout_model.actions"
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
