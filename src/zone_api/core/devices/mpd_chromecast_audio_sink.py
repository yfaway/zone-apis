from typing import Union

from zone_api import platform_encapsulator as pe
from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink
from zone_api.core.devices.mpd_controller import MpdController
from zone_api.music_streams import MusicStream


class MpdChromeCastAudioSink(ChromeCastAudioSink):
    """
    Represents a ChromeCast audio sink bound to a MPD server.
    @see https://www.musicpd.org/
    """

    def __init__(self, sink_name, player_item, volume_item, title_item, idling_item, out_current_stream_item=None):
        """
        Ctor

        :param str sink_name: the sink name for voice and audio play. The sink
            name can be retrieved by running "openhab-cli console" and then
            "smarthome:audio sinks".
        :param PlayerItem player_item:
        :param NumberItem volume_item:
        :param StringItem title_item:
        :param SwitchItemItem idling_item:
        :param StringItem out_current_stream_item: the optional item to display the current music stream name
        :raise ValueError: if any parameter is invalid
        """
        ChromeCastAudioSink.__init__(self, sink_name, player_item, volume_item, title_item, idling_item,
                                     out_current_stream_item)



    def play_stream(self, url_or_stream: Union[str, MusicStream], volume=None):
        """
        Override to always play the Mpd stream.
        """
        controller: MpdController = pe.get_zone_manager_from_context().get_first_device_by_type(MpdController)
        if controller is None:
            self.log_error("No MDP controller found.")
            return

        controller.shuffle_and_play()

        # Wait for a bit till MPC resumes the stream. Without this, the audio device might error out as
        # there is no audio stream.
        import time
        time.sleep(2)

        super(MpdChromeCastAudioSink, self).play_stream(controller.stream_url(), volume)
