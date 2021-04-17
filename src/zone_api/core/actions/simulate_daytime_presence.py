import random
from threading import Timer

from zone_api import platform_encapsulator as pe
from zone_api import security_manager as sm
from zone_api.audio_manager import MusicStreams, get_main_audio_sink
from zone_api.core.action import action
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.activity_times import ActivityTimes


@action(events=[ZoneEvent.MOTION], devices=[MotionSensor], internal=False, external=True)
class SimulateDaytimePresence:
    """
    Play the provided URL stream when an external motion sensor is triggered
    and while the system is in arm-away mode, and when it is not sleep time.
    @todo: use local URL to avoid reliance on the Internet connection.
    """

    def __init__(self, music_url=MusicStreams.CLASSIC_ROCK_FLORIDA.value.url, music_volume=90,
                 play_duration_in_seconds: float = None):
        """
        Ctor

        :param str music_url: 
        :param int music_volume: percentage from 0 to 100 
        :param int play_duration_in_seconds: how long the music will be played. \
            If not specified, this value will be generated randomly.
        :raise ValueError: if any parameter is invalid
        """

        if music_url is None:
            raise ValueError('musicUrl must be specified')

        self.music_url = music_url
        self.music_volume = music_volume
        self.play_duration_in_seconds = play_duration_in_seconds
        self.timer = None

    def on_action(self, event_info):
        zone_manager = event_info.get_zone_manager()

        if not sm.is_armed_away(zone_manager):
            return False

        audio_sink = get_main_audio_sink(zone_manager)
        if audio_sink is None:
            pe.log_info(f"{self.__module__} - No audio sink available")
            return False

        activities = zone_manager.get_devices_by_type(ActivityTimes)
        if len(activities) > 0:
            if activities[0].is_sleep_time():
                return False

        audio_sink.play_stream(self.music_url, self.music_volume)

        if self.timer is not None:
            self.timer.cancel()

        duration_in_seconds = self.play_duration_in_seconds
        if duration_in_seconds is None:
            duration_in_seconds = random.randint(3 * 60, 10 * 60)

        self.timer = Timer(duration_in_seconds, lambda: audio_sink.pause())
        self.timer.start()

        pe.log_info(f"{self.__module__} - playing music for {duration_in_seconds} seconds")

        return True
