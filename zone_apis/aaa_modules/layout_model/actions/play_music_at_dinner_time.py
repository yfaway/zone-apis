import random
from threading import Timer

from aaa_modules import platform_encapsulator as pe
from aaa_modules.audio_manager import AudioManager, Genre
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.zone import ZoneEvent
from aaa_modules.layout_model.devices.activity_times import ActivityTimes


@action(events=[ZoneEvent.MOTION], devices=[MotionSensor], zone_name_pattern='.*Kitchen.*')
class PlayMusicAtDinnerTime:
    """
    Chooses a random URL stream when the motion sensor in the kitchen is triggered at dinner time.
    Turns off after the specified period.
    """

    # noinspection PyDefaultArgument
    def __init__(self,
                 music_urls=AudioManager.get_music_streams_by_genres(
                     [Genre.CLASSICAL, Genre.INSTRUMENT, Genre.JAZZ]),
                 duration_in_minutes: float = 180):
        """
        Ctor

        :param list[str] music_urls: a list of music stream URL; a random stream will be selected
            from the list.
        :raise ValueError: if any parameter is invalid
        """

        if music_urls is None or len(music_urls) == 0:
            raise ValueError('musicUrls must be specified')

        self._music_urls = music_urls
        self._duration_in_minutes = duration_in_minutes
        self._in_session = False
        self._timer = None

    def onAction(self, event_info):
        zone = event_info.getZone()
        zone_manager = event_info.getZoneManager()

        activities = zone_manager.get_devices_by_type(ActivityTimes)
        if len(activities) == 0:
            pe.log_info(f"{self.__class__.__name__}: missing ActivityTimes; can't determine if this is dinner time.")
            return False

        sink = AudioManager.get_nearby_audio_sink(zone, zone_manager)
        if sink is None:
            pe.log_info(f"{self.__class__.__name__}: missing audio device; can't play music.")
            return False

        activity = activities[0]
        if activity.isDinnerTime():
            if not self._in_session:
                sink.play_stream(random.choice(self._music_urls), 40)

                self._in_session = True

                def stop_music_session():
                    sink.pause()
                    self._in_session = False

                self._timer = Timer(self._duration_in_minutes * 60, stop_music_session)
                self._timer.start()

        return True
