import random
from threading import Timer
from typing import List

from zone_api.audio_manager import Genre, get_music_streams_by_genres, get_nearby_audio_sink
from zone_api.core.action import action, Action
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.event_info import EventInfo
from zone_api.core.parameters import positive_number_validator, ParameterConstraint, Parameters
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.activity_times import ActivityType


@action(events=[ZoneEvent.MOTION], devices=[MotionSensor], activity_types=[ActivityType.DINNER],
        zone_name_pattern='.*Kitchen.*')
class PlayMusicAtDinnerTime(Action):
    """
    Chooses a random URL stream when the motion sensor in the kitchen is triggered at dinner time.
    Turns off after the specified period.
    """
    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [ParameterConstraint.optional('durationInMinutes', positive_number_validator)]

    # noinspection PyDefaultArgument
    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._music_streams = get_music_streams_by_genres([Genre.CLASSICAL, Genre.INSTRUMENT, Genre.JAZZ])
        self._duration_in_minutes = self.parameters().get(self, self.supported_parameters()[-1].name(), 180)
        self._in_session = False
        self._timer = None

    def on_action(self, event_info: EventInfo):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        sink = get_nearby_audio_sink(zone, zone_manager)
        if sink is None:
            self.log_warning("Missing audio device; can't play music.")
            return False

        if not self._in_session:
            sink.play_stream(random.choice(self._music_streams), 40)

            self._in_session = True

            def stop_music_session():
                sink.pause()
                self._in_session = False

            self._timer = Timer(self._duration_in_minutes * 60, stop_music_session)
            self._timer.start()

        return True
