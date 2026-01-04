import random
from threading import Timer
from typing import List

from zone_api import platform_encapsulator as pe
from zone_api import security_manager as sm
from zone_api.audio_manager import MusicStreams, get_main_audio_sink
from zone_api.core.action import action, Action
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.parameters import ParameterConstraint, percentage_validator, positive_number_validator, Parameters
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.activity_times import ActivityType


@action(events=[ZoneEvent.MOTION], devices=[MotionSensor], internal=False, external=True,
        excluded_activity_types=[ActivityType.SLEEP])
class SimulateDaytimePresence(Action):
    """
    Play the provided URL stream when an external motion sensor is triggered
    and while the system is in arm-away mode, and when it is not sleep time.
    @todo: use local URL to avoid reliance on the Internet connection.
    """

    MUSIC_URL = ParameterConstraint.optional('musicUrl')
    MUSIC_VOLUME = ParameterConstraint.optional('musicVolume', percentage_validator)
    PLAY_DURATION_IN_SECONDS = ParameterConstraint.optional('playDurationInSeconds', positive_number_validator)

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [SimulateDaytimePresence.MUSIC_URL, SimulateDaytimePresence.MUSIC_VOLUME,
                SimulateDaytimePresence.PLAY_DURATION_IN_SECONDS]

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self.music_url = self.parameters().get(
            self, SimulateDaytimePresence.MUSIC_URL.name(), MusicStreams.ROCK_BALLAD.value.url)
        self.music_volume = self.parameters().get(self, SimulateDaytimePresence.MUSIC_VOLUME.name(), 90)
        self.play_duration_in_seconds = self.parameters().get(
            self, SimulateDaytimePresence.PLAY_DURATION_IN_SECONDS.name(), None)

        self.timer = None

    def on_action(self, event_info):
        zone_manager = event_info.get_zone_manager()

        if not sm.is_armed_away(zone_manager):
            return False

        audio_sink = get_main_audio_sink(zone_manager)
        if audio_sink is None:
            pe.log_info(f"{self.__module__} - No audio sink available")
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
