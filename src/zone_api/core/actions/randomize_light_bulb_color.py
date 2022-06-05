from random import randint
from threading import Timer
from typing import List

from zone_api.core.action import action, Action
from zone_api.core.devices.switch import ColorLight
from zone_api.core.event_info import EventInfo
from zone_api.core.parameters import Parameters, ParameterConstraint, positive_number_validator
from zone_api.core.zone_event import ZoneEvent


@action(events=[ZoneEvent.SWITCH_TURNED_ON], devices=[ColorLight])
class RandomizeLightBulbColor(Action):
    """
    On triggered, change the bulb color immediately. Then starts a timer with a random duration to change the
    bulb color again. Terminate if the bulb is switched off.
    """

    MIN_COLOR_DURATION_IN_MINUTES = ParameterConstraint.optional(
        'minimumColorDurationInMinutes', positive_number_validator)
    MAX_COLOR_DURATION_IN_MINUTES = ParameterConstraint.optional(
        'maximumColorDurationInMinutes', positive_number_validator)

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [RandomizeLightBulbColor.MIN_COLOR_DURATION_IN_MINUTES,
                RandomizeLightBulbColor.MAX_COLOR_DURATION_IN_MINUTES]

    def __init__(self, parameters: Parameters):
        """ Ctor """
        super().__init__(parameters)

        self.min_color_duration_in_minutes = self.parameters().get(
            self, RandomizeLightBulbColor.MIN_COLOR_DURATION_IN_MINUTES, 3)
        self.max_color_duration_in_minutes = self.parameters().get(
            self, RandomizeLightBulbColor.MAX_COLOR_DURATION_IN_MINUTES, 8)

        # noinspection PyTypeChecker
        self._timer: Timer = None

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info: EventInfo):
        # noinspection PyTypeChecker
        color_light: ColorLight = event_info.get_zone().get_first_device_by_type(ColorLight)

        def change_to_random_color():
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

            if self._terminate(color_light):
                return

            rgb = [randint(0, 255), randint(0, 255), randint(0, 255)]
            color_light.change_color(rgb)

            duration_in_seconds = randint(self.min_color_duration_in_minutes * 60,
                                          self.max_color_duration_in_minutes * 60)

            self._timer = Timer(duration_in_seconds, change_to_random_color)
            self._timer.start()

        change_to_random_color()

        return True

    # noinspection PyMethodMayBeStatic
    def _terminate(self, color_light: ColorLight):
        """ Returns true if the timer shouldn't be renewed again. """
        if not color_light.is_on():
            return True

        return False
