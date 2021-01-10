import random
from threading import Timer

from aaa_modules import platform_encapsulator as pe
from aaa_modules.audio_manager import AudioManager, MusicStream
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.zone import ZoneEvent
from aaa_modules.layout_model.devices.activity_times import ActivityTimes


@action(events=[ZoneEvent.MOTION], devices=[MotionSensor], zone_name_pattern='.*Kitchen.*')
class PlayMusicAtDinnerTime:
    """
    Play the provided URL stream when the washroom fan is turned on. Pause
    when it it turned off.
    Won't play if it is sleep time. Otherwise, adjust the volume based on the
    current activity.
    """

    def __init__(self,
                 music_urls=[MusicStream.AUDIOPHILE_CLASSICAL.value,
                             MusicStream.CD101_9_NY_SMOOTH_JAZZ.value,
                             MusicStream.WWFM_CLASSICAL.value,
                             MusicStream.MEDITATION_YIMAGO_RADIO_4 ],
                 duration_in_minutes: float = 120):
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
        self._in_dinner_session = False
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
            if not self._in_dinner_session:
                sink.play_stream(random.choice(self._music_urls), 40)

                self._in_dinner_session = True

                self._timer = Timer(self._duration_in_minutes * 60, lambda: sink.pause())
                self._timer.start()

        return True
