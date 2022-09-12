import random
from threading import Timer
from typing import Union, List

from zone_api.audio_manager import Genre, get_music_streams_by_genres, get_nearby_audio_sink
from zone_api.core.devices.weather import Weather
from zone_api.core.parameters import ParameterConstraint, positive_number_validator, Parameters
from zone_api.environment_canada import EnvCanada
from zone_api.core.action import action, Action
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.activity_times import ActivityType


@action(events=[ZoneEvent.MOTION], external_events=[ZoneEvent.DOOR_CLOSED],
        devices=[MotionSensor], activity_types=[ActivityType.WAKE_UP], zone_name_pattern='.*Kitchen.*')
class AnnounceMorningWeatherAndPlayMusic(Action):
    """
    Announces the current weather and plays a random music stream twice during the wake up period.
    This is based on the assumption of a household having two adults that leave work at different
    times. The music stops when the front door is closed.
    """

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [ParameterConstraint.optional('durationInMinutes', positive_number_validator),
                ParameterConstraint.optional('maximumStartCount', positive_number_validator)
                ]

    # noinspection PyDefaultArgument
    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._music_streams = get_music_streams_by_genres(
                     [Genre.CLASSICAL, Genre.INSTRUMENT, Genre.JAZZ])
        self._duration_in_minutes = self.parameters().get(self, self.supported_parameters()[-2].name(), 120)
        self._max_start_count = self.parameters().get(self, self.supported_parameters()[-1].name(), 2)
        self._in_session = False
        self._start_count = 0
        self._timer = None
        self._sink = None

    def on_action(self, event_info):

        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        def stop_music_session():
            self._sink.pause()
            self._in_session = False

        if event_info.get_event_type() == ZoneEvent.DOOR_CLOSED:
            if self._in_session:
                owning_zone = event_info.get_owning_zone()
                if owning_zone.is_external():
                    stop_music_session()
                    return True

            return False
        else:
            self._sink = get_nearby_audio_sink(zone, zone_manager)
            if self._sink is None:
                self.log_warning("Missing audio device; can't play music.")
                return False

            if not self._in_session and \
                    self._start_count < self._max_start_count:

                self._in_session = True

                weather_msg = self.get_morning_announcement(zone_manager)
                if weather_msg is not None:
                    self._sink.play_message(weather_msg)

                self._sink.play_stream(random.choice(self._music_streams), 40)

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
    def get_morning_announcement(self, zone_manager) -> Union[None, str]:
        """ Returns a string containing the current's weather and today's forecast. """

        weather = zone_manager.get_first_device_by_type(Weather)
        if weather is None or not weather.support_forecast_min_temperature() \
                or not weather.support_forecast_max_temperature():
            return None

        message = u'Good morning. It is {} degree currently; the weather ' \
                  'condition is {}. Forecasted temperature range is between {} and {} ' \
                  'degrees.'.format(weather.get_temperature(),
                                    weather.get_condition(),
                                    weather.get_forecast_min_temperature(),
                                    weather.get_forecast_max_temperature())

        forecasts = EnvCanada.retrieve_hourly_forecast('Ottawa', 12)
        rain_periods = [f for f in forecasts if
                        'High' == f.get_precipitation_probability() or
                        'Medium' == f.get_precipitation_probability()]
        if len(rain_periods) > 0:
            if len(rain_periods) == 1:
                message += u" There will be precipitation at {}.".format(
                    rain_periods[0].get_user_friendly_forecast_time())
            else:
                message += u" There will be precipitation from {} to {}.".format(
                    rain_periods[0].get_user_friendly_forecast_time(),
                    rain_periods[-1].get_user_friendly_forecast_time())

        return message
