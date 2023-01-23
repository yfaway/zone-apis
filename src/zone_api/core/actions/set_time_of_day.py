from datetime import datetime, time
from typing import List

from zone_api import platform_encapsulator as pe
from zone_api.core.devices.astro_sensor import AstroSensor
from zone_api.core.event_info import EventInfo
from zone_api.core.parameters import ParameterConstraint, no_op_validator, Parameters, positive_number_validator
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action


@action(events=[ZoneEvent.STARTUP], devices=[], zone_name_pattern='.*Virtual.*')
class SetTimeOfDay(Action):
    """
    Set the time of day based on the sun position.
    The code below is based on https://community.openhab.org/t/design-pattern-time-of-day/15407/622.
    @depend Astro binding.
    """

    SUNRISE_TIME_ITEM: ParameterConstraint = ParameterConstraint.optional('sunriseTimeItemName', no_op_validator)
    SUNSET_TIME_ITEM: ParameterConstraint = ParameterConstraint.optional('sunsetTimeItemName', no_op_validator)
    EVENING_TIME_ITEM: ParameterConstraint = ParameterConstraint.optional('eveningTimeItemName', no_op_validator)
    CHECK_PERIOD: ParameterConstraint = ParameterConstraint.optional(
        'checkPeriodInMinutes', positive_number_validator, "must be positive")

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._sunrise_time_item_name = self.parameters().get(
            self, SetTimeOfDay.SUNRISE_TIME_ITEM.name(), 'vSunrise_Time')
        self._sunset_time_item_name = self.parameters().get(
            self, SetTimeOfDay.SUNSET_TIME_ITEM.name(), 'vSunset_Time')
        self._evening_time_item_name = self.parameters().get(
            self, SetTimeOfDay.EVENING_TIME_ITEM.name(), 'vEvening_Time')

        self._check_period_in_minutes = self.parameters().get(self, SetTimeOfDay.CHECK_PERIOD.name(), 1)

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [SetTimeOfDay.SUNRISE_TIME_ITEM, SetTimeOfDay.SUNSET_TIME_ITEM, SetTimeOfDay.EVENING_TIME_ITEM,
                SetTimeOfDay.CHECK_PERIOD]

    # noinspection PyMethodMayBeStatic
    def on_startup(self, event_info: EventInfo):
        self._set_time_of_day(event_info.get_zone_manager())

        def handle_timer_event():
            self.on_action(self.create_timer_event_info(event_info))

        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every(self._check_period_in_minutes).minutes.do(handle_timer_event)

    def on_action(self, event_info):
        self._set_time_of_day(event_info.get_zone_manager())

    def _set_time_of_day(self, zm):
        morning_start = time(hour=6)
        bed_start = time(hour=0)
        night_start = time(hour=23)

        day_start = pe.get_datetime_value(self._sunrise_time_item_name).time()
        evening_start = pe.get_datetime_value(self._sunset_time_item_name).time()
        afternoon_start = pe.get_datetime_value(self._evening_time_item_name).time()

        current_value = ''
        now = datetime.now().time()
        if morning_start <= now < day_start:
            current_value = "MORNING"
        elif day_start <= now < afternoon_start:
            current_value = "DAY"
        elif afternoon_start <= now < evening_start:
            current_value = "AFTERNOON"
        elif evening_start <= now < night_start:
            current_value = "EVENING"
        elif now >= night_start:
            current_value = "NIGHT"
        elif bed_start <= now < morning_start:
            current_value = "BED"

        sensor: AstroSensor = zm.get_first_device_by_type(AstroSensor)
        if sensor.current_period() != current_value:
            # noinspection PyProtectedMember
            sensor._set_current_period(current_value)
            self.log_info(f"Set day period to {current_value}")
