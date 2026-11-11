from asyncio import AbstractEventLoop
import logging
import smtplib
import ssl

from email.message import EmailMessage
from email.utils import make_msgid
import mimetypes

from typing import cast, List, Union, TYPE_CHECKING

from zone_api.core.zone_manager import ZoneManager
from zone_api.models import BaseItem, DimmerItem, NumberItem, StringItem, SwitchItem
from zone_api.openhab.oh_models import OpenHabStringItem, OpenHabSwitchItem

from zone_api.core.immutable_zone_manager import EmailSettings, ImmutableZoneManager

if TYPE_CHECKING:
    from zone_api.core.immutable_zone_manager import EmailSettings, ImmutableZoneManager

logger = logging.getLogger('ZoneApis')

ACTION_AUDIO_SINK_ITEM_NAME = 'AudioVoiceSinkName'
ACTION_TEXT_TO_SPEECH_MESSAGE_ITEM_NAME = 'TextToSpeechMessage'
ACTION_AUDIO_LOCAL_FILE_LOCATION_ITEM_NAME = 'AudioFileLocation'
ACTION_AUDIO_STREAM_URL_ITEM_NAME = 'AudioStreamUrl'
""" 
The previous 4 items are used to play TTS message and audio file/URL. 
The corresponding script to process these actions are in JSR223 side, within OpenHab.
"""

ZONE_MANAGER: 'ImmutableZoneManager'
MAIN_EVENT_LOOP: AbstractEventLoop

_in_unit_tests = False


def register_test_item(item: BaseItem) -> None:
    """ Register the given item with the runtime. """
    get_zone_manager_from_context().add_item(item)


def unregister_test_item(item) -> None:
    """ Unregister the given item with the runtime. """
    get_zone_manager_from_context().remove_item(item)


def add_zone_manager_to_context(zm: 'ImmutableZoneManager'):
    """
    Adds the zone manager instance to the context.

    :param ImmutableZoneManager zm:
    """
    global ZONE_MANAGER
    ZONE_MANAGER = zm

def get_zone_manager_from_context() -> 'ImmutableZoneManager':
    """
    Gets the zone manager from the context.

    :rtype ImmutableZoneManager:
    """
    return ZONE_MANAGER

def set_main_event_loop(loop):
    global MAIN_EVENT_LOOP
    MAIN_EVENT_LOOP = loop

def get_main_event_loop() -> AbstractEventLoop:
    return MAIN_EVENT_LOOP

def is_in_on_state(item: SwitchItem):
    """
    :param SwitchItem item:
    :return: True if the state is ON.
    """
    return item.is_on()

def set_number_value(item_or_item_name: Union[NumberItem, str], value: float):
    item:NumberItem
    if isinstance(item_or_item_name, str):
        item: NumberItem = cast(NumberItem, ZONE_MANAGER.get_item(item_or_item_name))
    else:
        item = item_or_item_name

    item.set_value(value)


def get_number_value(item_or_item_name: Union[NumberItem, DimmerItem, str]) -> Union[float, int]:
    item:NumberItem
    if isinstance(item_or_item_name, str):
        item: NumberItem = cast(NumberItem, ZONE_MANAGER.get_item(item_or_item_name))
    else:
        item = item_or_item_name

    return item.get_value() or 0


def set_string_value(item_or_item_name: Union[StringItem, str], value: str):
    item: StringItem
    if isinstance(item_or_item_name, str):
        item: StringItem = cast(StringItem, ZONE_MANAGER.get_item(item_or_item_name))
    else:
        item = item_or_item_name

    item.set_value(value)


def get_string_value(item_or_item_name: Union[StringItem, str]) -> str:
    item: StringItem
    if isinstance(item_or_item_name, str):
        item: StringItem = cast(StringItem, ZONE_MANAGER.get_item(item_or_item_name)) 
    else:
        item = item_or_item_name

    return item.get_value() or ""


def has_item(item_name: str):
    """ Returns true if the item name is present in the back store. """
    return ZONE_MANAGER.has_item(item_name)

def get_item(item_name: str):
    return ZONE_MANAGER.get_item(item_name)

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


def get_event_dispatcher():
    class EventDispatcher:
        pass
    return EventDispatcher()


def set_in_unit_tests():
    global _in_unit_tests
    global ZONE_MANAGER

    zm = ZoneManager()
    ZONE_MANAGER = zm.get_immutable_instance()
    if not is_in_unit_tests():
        _in_unit_tests = True


def is_in_unit_tests():
    return _in_unit_tests


def play_local_audio_file(sink_name: str, file_location: str):
    """ Plays a local audio file on the given audio sink. """
    #OpenHabStringItem.get_item(ACTION_AUDIO_SINK_ITEM_NAME).oh_post_update(sink_name)
    #OpenHabStringItem.get_item(ACTION_AUDIO_LOCAL_FILE_LOCATION_ITEM_NAME).oh_post_update(file_location)
    zm = get_zone_manager_from_context()
    cast(OpenHabStringItem, zm.get_item(ACTION_AUDIO_SINK_ITEM_NAME)).set_value(sink_name)
    cast(OpenHabStringItem, zm.get_item(ACTION_AUDIO_LOCAL_FILE_LOCATION_ITEM_NAME)).set_value(file_location)


def play_stream_url(sink_name: str, url: str):
    """ Plays a stream URL on the given audio sink. """
    #OpenHabStringItem.get_item(ACTION_AUDIO_SINK_ITEM_NAME).oh_post_update(sink_name)
    #OpenHabStringItem.get_item(ACTION_AUDIO_STREAM_URL_ITEM_NAME).oh_post_update(url)

    zm = get_zone_manager_from_context()
    cast(OpenHabStringItem, zm.get_item(ACTION_AUDIO_SINK_ITEM_NAME)).set_value(sink_name)
    cast(OpenHabStringItem, zm.get_item(ACTION_AUDIO_STREAM_URL_ITEM_NAME)).set_value(url)


def play_text_to_speech_message(sink_name: str, tts: str):
    """ Plays a text to speech message on the given audio sink. """
    #OpenHabStringItem.get_item(ACTION_AUDIO_SINK_ITEM_NAME).oh_post_update(sink_name)
    #OpenHabStringItem.get_item(ACTION_TEXT_TO_SPEECH_MESSAGE_ITEM_NAME).oh_post_update(tts)

    zm = get_zone_manager_from_context()
    cast(OpenHabStringItem, zm.get_item(ACTION_AUDIO_SINK_ITEM_NAME)).set_value(sink_name)
    cast(OpenHabStringItem, zm.get_item(ACTION_TEXT_TO_SPEECH_MESSAGE_ITEM_NAME)).set_value(tts)


def send_email(email_addresses: List[str], subject: str, body: str = '', images_paths: List[str] = None):
    """
    Send an email using the python library smtplib. The content of the email is formatted in html . If the images are
    provided, they will be embedded inline.
    If an error is encountered, it will be logged and this function will return immediately.

    :param List[str] email_addresses:
    :param str subject:
    :param str body: an optional body text; can be embedded html code.
    :param List[str] images_paths: the full paths to the attachment
    """

    if images_paths is None:
        images_paths = []

    if body is None:
        body = ''

    email_settings: 'EmailSettings' = get_zone_manager_from_context().email_settings
    message = EmailMessage()

    # @see https://stackoverflow.com/questions/920910/sending-multipart-html-emails-which-contain-embedded-images
    message["From"] = email_settings.from_email_address
    message["To"] = ";".join(email_addresses)
    message["Subject"] = subject

    message.set_content(body)  # set the plain text body

    image_htmls = ""
    image_ids = {}
    for path in images_paths:
        cid = make_msgid()
        image_ids[path] = cid

        # Image_cid looks like <long.random.number@xyz.com>.
        # To use it as the img src, we don't need `<` or `>` so we use [1:-1] to strip them off.
        image_htmls = f"{image_htmls}<p><img src=\"cid:{cid[1:-1]}\" /></p>\n"

    html_message = f"""\
    <html>
        <body>
            {body}
            <hr />
            {image_htmls}
        </body>
    </html>
    """
    message.add_alternative(html_message, subtype='html')

    # Now open the attachments and attach it to the email
    for path in images_paths:
        with open(path, 'rb') as img:
            # Determine the Content-Type of the image.
            maintype, subtype = mimetypes.guess_type(img.name)[0].split('/')
            message.get_payload()[1].add_related(img.read(), maintype=maintype, subtype=subtype, cid=image_ids[path])

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(email_settings.smtp_server, email_settings.port, context=context) as server:
            server.login(email_settings.from_email_address, email_settings.password)
            server.sendmail(email_settings.from_email_address, email_addresses, message.as_string())
    except Exception as e:
        log_error(str(e))


def change_ecobee_thermostat_hold_mode(mode: str):
    """ Change Ecobee thermostat to the specified mode via the Ecobee action in OpenHab. """
    #OpenHabStringItem.get_item('EcobeeThermostatHoldMode').oh_post_update(mode)
    cast(OpenHabStringItem, get_zone_manager_from_context().get_item('EcobeeThermostatHoldMode')).set_value(mode)


def resume_ecobee_thermostat_program():
    """ Resume the Ecobee thermostat via the Ecobee action in OpenHab. """
    cast(OpenHabSwitchItem, get_zone_manager_from_context().get_item('EcobeeThermostatResume')).on()
