import random

from zone_api.audio_manager import MusicStreams, MusicStream
from zone_api.core.action import action, Action
from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent


@action(events=[ZoneEvent.PLAYER_PLAY, ZoneEvent.PLAYER_NEXT, ZoneEvent.PLAYER_PREVIOUS],
        has_all_devices=[ChromeCastAudioSink])
class ControlMusicPlayer(Action):
    """
    The Next and Previous events chooses a random music stream and plays it.
    """

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info: EventInfo):
        if not isinstance(event_info.get_device(), ChromeCastAudioSink):
            return False

        device: ChromeCastAudioSink = event_info.get_device()
        event_type = event_info.get_event_type()

        if event_type in [ZoneEvent.PLAYER_NEXT, ZoneEvent.PLAYER_PREVIOUS]:
            stream: MusicStream = random.choice(list(MusicStreams)).value
            device.play_stream(stream)
        elif event_type == ZoneEvent.PLAYER_PLAY:
            # Only handle the event if the device is not playing anything. Otherwise, we might have
            # been triggered automatically from playing a file / stream / TTS rather than the user
            # clicking.
            if not device.is_active():
                device.resume()

        return True
