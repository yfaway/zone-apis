from zone_api import security_manager as sm
from zone_api.audio_manager import get_nearby_audio_sink
from zone_api.audio_manager import get_main_audio_sink
from zone_api.core.action import action
from zone_api.core.devices.activity_times import ActivityTimes
from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink
from zone_api.core.event_info import EventInfo
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.zone import Level
from zone_api.core.zone_event import ZoneEvent


@action(events=[ZoneEvent.TIMER], devices=[ChromeCastAudioSink], levels=[Level.FIRST_FLOOR])
class PlayMindfulnessBell:
    """
    Play a bell sound every x minutes. This is a Zen Buddhist practice. When the bell rings, stop if
    possible and do a deep breath for a few times.
    """

    BELL_URL = 'bell-outside.wav'
    BELL_DURATION_IN_SECS = 15

    def on_startup(self, event_info: EventInfo):

        # start timer here. Main logic remains in on_action.
        def invoke_action():
            self.on_action(self.create_timer_event_info(event_info))

        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every(25).minutes.do(invoke_action)

    def on_action(self, event_info: EventInfo):
        zone = event_info.get_zone()
        zone_manager: ImmutableZoneManager = event_info.get_zone_manager()

        if sm.is_armed_away(zone_manager):
            return False

        activity = zone_manager.get_first_device_by_type(ActivityTimes)
        if activity is None:
            self.log_info("Missing activities time; can't play meditation bell.")
            return False

        sink = get_nearby_audio_sink(zone, zone_manager)
        if sink is None:
            self.log_warning("Missing audio device; can't play music.")
            return False

        if activity.is_sleep_time():
            return False

        if activity.is_quiet_time():
            volume = 40
        else:
            volume = 60

        sink = get_main_audio_sink(zone_manager)
        sink.play_sound_file(PlayMindfulnessBell.BELL_URL,
                             PlayMindfulnessBell.BELL_DURATION_IN_SECS, volume)

        return True
