import re
from typing import Union, Dict, Any

import HABApp
from HABApp.core import Items
from HABApp.core.events import ValueChangeEvent, ValueUpdateEvent
from HABApp.core.items.base_item import BaseItem
from HABApp.openhab.events import ItemCommandEvent
from HABApp.openhab.events import ItemStateEvent
from HABApp.openhab.items import ColorItem, DimmerItem, NumberItem, SwitchItem, StringItem

from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device
from zone_api.core.devices.alarm_partition import AlarmPartition, AlarmState
from zone_api.core.devices.astro_sensor import AstroSensor
from zone_api.core.devices.camera import Camera
from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink
from zone_api.core.devices.computer import Computer
from zone_api.core.devices.contact import Door, GarageDoor, Window
from zone_api.core.devices.dimmer import Dimmer
from zone_api.core.devices.gas_sensor import GasSensor
from zone_api.core.devices.humidity_sensor import HumiditySensor
from zone_api.core.devices.illuminance_sensor import IlluminanceSensor
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.devices.network_presence import NetworkPresence
from zone_api.core.devices.plug import Plug
from zone_api.core.devices.switch import Light, Fan
from zone_api.core.devices.temperature_sensor import TemperatureSensor
from zone_api.core.devices.thermostat import EcobeeThermostat
from zone_api.core.devices.tv import Tv
from zone_api.core.devices.water_leak_sensor import WaterLeakSensor
from zone_api.core.devices.weather import Weather
from zone_api.core.devices.wled import Wled
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.zone_event import ZoneEvent

"""
This module contains a set of utility functions to create devices and their associated event handler.
They are independent from the OpenHab naming convention but they are HABApp specific.
"""


def create_switches(zm: ImmutableZoneManager,
                    item: Union[ColorItem, DimmerItem, NumberItem, SwitchItem]) \
        -> Union[None, Dimmer, Light, Fan, Wled]:
    """
    Parses and creates Dimmer, Fan or Light device.
    :param zm: the zone manager instance to dispatch the event.
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
        duration_in_minutes = int(get_meta_value(metadata, duration_in_minutes_key, -1))
        if duration_in_minutes == -1:
            raise ValueError(f"Missing durationInMinutes value for {item_name}'")
    else:
        duration_in_minutes = None

    device = None
    if 'LightSwitch' == device_name:
        no_premature_turn_off_time_range = get_meta_value(metadata, "noPrematureTurnOffTimeRange", None)

        if dimmable_key in metadata:
            config = metadata.get(dimmable_key).get('config')
            level = int(config.get('level'))
            time_ranges = config.get('timeRanges')

            device = Dimmer(item, duration_in_minutes, level, time_ranges,
                            illuminance_threshold_in_lux,
                            no_premature_turn_off_time_range)
        else:
            device = Light(item, duration_in_minutes,
                           illuminance_threshold_in_lux,
                           no_premature_turn_off_time_range)

    elif 'FanSwitch' == device_name:
        device = Fan(item, duration_in_minutes)
    elif 'Wled_MasterControls' in device_name:
        effect_item = Items.get_item(item.name.replace('MasterControls', 'FX'))
        primary_color_item = Items.get_item(item.name.replace('MasterControls', 'Primary'))
        secondary_color_item = Items.get_item(item.name.replace('MasterControls', 'Secondary'))

        device = Wled(item, effect_item, primary_color_item, secondary_color_item, duration_in_minutes)

    if device is not None:
        device = _configure_device(device, zm)

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
                if not zm.on_switch_turned_on(pe.get_event_dispatcher(), device, item):
                    pe.log_debug(f'Switch on event for {item.name} is not processed.')
            elif is_off:
                if not zm.on_switch_turned_off(pe.get_event_dispatcher(), device, item):
                    pe.log_debug(f'Switch off event for {item.name} is not processed.')

        item.listen_event(handler, ValueChangeEvent)

    return device


def create_alarm_partition(zm: ImmutableZoneManager, item: SwitchItem) -> AlarmPartition:
    """
    Creates an alarm partition.
    :param zm: the zone manager instance to dispatch the event.
    :param item: SwitchItem
    :return: AlarmPartition
    """
    arm_mode_item = Items.get_item(item.name + '_ArmMode')
    device = _configure_device(AlarmPartition(item, arm_mode_item), zm)

    def arm_mode_value_changed(event: ValueChangeEvent):
        if AlarmState.ARM_AWAY == AlarmState(int(event.value)):
            dispatch_event(zm, ZoneEvent.PARTITION_ARMED_AWAY, device, item)
        elif AlarmState.UNARMED == AlarmState(int(event.value)) \
                and AlarmState.ARM_AWAY == AlarmState(int(event.old_value)):
            dispatch_event(zm, ZoneEvent.PARTITION_DISARMED_FROM_AWAY, device, item)

    def arm_mode_value_received(event: ItemCommandEvent):
        if AlarmState.ARM_AWAY == AlarmState(int(event.value)):
            dispatch_event(zm, ZoneEvent.PARTITION_RECEIVE_ARM_AWAY, device, arm_mode_item)
        elif AlarmState.ARM_STAY == AlarmState(int(event.value)):
            dispatch_event(zm, ZoneEvent.PARTITION_RECEIVE_ARM_STAY, device, arm_mode_item)

    # noinspection PyUnusedLocal
    def state_change_handler(event: ValueChangeEvent):
        dispatch_event(zm, ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED, device, item)

    arm_mode_item.listen_event(arm_mode_value_changed, ValueChangeEvent)
    arm_mode_item.listen_event(arm_mode_value_received, ValueUpdateEvent)

    item.listen_event(state_change_handler, ValueChangeEvent)

    # noinspection PyTypeChecker
    return device


def create_chrome_cast(zm: ImmutableZoneManager, item: StringItem) -> ChromeCastAudioSink:
    item_def = HABApp.openhab.interface.get_item(item.name, "sinkName")
    metadata = item_def.metadata

    sink_name = get_meta_value(metadata, "sinkName", None)
    player_item = Items.get_item(item.name + "Player")
    volume_item = Items.get_item(item.name + "Volume")
    title_item = Items.get_item(item.name + "Title")
    idling_item = Items.get_item(item.name + "Idling")

    stream_title_name = item.name + "StreamTitle"
    stream_title_item = None
    if pe.has_item(stream_title_name):
        stream_title_item = Items.get_item(stream_title_name)

    device = _configure_device(ChromeCastAudioSink(
        sink_name, player_item, volume_item, title_item, idling_item, stream_title_item), zm)

    def player_command_event(event):
        event_map = {'NEXT': ZoneEvent.PLAYER_NEXT,
                     'PREVIOUS': ZoneEvent.PLAYER_PREVIOUS}
        if event.value in event_map.keys():
            event = event_map[event.value]
            dispatch_event(zm, event, device, player_item)

    player_item.listen_event(player_command_event, ItemCommandEvent)

    # noinspection PyTypeChecker
    return device


def get_meta_value(metadata: Dict[str, Any], key, default_value=None) -> str:
    """ Helper method to get the metadata value. """
    value = metadata.get(key)
    if value is None:
        return default_value
    else:
        return value['value']


def get_zone_id_from_item_name(item_name: str) -> Union[str, None]:
    """ Extract and return the zone id from the the item name. """
    pattern = '([^_]+)_([^_]+)_(.+)'

    match = re.search(pattern, item_name)
    if not match:
        return None

    level_string = match.group(1)
    location = match.group(2)

    return level_string + '_' + location


def create_camera(zm: ImmutableZoneManager, item: StringItem) -> Camera:
    """
    Creates a Camera.
    :param zm: the zone manager instance to dispatch the event.
    :param item: SwitchItem
    """
    zone_name = get_zone_id_from_item_name(item.name)

    # noinspection PyTypeChecker
    return _configure_device(Camera(item, zone_name), zm)


def create_motion_sensor(zm: ImmutableZoneManager, item) -> MotionSensor:
    """
    Creates a MotionSensor and register for change event.
    :param zm: the zone manager instance to dispatch the event.
    :param item: SwitchItem
    :return: MotionSensor
    """
    key_disable_triggering_switches = "disableTriggeringSwitches"
    item_def = HABApp.openhab.interface.get_item(item.name, f"{key_disable_triggering_switches}")
    metadata = item_def.metadata
    can_trigger_switches = False if "true" == get_meta_value(metadata, key_disable_triggering_switches) else True

    sensor = _configure_device(MotionSensor(item, True, can_trigger_switches), zm)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item):
            dispatch_event(zm, ZoneEvent.MOTION, sensor, item)

    item.listen_event(handler, ValueChangeEvent)

    # noinspection PyTypeChecker
    return sensor


def create_humidity_sensor(zm: ImmutableZoneManager, item) -> HumiditySensor:
    """
    Creates a MotionSensor and register for change event.
    :param zm: the zone manager instance to dispatch the event.
    :param item: SwitchItem
    """
    sensor = _configure_device(HumiditySensor(item), zm)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        dispatch_event(zm, ZoneEvent.HUMIDITY_CHANGED, sensor, item)

    item.listen_event(handler, ValueChangeEvent)

    # noinspection PyTypeChecker
    return sensor


def create_network_presence_device(zm: ImmutableZoneManager, item) -> NetworkPresence:
    """
    Creates a MotionSensor and register for change event.
    :param zm: the zone manager instance to dispatch the event.
    :param item: SwitchItem
    """
    sensor = _configure_device(NetworkPresence(item), zm)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item):
            zm.on_network_device_connected(pe.get_event_dispatcher(), sensor, item)

    item.listen_event(handler, ValueChangeEvent)

    # noinspection PyTypeChecker
    return sensor


def create_temperature_sensor(zm: ImmutableZoneManager, item) -> TemperatureSensor:
    """
    Creates a MotionSensor and register for change event.
    :param zm: the zone manager instance to dispatch the event.
    :param item: SwitchItem
    """
    sensor = _configure_device(TemperatureSensor(item), zm)

    item.listen_event(lambda event: dispatch_event(zm, ZoneEvent.TEMPERATURE_CHANGED, sensor, item),
                      ValueChangeEvent)

    # noinspection PyTypeChecker
    return sensor


def create_plug(zm: ImmutableZoneManager, item) -> Plug:
    """
    Creates a smart plug.
    :param zm: the zone manager instance to dispatch the event.
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
    always_on = True if "true" == get_meta_value(metadata, "alwaysOn") else False

    # noinspection PyTypeChecker
    return _configure_device(Plug(item, power_item, always_on), zm)


def create_gas_sensor(cls):
    """
    :return: a function that create the specific gas sensor type.
    """

    def inner_fcn(zm: ImmutableZoneManager, item) -> GasSensor:
        state_item = Items.get_item(item.name + 'State')

        sensor = _configure_device(cls(item, state_item), zm)

        # noinspection PyUnusedLocal
        def state_change_handler(event: ValueChangeEvent):
            dispatch_event(zm, ZoneEvent.GAS_TRIGGER_STATE_CHANGED, sensor, state_item)

        # noinspection PyUnusedLocal
        def value_change_handler(event: ValueChangeEvent):
            dispatch_event(zm, ZoneEvent.GAS_VALUE_CHANGED, sensor, item)

        item.listen_event(value_change_handler, ValueChangeEvent)
        state_item.listen_event(state_change_handler, ValueChangeEvent)

        # noinspection PyTypeChecker
        return sensor

    return inner_fcn


def create_door(zm: ImmutableZoneManager, item) -> Door:
    if 'garage' in pe.get_item_name(item).lower():
        sensor = GarageDoor(item)
    else:
        sensor = Door(item)

    sensor = _configure_device(sensor, zm)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item) or pe.is_in_open_state(item):
            dispatch_event(zm, ZoneEvent.DOOR_OPEN, sensor, item)
        else:
            dispatch_event(zm, ZoneEvent.DOOR_CLOSED, sensor, item)

    item.listen_event(handler, ValueChangeEvent)

    # noinspection PyTypeChecker
    return sensor


def create_window(zm: ImmutableZoneManager, item) -> Window:
    sensor = _configure_device(Window(item), zm)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item) or pe.is_in_open_state(item):
            dispatch_event(zm, ZoneEvent.WINDOW_OPEN, sensor, item)
        else:
            dispatch_event(zm, ZoneEvent.WINDOW_CLOSED, sensor, item)

    item.listen_event(handler, ValueChangeEvent)

    # noinspection PyTypeChecker
    return sensor


def create_water_leak_sensor(zm: ImmutableZoneManager, item) -> WaterLeakSensor:
    """
    Creates a water leak sensor and register for change event.
    :param zm: the zone manager instance to dispatch the event.
    :param item: SwitchItem
    :return: WaterLeakSensor
    """
    sensor = _configure_device(WaterLeakSensor(item), zm)
    item.listen_event(lambda event: dispatch_event(zm, ZoneEvent.WATER_LEAK_STATE_CHANGED, sensor, item),
                      ValueChangeEvent)

    # noinspection PyTypeChecker
    return sensor


def create_illuminance_sensor(zm: ImmutableZoneManager, item) -> IlluminanceSensor:
    """ Create an illuminance sensor. """
    # noinspection PyTypeChecker
    return _configure_device(IlluminanceSensor(item), zm)


def create_ecobee_thermostat(zm: ImmutableZoneManager, item) -> IlluminanceSensor:
    """
    Create an Ecobee thermostat and set up the event listener to trap the vacation setting via the Ecobee
    application.
    If the OH switch item 'Out_Vacation' is present, set its value to the vacation mode setting.
    """

    event_item_name = item.name.replace("EcobeeName", "FirstEvent_Type")
    event_item = Items.get_item(event_item_name)

    # noinspection PyTypeChecker
    device: EcobeeThermostat = _configure_device(EcobeeThermostat(item, event_item), zm)

    def handler(event: ValueChangeEvent):
        display_item_name = 'Out_Vacation'

        if device.is_in_vacation():
            dispatch_event(zm, ZoneEvent.VACATION_MODE_ON, device, event_item)
            if pe.has_item(display_item_name):
                pe.set_switch_state(display_item_name, True)
        elif event.old_value == EcobeeThermostat.VACATION_EVENT_TYPE:
            dispatch_event(zm, ZoneEvent.VACATION_MODE_OFF, device, event_item)
            if pe.has_item(display_item_name):
                pe.set_switch_state(display_item_name, False)

    event_item.listen_event(handler, ValueChangeEvent)

    # noinspection PyTypeChecker
    return device


def create_astro_sensor(zm: ImmutableZoneManager, item) -> AstroSensor:
    # noinspection PyTypeChecker
    device: AstroSensor = _configure_device(AstroSensor(item), zm)

    def handler(event: ValueChangeEvent):
        was_light_on_time = device.is_light_on_time(event.old_value)
        is_light_on_time = device.is_light_on_time(event.value)
        if was_light_on_time != is_light_on_time:
            if is_light_on_time:
                dispatch_event(zm, ZoneEvent.ASTRO_LIGHT_ON, device, item)
            else:
                dispatch_event(zm, ZoneEvent.ASTRO_LIGHT_OFF, device, item)

        if device.is_bed_time(event.value):
            dispatch_event(zm, ZoneEvent.ASTRO_BED_TIME, device, item)

    item.listen_event(handler, ValueChangeEvent)

    # noinspection PyTypeChecker
    return device


def create_television_device(zm: ImmutableZoneManager, item) -> Tv:
    """ Create an television device. """
    # noinspection PyTypeChecker
    return _configure_device(Tv(item), zm)


def create_computer(zm: ImmutableZoneManager, item) -> Computer:
    """ Create an computer device. """
    item_def = HABApp.openhab.interface.get_item(item.name, "name, alwaysOn")
    metadata = item_def.metadata

    name = get_meta_value(metadata, "name", None)
    always_on = True if get_meta_value(metadata, "alwaysOn", None) == "true" else False

    tmp_item_name = item.name + "_CpuTemperature"
    cpu_temperature_item = Items.get_item(tmp_item_name) if pe.has_item(tmp_item_name) else None

    tmp_item_name = item.name + "_GpuTemperature"
    gpu_temperature_item = Items.get_item(tmp_item_name) if pe.has_item(tmp_item_name) else None

    tmp_item_name = item.name + "_GpuFanSpeed"
    gpu_fan_speed_item = Items.get_item(tmp_item_name) if pe.has_item(tmp_item_name) else None

    device = _configure_device(Computer(
        name, cpu_temperature_item, gpu_temperature_item, gpu_fan_speed_item, always_on), zm)

    if cpu_temperature_item is not None:
        cpu_temperature_item.listen_event(
            lambda event: dispatch_event(zm, ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED, device, cpu_temperature_item),
            ValueChangeEvent)

    if gpu_temperature_item is not None:
        gpu_temperature_item.listen_event(
            lambda event: dispatch_event(zm, ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED, device, gpu_temperature_item),
            ValueChangeEvent)

    if gpu_fan_speed_item is not None:
        gpu_fan_speed_item.listen_event(
            lambda event: dispatch_event(zm, ZoneEvent.COMPUTER_GPU_FAN_SPEED_CHANGED, device, gpu_fan_speed_item),
            ValueChangeEvent)

    # noinspection PyTypeChecker
    return device


def create_weather(zm: ImmutableZoneManager, temperature_item: NumberItem) -> Union[None, Weather]:
    """
    Creates a weather device.
    :param zm: the zone manager instance to dispatch the event.
    :param temperature_item: the temperature weather item.
    """
    device_name_pattern = '(.*)_Temperature'
    match = re.search(device_name_pattern, temperature_item.name)
    if not match:
        return None

    device_name = match.group(1)
    humidity_item = Items.get_item(f"{device_name}_Humidity")
    condition_item = Items.get_item(f"{device_name}_Condition")

    item_name = f"{device_name}_Alert_Title"
    alert_item = Items.get_item(item_name) if pe.has_item(item_name) else None

    item_name = f"{device_name}_ForecastTempMin"
    forecast_min_temp_item = Items.get_item(item_name) if pe.has_item(item_name) else None

    item_name = f"{device_name}_ForecastTempMax"
    forecast_max_temp_item = Items.get_item(item_name) if pe.has_item(item_name) else None

    device = Weather(temperature_item, humidity_item, condition_item, alert_item, forecast_min_temp_item,
                     forecast_max_temp_item)
    device = _configure_device(device, zm)

    temperature_item.listen_event(
        lambda event: dispatch_event(
            zm, ZoneEvent.WEATHER_TEMPERATURE_CHANGED, device, temperature_item), ValueChangeEvent)

    humidity_item.listen_event(
        lambda event: dispatch_event(
            zm, ZoneEvent.WEATHER_HUMIDITY_CHANGED, device, humidity_item), ValueChangeEvent)

    condition_item.listen_event(
        lambda event: dispatch_event(
            zm, ZoneEvent.WEATHER_CONDITION_CHANGED, device, condition_item), ValueChangeEvent)

    alert_item.listen_event(
        lambda event: dispatch_event(
            zm, ZoneEvent.WEATHER_ALERT_CHANGED, device, alert_item), ValueChangeEvent)

    # noinspection PyTypeChecker
    return device


def dispatch_event(zm: ImmutableZoneManager, zone_event: ZoneEvent, device: Device, item: BaseItem):
    """
    Dispatches an event to the ZoneManager. If the event is not processed,
    create a debug log.
    """
    # pe.log_info(f"Dispatching event {zone_event.name} for {item.name}")
    if not zm.dispatch_event(zone_event, pe.get_event_dispatcher(), device, item):
        pe.log_debug(f'Event {zone_event} for item {item.name} is not processed.')


def _configure_device(device: Device, zm: ImmutableZoneManager) -> Device:
    """
    - Set a few properties on the device. Note that each setter returns a new device instance, and as such, this method
      should be called before configuring the event handler.
    - Also register the item state event for each item in the device to update the last activated timestamp.
    """
    device = device.set_channel(pe.get_channel(device.get_item()))
    device = device.set_zone_manager(zm)

    # Can't rely on item changed even to determine last activated time, as sometimes the device may send the same value
    # and that wouldn't trigger the item changed event.
    # However, we need to exclude a few sensor types that would falsely flag occupancy (occupancy determination is
    # based on the ON state in the last number of minutes).
    if not isinstance(device, MotionSensor) and not isinstance(device, NetworkPresence):
        for item in device.get_all_items():
            item.listen_event(lambda event: device.update_last_activated_timestamp(), ItemStateEvent)

    return device
