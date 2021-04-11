import random

from aaa_modules.audio_manager import MusicStreams, MusicStream
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.chromecast_audio_sink import ChromeCastAudioSink
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone_event import ZoneEvent


@action(events=[ZoneEvent.PLAYER_NEXT, ZoneEvent.PLAYER_PREVIOUS],
        devices=[ChromeCastAudioSink])
class ControlMusicPlayer:
    """
    The Next and Previous events chooses a random music stream and plays it.
    """

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info: EventInfo):
        device: ChromeCastAudioSink = event_info.get_device()
        event_type = event_info.get_event_type()

        if event_type in [ZoneEvent.PLAYER_NEXT, ZoneEvent.PLAYER_PREVIOUS]:
            stream: MusicStream = random.choice(list(MusicStreams)).value
            device.play_stream(stream.url)

        return True
