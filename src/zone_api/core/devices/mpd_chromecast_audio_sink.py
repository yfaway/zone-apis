from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink


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
