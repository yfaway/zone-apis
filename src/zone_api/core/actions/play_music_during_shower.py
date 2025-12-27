import random
from zone_api.audio_manager import get_nearby_audio_sink
from zone_api.core.action import action, Action
from zone_api.core.devices.switch import Fan
from zone_api.core.parameters import Parameters
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.activity_times import ActivityType, ActivityTimes
from zone_api.music_streams import MusicStreams


@action(events=[ZoneEvent.SWITCH_TURNED_ON, ZoneEvent.SWITCH_TURNED_OFF], excluded_activity_types=[ActivityType.SLEEP],
        devices=[Fan])
class PlayMusicDuringShower(Action):
    """
    Play the provided URL stream when the washroom fan is turned on. Pause
    when it it turned off.
    Won't play if it is sleep time. Otherwise, adjust the volume based on the
    current activity.
    """

    # noinspection PyDefaultArgument
    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._music_streams = [m.value for m in list(MusicStreams)]

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        sink = get_nearby_audio_sink(zone, zone_manager)
        if sink is None:
            self.log_warning(f"{zone.get_name()}: Missing audio device; can't play music.")
            return False

        activity = zone_manager.get_first_device_by_type(ActivityTimes)
        if ZoneEvent.SWITCH_TURNED_ON == event_info.get_event_type():
            volume = 25 if (activity is not None and activity.is_quiet_time()) else 35
            sink.play_stream(random.choice(self._music_streams), volume)
        elif ZoneEvent.SWITCH_TURNED_OFF == event_info.get_event_type():
            sink.pause()

        return True
