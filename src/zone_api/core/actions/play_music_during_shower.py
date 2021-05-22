import random
from zone_api.audio_manager import get_nearby_audio_sink, get_music_streams_by_genres
from zone_api.core.action import action
from zone_api.core.devices.switch import Fan
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.activity_times import ActivityTimes
from zone_api.music_streams import Genre, MusicStreams


@action(events=[ZoneEvent.SWITCH_TURNED_ON, ZoneEvent.SWITCH_TURNED_OFF], devices=[Fan])
class PlayMusicDuringShower:
    """
    Play the provided URL stream when the washroom fan is turned on. Pause
    when it it turned off.
    Won't play if it is sleep time. Otherwise, adjust the volume based on the
    current activity.
    """

    # noinspection PyDefaultArgument
    def __init__(self, music_streams=[m.value for m in list(MusicStreams)]):
        """
        Ctor

        :param str music_streams: list of music streams
        :raise ValueError: if any parameter is invalid
        """
        if music_streams is None or len(music_streams) == 0:
            raise ValueError('music_streams must be specified')

        self._music_streams = music_streams

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        sink = get_nearby_audio_sink(zone, zone_manager)
        if sink is None:
            self.log_warning("Missing audio device; can't play music.")
            return False

        activity = None
        if zone_manager is not None:
            activities = zone_manager.get_devices_by_type(ActivityTimes)
            if len(activities) > 0:
                activity = activities[0]

                if activity.is_sleep_time():
                    return False

        if ZoneEvent.SWITCH_TURNED_ON == event_info.get_event_type():
            volume = 25 if (activity is not None and activity.is_quiet_time()) else 35
            sink.play_stream(random.choice(self._music_streams), volume)
        elif ZoneEvent.SWITCH_TURNED_OFF == event_info.get_event_type():
            sink.pause()

        return True
