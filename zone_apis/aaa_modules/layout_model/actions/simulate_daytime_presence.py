import random
from threading import Timer

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.zone import Level, ZoneEvent
from aaa_modules.layout_model.devices.activity_times import ActivityTimes
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition
from aaa_modules.layout_model.devices.chromecast_audio_sink import ChromeCastAudioSink


@action(events=[ZoneEvent.MOTION], devices=[MotionSensor], internal=False, external=True)
class SimulateDaytimePresence:
    """
    Play the provided URL stream when an external motion sensor is triggered
    and while the system is in arm-away mode, and when it is not sleep time.
    @todo: use local URL to avoid reliance on the Internet connection.
    """

    def __init__(self, music_url='http://hestia2.cdnstream.com:80/1277_192', music_volume=90,
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

    def onAction(self, event_info):
        zone_manager = event_info.getZoneManager()

        security_partitions = zone_manager.get_devices_by_type(AlarmPartition)
        if len(security_partitions) == 0:
            return False

        if not security_partitions[0].is_armed_away():
            return False

        # Get an audio sink from the first floor.
        audio_sink = None
        zones = [z for z in zone_manager.get_zones() if z.getLevel() == Level.FIRST_FLOOR]
        for z in zones:
            sinks = z.getDevicesByType(ChromeCastAudioSink)
            if len(sinks) > 0:
                audio_sink = sinks[0]
                break

        if audio_sink is None:
            pe.log_info(f"{self.__module__} - No audio sink available")
            return False

        activities = zone_manager.get_devices_by_type(ActivityTimes)
        if len(activities) > 0:
            if activities[0].isSleepTime():
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
