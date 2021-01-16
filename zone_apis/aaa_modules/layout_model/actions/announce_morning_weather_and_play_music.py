import random
from threading import Timer

from aaa_modules import platform_encapsulator as pe
from aaa_modules.audio_manager import AudioManager, MusicStream, Genre
from aaa_modules.environment_canada import EnvCanada
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.zone import ZoneEvent
from aaa_modules.layout_model.devices.activity_times import ActivityTimes


@action(events=[ZoneEvent.MOTION], external_events=[ZoneEvent.CONTACT_CLOSED],
        devices=[MotionSensor], zone_name_pattern='.*Kitchen.*')
class AnnounceMorningWeatherAndPlayMusic:
    """
    Announces the current weather and plays a random music stream twice during the wake up period.
    This is based on the assumption of a household having two adults that leave work at different
    times. The music stops when the front door is closed.
    """

    # noinspection PyDefaultArgument
    def __init__(self,
                 music_urls=AudioManager.get_music_streams_by_genres(
                     [Genre.CLASSICAL, Genre.INSTRUMENT, Genre.JAZZ]),
                 duration_in_minutes: float = 120,
                 max_start_count: int = 2):
        """
        Ctor

        :param list[str] music_urls: a list of music stream URL; a random stream will be selected
            from the list.
        :raise ValueError: if any parameter is invalid
        """

        if music_urls is None or len(music_urls) == 0:
            raise ValueError('musicUrls must be specified')

        self._music_urls = music_urls
        self._max_start_count = max_start_count
        self._duration_in_minutes = duration_in_minutes
        self._in_session = False
        self._start_count = 0
        self._timer = None
        self._sink = None

    def onAction(self, event_info):

        zone = event_info.getZone()
        zone_manager = event_info.getZoneManager()

        activities = zone_manager.get_devices_by_type(ActivityTimes)
        if len(activities) == 0:
            pe.log_info(f"{self.__class__.__name__}: missing ActivityTimes; can't determine if this is dinner time.")
            return False

        def stop_music_session():
            self._sink.pause()
            self._in_session = False

        if event_info.getEventType() == ZoneEvent.CONTACT_CLOSED:
            if self._in_session:
                owning_zone = event_info.get_owning_zone()
                if owning_zone.isExternal():
                    stop_music_session()
                    return True

            return False
        else:
            self._sink = AudioManager.get_nearby_audio_sink(zone, zone_manager)
            if self._sink is None:
                pe.log_info(f"{self.__class__.__name__}: missing audio device; can't play music.")
                return False

            activity = activities[0]
            if activity.isWakeupTime() and \
                    not self._in_session and \
                    self._start_count < self._max_start_count:

                self._in_session = True

                weather_msg = self.get_morning_announcement()
                self._sink.play_message(weather_msg)
                self._sink.play_stream(random.choice(self._music_urls), 40)

                self._start_count += 1

                def reset_state():
                    stop_music_session()
                    self._sink = None
                    self._start_count = 0

                if self._timer is not None and self._timer.is_alive():
                    self._timer.cancel()

                self._timer = Timer(self._duration_in_minutes * 60, reset_state)
                self._timer.start()

        return True

    # noinspection PyMethodMayBeStatic
    def get_morning_announcement(self):
        """ Returns a string containing the current's weather and today's forecast. """

        message = u'Good morning. It is {} degree currently; the weather ' \
                  'condition is {}. Forecasted temperature range is between {} and {} ' \
                  'degrees.'.format(pe.get_number_value('VT_Weather_Temperature'),
                                    pe.get_string_value('VT_Weather_Condition'),
                                    pe.get_number_value('VT_Weather_ForecastTempMin'),
                                    pe.get_number_value('VT_Weather_ForecastTempMax'))

        forecasts = EnvCanada.retrieve_hourly_forecast('Ottawa', 12)
        rain_periods = [f for f in forecasts if
                        'High' == f.getPrecipationProbability() or
                        'Medium' == f.getPrecipationProbability()]
        if len(rain_periods) > 0:
            if len(rain_periods) == 1:
                message += u" There will be precipitation at {}.".format(
                    rain_periods[0].getUserFriendlyForecastTime())
            else:
                message += u" There will be precipitation from {} to {}.".format(
                    rain_periods[0].getUserFriendlyForecastTime(),
                    rain_periods[-1].getUserFriendlyForecastTime())

        return message
