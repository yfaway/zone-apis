from aaa_modules import platform_encapsulator as pe
from aaa_modules.audio_manager import MusicStreams, get_nearby_audio_sink
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.switch import Fan
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.devices.activity_times import ActivityTimes


@action(events=[ZoneEvent.SWITCH_TURNED_ON, ZoneEvent.SWITCH_TURNED_OFF], devices=[Fan])
class PlayMusicDuringShower:
    """
    Play the provided URL stream when the washroom fan is turned on. Pause
    when it it turned off.
    Won't play if it is sleep time. Otherwise, adjust the volume based on the
    current activity.
    """

    def __init__(self, music_url: str = MusicStreams.CD101_9_NY_SMOOTH_JAZZ.value.url):
        """
        Ctor

        :param str music_url:
        :raise ValueError: if any parameter is invalid
        """

        if music_url is None:
            raise ValueError('musicUrl must be specified')

        self.music_url = music_url

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        sink = get_nearby_audio_sink(zone, zone_manager)
        if sink is None:
            pe.log_info(f"{self.__class__.__name__}: missing audio device; can't play music.")
            return False

        activity = None
        if zone_manager is not None:
            activities = zone_manager.get_devices_by_type(ActivityTimes)
            if len(activities) > 0:
                activity = activities[0]

                if activity.is_sleep_time():
                    return False

        if ZoneEvent.SWITCH_TURNED_ON == event_info.get_event_type():
            volume = 25 if (activity is not None and activity.isQuietTime()) else 35
            sink.play_stream(self.music_url, volume)
        elif ZoneEvent.SWITCH_TURNED_OFF == event_info.get_event_type():
            sink.pause()

        return True
