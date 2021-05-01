import random
from threading import Timer

from zone_api.audio_manager import Genre, get_music_streams_by_genres, get_nearby_audio_sink
from zone_api.core.action import action
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.activity_times import ActivityTimes


@action(events=[ZoneEvent.MOTION], devices=[MotionSensor], zone_name_pattern='.*Kitchen.*')
class PlayMusicAtDinnerTime:
    """
    Chooses a random URL stream when the motion sensor in the kitchen is triggered at dinner time.
    Turns off after the specified period.
    """

    # noinspection PyDefaultArgument
    def __init__(self,
                 music_streams=get_music_streams_by_genres(
                     [Genre.CLASSICAL, Genre.INSTRUMENT, Genre.JAZZ]),
                 duration_in_minutes: float = 180):
        """
        Ctor

        :param list[str] music_streams: a list of music stream URL; a random stream will be selected
            from the list.
        :raise ValueError: if any parameter is invalid
        """

        if music_streams is None or len(music_streams) == 0:
            raise ValueError('musicUrls must be specified')

        self._music_streams = music_streams
        self._duration_in_minutes = duration_in_minutes
        self._in_session = False
        self._timer = None

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        activities = zone_manager.get_devices_by_type(ActivityTimes)
        if len(activities) == 0:
            self.log_warning("Missing ActivityTimes; can't determine if this is dinner time.")
            return False

        sink = get_nearby_audio_sink(zone, zone_manager)
        if sink is None:
            self.log_warning("Missing audio device; can't play music.")
            return False

        activity = activities[0]
        if activity.is_dinner_time():
            if not self._in_session:
                sink.play_stream(random.choice(self._music_streams), 40)

                self._in_session = True

                def stop_music_session():
                    sink.pause()
                    self._in_session = False

                self._timer = Timer(self._duration_in_minutes * 60, stop_music_session)
                self._timer.start()

        return True
