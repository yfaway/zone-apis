from HABApp.openhab.exceptions import ItemNotFoundError

try:
    import HABApp
except ImportError:
    from org.slf4j import Logger, LoggerFactory
    from org.eclipse.smarthome.core.types import UnDefType
    from org.eclipse.smarthome.core.library.types import DecimalType
    from org.eclipse.smarthome.core.library.items import StringItem
    from org.eclipse.smarthome.core.library.types import OnOffType
    from org.eclipse.smarthome.core.library.types import OpenClosedType

    from core.jsr223 import scope
    from core.testing import run_test

    logger = LoggerFactory.getLogger("org.eclipse.smarthome.model.script.Rules")
    _in_hab_app = False
else:
    import logging
    from typing import Tuple, List, Union, Dict, Any

    from HABApp.core import Items
    from HABApp.core.items import Item
    from HABApp.openhab.items import ContactItem, DimmerItem, NumberItem, StringItem, SwitchItem, PlayerItem
    from HABApp.openhab.definitions import OnOffValue
    from HABApp.core.events import ValueChangeEvent

    _in_hab_app = True
    logger = logging.getLogger('ZoneApis')

ACTION_AUDIO_SINK_ITEM_NAME = 'AudioVoiceSinkName'
ACTION_TEXT_TO_SPEECH_MESSAGE_ITEM_NAME = 'TextToSpeechMessage'
ACTION_AUDIO_LOCAL_FILE_LOCATION_ITEM_NAME = 'AudioFileLocation'
ACTION_AUDIO_STREAM_URL_ITEM_NAME = 'AudioStreamUrl'
""" 
The previous 4 items are used to play TTS message and audio file/URL. 
The corresponding script to process these actions are in JSR223 side, within OpenHab.
"""

_in_unit_tests = False


def is_in_hab_app() -> bool:
    return _in_hab_app


def register_test_item(item: Item) -> None:
    """ Register the given item with the runtime. """
    if is_in_hab_app():
        HABApp.core.Items.add_item(item)
    else:
        scope.itemRegistry.remove(item.getName())
        scope.itemRegistry.add(item)


def unregister_test_item(item) -> None:
    """ Unregister the given item with the runtime. """
    HABApp.core.Items.pop_item(item.name)


def is_in_on_state(item: SwitchItem):
    """
    :param SwitchItem item:
    :return: True if the state is ON.
    """
    if isinstance(item, SwitchItem):
        return item.is_on()

    return False


def is_in_open_state(item: ContactItem):
    """
    :param SwitchItem item:
    :return: True if the state is OPEN.
    """
    if isinstance(item, ContactItem):
        return item.is_open()

    return False


def create_number_item(name: str) -> NumberItem:
    return NumberItem(name)


def create_player_item(name: str) -> PlayerItem:
    return PlayerItem(name)


def create_dimmer_item(name: str, percentage: int = 0) -> DimmerItem:
    """
    :param name: the item name
    :param int percentage: 0 (OFF) to 100 (full brightness)
    :return: DimmerItem
    """
    return DimmerItem(name, percentage)


def create_switch_item(name: str, on=False) -> SwitchItem:
    """
    :param name: the item name
    :param on: if True, the state is ON, else the state is OFF
    :return: SwitchItem
    """
    return SwitchItem(name, OnOffValue.ON if on else OnOffValue.OFF)


def create_string_item(name: str) -> StringItem:
    return StringItem(name)


def set_switch_state(item: SwitchItem, on: bool):
    if is_in_unit_tests():
        item.set_value(OnOffValue.ON if on else OnOffValue.OFF)
    else:
        if on:
            item.on()
        else:
            item.off()


def set_dimmer_value(item: DimmerItem, percentage: int):
    if is_in_unit_tests():
        item.post_value(percentage)
    else:
        item.percent(percentage)


def get_dimmer_percentage(item: DimmerItem) -> int:
    return item.get_value(0)


def set_number_value(item: NumberItem, value: float):
    if is_in_unit_tests():
        item.post_value(value)
    else:
        item.oh_send_command(str(value))


def get_number_value(item: NumberItem) -> float:
    return int(item.get_value(0))


def set_string_value(item: StringItem, value: str):
    if is_in_unit_tests():
        item.post_value(value)
    else:
        item.oh_send_command(value)


def get_string_value(item: StringItem) -> str:
    return item.get_value()


def change_player_state_to_pause(item: PlayerItem):
    if is_in_unit_tests():
        item.set_value("PAUSE")
    else:
        item.oh_send_command("PAUSE")


def change_player_state_to_play(item: PlayerItem):
    if is_in_unit_tests():
        item.set_value("PLAY")
    else:
        item.oh_send_command("PLAY")


def is_player_playing(item: PlayerItem):
    return item.get_value() == "PLAY"


def get_item_name(item):
    return item.name


def register_value_change_event(item: Item, handler):
    item.listen_event(handler, ValueChangeEvent)


def log_debug(message: str):
    """ Log a debug message. """
    logger.debug(message)


def log_info(message: str):
    """ Log an info message. """
    logger.info(message)


def log_error(message: str):
    """ Log an error message. """
    logger.error(message)


def log_warning(message: str):
    """ Log an warning message. """
    logger.warning(message)


def get_channel(item) -> str:
    """
    Returns the OpenHab channel string linked with the item.

    :rtype: str the channel string or None if the item is not linked to
    a channel
    """
    if _in_hab_app:
        if is_in_unit_tests():
            return None
        else:
            try:
                item_def = HABApp.openhab.interface.get_item(item.name, "channel")
                metadata = item_def.metadata
                value = metadata.get("channel")
                return value['value'] if value is not None else None
            except ItemNotFoundError:
                return None
    else:
        from core import osgi
        from org.eclipse.smarthome.core.items import MetadataKey
        meta_registry = osgi.get_service("org.eclipse.smarthome.core.items.MetadataRegistry")

        channel_meta = meta_registry.get(
            MetadataKey('channel', item.getName()))
        if channel_meta is not None:
            return channel_meta.value
        else:
            return None


def get_event_dispatcher():
    if not is_in_unit_tests():
        class EventDispatcher:
            # noinspection PyMethodMayBeStatic
            def send_command(self, item_name: str, command: Any):
                HABApp.openhab.interface.send_command(item_name, command)

        return EventDispatcher()
    else:
        class TestEventDispatcher:
            # noinspection PyMethodMayBeStatic
            def send_command(self, item_name: str, command: Any):
                item = Items.get_item(item_name)
                if isinstance(item, SwitchItem):
                    item = SwitchItem.get_item(item_name)

                    if command == "ON":
                        item.post_value(OnOffValue.ON)
                    elif command == "OFF":
                        item.post_value(OnOffValue.OFF)
                elif isinstance(item, DimmerItem):
                    item.post_value(int(command))
                elif isinstance(item, NumberItem):
                    item.post_value(command)
                else:
                    log_error("type: {}".format(type(item)))
                    raise ValueError("Unsupported type for item '{}'".format(item_name))

        return TestEventDispatcher()


def set_in_unit_tests(value: bool):
    global _in_unit_tests
    _in_unit_tests = value


def is_in_unit_tests():
    return _in_unit_tests


def play_local_audio_file(sink_name: str, file_location: str):
    """ Plays a local audio file on the given audio sink. """
    HABApp.openhab.interface.send_command(ACTION_AUDIO_SINK_ITEM_NAME, sink_name)
    HABApp.openhab.interface.send_command(ACTION_AUDIO_LOCAL_FILE_LOCATION_ITEM_NAME, file_location)


def play_stream_url(sink_name: str, url: str):
    """ Plays a stream URL on the given audio sink. """
    HABApp.openhab.interface.send_command(ACTION_AUDIO_SINK_ITEM_NAME, sink_name)
    HABApp.openhab.interface.send_command(ACTION_AUDIO_STREAM_URL_ITEM_NAME, url)


def play_text_to_speech_message(sink_name: str, tts: str):
    """ Plays a text to speech message on the given audio sink. """
    HABApp.openhab.interface.send_command(ACTION_AUDIO_SINK_ITEM_NAME, sink_name)
    HABApp.openhab.interface.send_command(ACTION_TEXT_TO_SPEECH_MESSAGE_ITEM_NAME, tts)


def send_email(email_addresses: List[str], subject: str, body: str = '', attachment_urls: List[str] = None):
    """ Send an email using the OpenHab email action. """

    if attachment_urls is None:
        attachment_urls = []

    HABApp.openhab.interface.send_command('EmailSubject', f'HABApp: {subject}')
    HABApp.openhab.interface.send_command('EmailBody', body)
    HABApp.openhab.interface.send_command('EmailAttachmentUrls', ', '.join(attachment_urls))
    HABApp.openhab.interface.send_command('EmailAddresses', ', '.join(email_addresses))

