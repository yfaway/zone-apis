from datetime import timedelta

import HABApp

from aaa_modules import security_manager as sm
from aaa_modules import platform_encapsulator as pe
from aaa_modules.audio_manager import get_main_audio_sink
from aaa_modules.layout_model.devices.activity_times import ActivityTimes

BELL_URL = 'bell-outside.wav'
BELL_DURATION_IN_SECS = 15


class PlayMindfulnessBell(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.run_every(timedelta(minutes=1), timedelta(minutes=25), self.play_bell)

    # noinspection PyMethodMayBeStatic
    def play_bell(self):
        zm = pe.get_zone_manager_from_context()

        # not triggered if house is armed away
        if sm.is_armed_away(zm):
            return

        activities = zm.get_devices_by_type(ActivityTimes)
        if len(activities) == 0:
            pe.log_warning(f"{self.__class__.__name__}: missing activities time; can't play meditation bell.")
            return

        activity = activities[0]
        if activity.is_sleep_time():
            return

        if activity.is_quiet_time():
            volume = 40
        else:
            volume = 60

        sink = get_main_audio_sink(zm)
        sink.play_sound_file(BELL_URL, BELL_DURATION_IN_SECS, volume)


PlayMindfulnessBell()
