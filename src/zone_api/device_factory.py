import re
from typing import Union, Dict, Any

import HABApp
from HABApp.core import Items
from HABApp.core.events import ValueUpdateEventFilter, ValueChangeEventFilter, ValueChangeEvent
from HABApp.core.events.filter.event import TypeBoundEventFilter
from HABApp.core.items.base_item import BaseItem
from HABApp.openhab.events import ItemCommandEvent
from HABApp.openhab.events import ItemStateUpdatedEvent
from HABApp.openhab.items import ColorItem, DimmerItem, NumberItem, SwitchItem, StringItem

from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device
from zone_api.core.devices.deferred_auto_report_notification import DeferredAutoReportNotification
from zone_api.core.devices.alarm_partition import AlarmPartition, AlarmState
from zone_api.core.devices.astro_sensor import AstroSensor
from zone_api.core.devices.camera import Camera
from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink
from zone_api.core.devices.computer import Computer
from zone_api.core.devices.contact import Door, GarageDoor, Window
from zone_api.core.devices.dimmer import Dimmer
from zone_api.core.devices.flash_message import FlashMessage
from zone_api.core.devices.gas_sensor import GasSensor
from zone_api.core.devices.humidity_sensor import HumiditySensor
from zone_api.core.devices.ikea_remote_control import IkeaRemoteControl
from zone_api.core.devices.illuminance_sensor import IlluminanceSensor
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.devices.network_presence import NetworkPresence
from zone_api.core.devices.plug import Plug
from zone_api.core.devices.switch import Light, Fan, ColorLight
from zone_api.core.devices.temperature_sensor import TemperatureSensor
from zone_api.core.devices.thermostat import EcobeeThermostat
from zone_api.core.devices.tv import Tv
from zone_api.core.devices.water_leak_sensor import WaterLeakSensor
from zone_api.core.devices.weather import Weather
from zone_api.core.devices.wled import Wled
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.zone_event import ZoneEvent

"""
This module contains a set of utility functions to create devices from OpenHab items. The OpenHab items' events are
captured and transformed into ZoneEvent, and then dispatched.
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
    color_bulb_key = 'colorBulb'
    duration_in_minutes_key = 'durationInMinutes'
    disable_triggering_key = "disableTriggeringFromMotionSensor"

    item_def = HABApp.openhab.interface_sync.get_item(item.name)
    metadata = item_def.metadata

    if device_name.endswith('LightSwitch') or device_name.endswith('FanSwitch') or 'Wled_MasterControls' in device_name:
        duration_in_minutes = int(get_meta_value(metadata, duration_in_minutes_key, -1))
        if duration_in_minutes == -1:
            raise ValueError(f"Missing durationInMinutes value for {item_name}'")
    else:
        duration_in_minutes = None

    device = None
    if device_name.endswith('LightSwitch'):
        no_premature_turn_off_time_range = get_meta_value(metadata, "noPrematureTurnOffTimeRange", None)

        if dimmable_key in metadata:
            config = metadata.get(dimmable_key).get('config')
            level = int(config.get('level'))
            time_ranges = config.get('timeRanges')

            device = Dimmer(item, duration_in_minutes, level, time_ranges,
                            illuminance_threshold_in_lux,
                            no_premature_turn_off_time_range)
        else:
            color_bulb = True if "true" == get_meta_value(metadata, color_bulb_key, 'false') else False
            if color_bulb:
                color_item = Items.get_item(item_name + 'Color')
                device = ColorLight(item, color_item, duration_in_minutes, illuminance_threshold_in_lux,
                                    no_premature_turn_off_time_range)
            else:
                device = Light(item, duration_in_minutes, illuminance_threshold_in_lux,
                               no_premature_turn_off_time_range)

    elif device_name.endswith('FanSwitch'):
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

        item.listen_event(handler, ValueChangeEventFilter())

    return device


def create_alarm_partition(zm: ImmutableZoneManager, item: SwitchItem) -> AlarmPartition:
    """
    Creates an alarm partition. Handle the following events:
      - Partition arm mode changed.
      - Partition in alarm.
      - Keypad panic events.

    :param zm: the zone manager instance to dispatch the event.
    :param item: SwitchItem
    :return: AlarmPartition
    """
    arm_mode_item = Items.get_item(item.name + '_ArmMode')
    send_command_item = Items.get_item(item.name + '_SendCommand')
    # noinspection PyTypeChecker
    panel_fire_key_alarm_item: SwitchItem = Items.get_item(item.name + '_PanelFireKeyAlarm')
    # noinspection PyTypeChecker
    panel_ambulance_key_alarm_item: SwitchItem = Items.get_item(item.name + '_PanelAmbulanceKeyAlarm')
    # noinspection PyTypeChecker
    panel_police_key_alarm_item: SwitchItem = Items.get_item(item.name + '_PanelPoliceKeyAlarm')

    # noinspection PyTypeChecker
    device: AlarmPartition = _configure_device(
        AlarmPartition(item, arm_mode_item, send_command_item, panel_fire_key_alarm_item), zm)

    def arm_mode_value_changed(event: ValueChangeEvent):
        if AlarmState.ARM_AWAY == AlarmState(int(event.value)):
            dispatch_event(zm, ZoneEvent.PARTITION_ARMED_AWAY, device, item)
        elif AlarmState.UNARMED == AlarmState(int(event.value)) \
                and AlarmState.ARM_AWAY == AlarmState(int(event.old_value)):
            dispatch_event(zm, ZoneEvent.PARTITION_DISARMED_FROM_AWAY, device, item)

        # Reset the key pad alarm states on unarmed event.
        if AlarmState.UNARMED == AlarmState(int(event.value)):
            pe.set_switch_state(panel_fire_key_alarm_item, False)
            pe.set_switch_state(panel_ambulance_key_alarm_item, False)
            pe.set_switch_state(panel_police_key_alarm_item, False)

    def arm_mode_value_received(event: ItemCommandEvent):
        if AlarmState.ARM_AWAY == AlarmState(int(event.value)):
            dispatch_event(zm, ZoneEvent.PARTITION_RECEIVE_ARM_AWAY, device, arm_mode_item)
        elif AlarmState.ARM_STAY == AlarmState(int(event.value)):
            dispatch_event(zm, ZoneEvent.PARTITION_RECEIVE_ARM_STAY, device, arm_mode_item)

    # noinspection PyUnusedLocal
    def in_alarm_state_change_handler(event: ValueChangeEvent):
        if not device.is_in_fire_alarm():
            dispatch_event(zm, ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED, device, item)

    # noinspection PyUnusedLocal
    def fire_alarm_state_change_handler(event: ValueChangeEvent):
        dispatch_event(zm, ZoneEvent.PARTITION_FIRE_ALARM_STATE_CHANGED, device, panel_fire_key_alarm_item)

    arm_mode_item.listen_event(arm_mode_value_changed, ValueChangeEventFilter())
    arm_mode_item.listen_event(arm_mode_value_received, ValueUpdateEventFilter())

    item.listen_event(in_alarm_state_change_handler, ValueChangeEventFilter())
    panel_fire_key_alarm_item.listen_event(fire_alarm_state_change_handler, ValueChangeEventFilter())

    # Wire the DSC key panels to the soft items. See notes in the .items file.
    def wire_soft_panel_events(dsc_item, panel_item):
        # noinspection PyUnusedLocal
        def handler(event: ValueChangeEvent):
            # We don't propagate the OFF state to work around a limitation on the DSC panel (the RESTORE event is sent
            # immediately).
            if pe.is_in_on_state(dsc_item):
                pe.set_switch_state(panel_item, True)

        dsc_item.listen_event(handler, ValueChangeEventFilter())

    wire_soft_panel_events(Items.get_item(item.name + '_DscPanelFireKeyAlarm'), panel_fire_key_alarm_item)
    wire_soft_panel_events(Items.get_item(item.name + '_DscPanelAmbulanceKeyAlarm'), panel_ambulance_key_alarm_item)
    wire_soft_panel_events(Items.get_item(item.name + '_DscPanelPoliceKeyAlarm'), panel_police_key_alarm_item)

    # noinspection PyTypeChecker
    return device


def create_chrome_cast(zm: ImmutableZoneManager, item: StringItem) -> ChromeCastAudioSink:
    item_def = HABApp.openhab.interface_sync.get_item(item.name)
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

    class ItemCommandEventFilter(TypeBoundEventFilter):
        def __init__(self):
            super().__init__(ItemCommandEvent)

    player_item.listen_event(player_command_event, ItemCommandEventFilter())

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
    in_alarm_name = item.name + "_InAlarm"
    in_alarm_item = None
    if pe.has_item(in_alarm_name):
        in_alarm_item = Items.get_item(in_alarm_name)

    battery_percentage_name = item.name + "_BatteryPercentage"
    battery_percentage_item = None
    if pe.has_item(battery_percentage_name):
        battery_percentage_item = Items.get_item(battery_percentage_name)

    key_disable_triggering_switches = "disableTriggeringSwitches"
    item_def = HABApp.openhab.interface_sync.get_item(item.name)
    metadata = item_def.metadata
    can_trigger_switches = False if "true" == get_meta_value(metadata, key_disable_triggering_switches) else True

    sensor = _configure_device(
        MotionSensor(item, can_trigger_switches, in_alarm_item, battery_percentage_item), zm)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item):
            dispatch_event(zm, ZoneEvent.MOTION, sensor, item)

    item.listen_event(handler, ValueChangeEventFilter())

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

    item.listen_event(handler, ValueChangeEventFilter())

    # noinspection PyTypeChecker
    return sensor


def create_ikea_remote_control(brightness_up_hold_event: ZoneEvent = None,
                               brightness_down_hold_event: ZoneEvent = None):
    """
    Creates an IKEARemoteControl and register events.
    :param brightness_up_hold_event: the event to fire when the bright up button is held.
    :param brightness_down_hold_event: the event to fire when the bright down button is held.
    """

    def inner_fcn(zm: ImmutableZoneManager, item) -> GasSensor:
        brightness_up_click_item = Items.get_item(item.name + "_BrightnessUpClick")
        brightness_up_hold_item = Items.get_item(item.name + "_BrightnessUpHold")

        brightness_down_click_item = Items.get_item(item.name + "_BrightnessDownClick")
        brightness_down_hold_item = Items.get_item(item.name + "_BrightnessDownHold")

        left_click_item = Items.get_item(item.name + "_ArrowLeftClick")
        left_hold_item = Items.get_item(item.name + "_ArrowLeftHold")

        right_click_item = Items.get_item(item.name + "_ArrowRightClick")
        right_hold_item = Items.get_item(item.name + "_ArrowRightHold")

        battery_item = Items.get_item(item.name + "_BatteryPercentage")

        sensor = _configure_device(
            IkeaRemoteControl(item, brightness_up_click_item, brightness_up_hold_item, brightness_down_click_item,
                              brightness_down_hold_item, left_click_item, left_hold_item, right_click_item,
                              right_hold_item, battery_item), zm)

        def register_event(control_item, mapped_zone_event):
            if mapped_zone_event is not None:
                # noinspection PyUnusedLocal
                def handler(event: ValueChangeEvent):
                    if pe.is_in_on_state(control_item):
                        dispatch_event(zm, mapped_zone_event, sensor, control_item)
                        sensor.reset_value_states()  # Set the switch to off to wait for the next triggering event.

                control_item.listen_event(handler, ValueChangeEventFilter())

        register_event(brightness_up_hold_item, brightness_up_hold_event)
        register_event(brightness_down_hold_item, brightness_down_hold_event)

        # noinspection PyTypeChecker
        return sensor

    return inner_fcn


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

    item.listen_event(handler, ValueChangeEventFilter())

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
                      ValueChangeEventFilter())

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

    item_def = HABApp.openhab.interface_sync.get_item(item.name)
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

        item.listen_event(value_change_handler, ValueChangeEventFilter())
        state_item.listen_event(state_change_handler, ValueChangeEventFilter())

        # noinspection PyTypeChecker
        return sensor

    return inner_fcn


def create_door(zm: ImmutableZoneManager, item) -> Door:
    in_alarm_name = item.name + "_InAlarm"
    in_alarm_item = None
    if pe.has_item(in_alarm_name):
        in_alarm_item = Items.get_item(in_alarm_name)

    if 'garage' in pe.get_item_name(item).lower():
        sensor = GarageDoor(item, in_alarm_item)
    else:
        sensor = Door(item, in_alarm_item)

    sensor = _configure_device(sensor, zm)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item) or pe.is_in_open_state(item):
            dispatch_event(zm, ZoneEvent.DOOR_OPEN, sensor, item)
        else:
            dispatch_event(zm, ZoneEvent.DOOR_CLOSED, sensor, item)

    item.listen_event(handler, ValueChangeEventFilter())

    # noinspection PyTypeChecker
    return sensor


def create_window(zm: ImmutableZoneManager, item) -> Window:
    in_alarm_name = item.name + "_InAlarm"
    in_alarm_item = None
    if pe.has_item(in_alarm_name):
        in_alarm_item = Items.get_item(in_alarm_name)

    sensor = _configure_device(Window(item, in_alarm_item), zm)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        if pe.is_in_on_state(item) or pe.is_in_open_state(item):
            dispatch_event(zm, ZoneEvent.WINDOW_OPEN, sensor, item)
        else:
            dispatch_event(zm, ZoneEvent.WINDOW_CLOSED, sensor, item)

    item.listen_event(handler, ValueChangeEventFilter())

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
                      ValueChangeEventFilter())

    # noinspection PyTypeChecker
    return sensor


def create_illuminance_sensor(zm: ImmutableZoneManager, item) -> IlluminanceSensor:
    """ Create an illuminance sensor. """
    # noinspection PyTypeChecker
    return _configure_device(IlluminanceSensor(item), zm)


def create_ecobee_thermostat(zm: ImmutableZoneManager, item) -> EcobeeThermostat:
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

    event_item.listen_event(handler, ValueChangeEventFilter())

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

    item.listen_event(handler, ValueChangeEventFilter())

    # noinspection PyTypeChecker
    return device


def create_television_device(zm: ImmutableZoneManager, item) -> Tv:
    """ Create an television device. """
    sensor = _configure_device(Tv(item), zm)

    # noinspection PyUnusedLocal
    def handler(event: ValueChangeEvent):
        zone_event = ZoneEvent.ENTERTAINMENT_ON if pe.is_in_on_state(item) else ZoneEvent.ENTERTAINMENT_OFF
        dispatch_event(zm, zone_event, sensor, item)

    item.listen_event(handler, ValueChangeEventFilter())

    # noinspection PyTypeChecker
    return sensor


def create_computer(zm: ImmutableZoneManager, item) -> Computer:
    """ Create an computer device. """
    item_def = HABApp.openhab.interface_sync.get_item(item.name)
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
            ValueChangeEventFilter())

    if gpu_temperature_item is not None:
        gpu_temperature_item.listen_event(
            lambda event: dispatch_event(zm, ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED, device, gpu_temperature_item),
            ValueChangeEventFilter())

    if gpu_fan_speed_item is not None:
        gpu_fan_speed_item.listen_event(
            lambda event: dispatch_event(zm, ZoneEvent.COMPUTER_GPU_FAN_SPEED_CHANGED, device, gpu_fan_speed_item),
            ValueChangeEventFilter())

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
    alert_title_item = Items.get_item(item_name) if pe.has_item(item_name) else None

    item_name = f"{device_name}_Alert_Date"
    alert_datetime_item = Items.get_item(item_name) if pe.has_item(item_name) else None

    item_name = f"{device_name}_ForecastTempMin"
    forecast_min_temp_item = Items.get_item(item_name) if pe.has_item(item_name) else None

    item_name = f"{device_name}_ForecastTempMax"
    forecast_max_temp_item = Items.get_item(item_name) if pe.has_item(item_name) else None

    device = Weather(temperature_item, humidity_item, condition_item, alert_title_item, alert_datetime_item,
                     forecast_min_temp_item, forecast_max_temp_item)
    device = _configure_device(device, zm)

    temperature_item.listen_event(
        lambda event: dispatch_event(
            zm, ZoneEvent.WEATHER_TEMPERATURE_CHANGED, device, temperature_item), ValueChangeEventFilter())

    humidity_item.listen_event(
        lambda event: dispatch_event(
            zm, ZoneEvent.WEATHER_HUMIDITY_CHANGED, device, humidity_item), ValueChangeEventFilter())

    condition_item.listen_event(
        lambda event: dispatch_event(
            zm, ZoneEvent.WEATHER_CONDITION_CHANGED, device, condition_item), ValueChangeEventFilter())

    alert_title_item.listen_event(
        lambda event: dispatch_event(
            zm, ZoneEvent.WEATHER_ALERT_CHANGED, device, alert_title_item), ValueChangeEventFilter())

    # noinspection PyTypeChecker
    return device


def create_auto_report_notification_setting(zm: ImmutableZoneManager, device_name_item: StringItem) \
        -> Union[None, DeferredAutoReportNotification]:
    """
    Creates deferred auto report notification item.
    :param zm: the zone manager instance to dispatch the event.
    :param device_name_item: the item tracking the device name
    """
    device_name_pattern = '(.*)_AutoReportDeviceName'
    match = re.search(device_name_pattern, device_name_item.name)
    if not match:
        return None

    name_prefix = match.group(1)
    duration_item = Items.get_item(f"{name_prefix}_AutoReportDeferredDurationInHour")

    device = DeferredAutoReportNotification(device_name_item, duration_item)
    device = _configure_device(device, zm)

    device_name_item.listen_event(
        lambda event: dispatch_event(
            zm, ZoneEvent.DEFERRED_NOTIFICATION_DEVICE_NAME_CHANGED, device, device_name_item),
        ValueChangeEventFilter())

    # noinspection PyTypeChecker
    return device


def create_flash_message(zm: ImmutableZoneManager, item: StringItem) -> Tv:
    # noinspection PyTypeChecker
    return _configure_device(FlashMessage(item), zm)


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
    class ItemStateUpdatedEventFilter(TypeBoundEventFilter):
        def __init__(self):
            super().__init__(ItemStateUpdatedEvent)

    if not isinstance(device, MotionSensor) and not isinstance(device, NetworkPresence):
        for item in device.get_all_items():
            item.listen_event(lambda event: device.update_last_activated_timestamp(), ItemStateUpdatedEventFilter())

    return device
