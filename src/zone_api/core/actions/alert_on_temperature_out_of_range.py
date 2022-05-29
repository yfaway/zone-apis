from typing import List

from zone_api.core.parameters import ParameterConstraint, positive_number_validator, Parameters
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action
from zone_api.core.actions.range_violation_alert import RangeViolationAlert
from zone_api.core.devices.temperature_sensor import TemperatureSensor


@action(events=[ZoneEvent.TEMPERATURE_CHANGED], devices=[TemperatureSensor], internal=True, unique_instance=True)
class AlertOnTemperatureOutOfRange(Action):
    """
    Send an warning alert if the temperature is outside the range.
    @see RangeViolationAlert.
    """

    MIN_TEMPERATURE_PARAM = ParameterConstraint.optional('minimumTemperature', positive_number_validator)
    MAX_TEMPERATURE_PARAM = ParameterConstraint.optional('maximumTemperature', positive_number_validator)
    NOTIFICATION_STEP_VALUE_PARAM = ParameterConstraint.optional('notificationStepValue', positive_number_validator)

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [AlertOnTemperatureOutOfRange.MIN_TEMPERATURE_PARAM, AlertOnTemperatureOutOfRange.MAX_TEMPERATURE_PARAM,
                AlertOnTemperatureOutOfRange.NOTIFICATION_STEP_VALUE_PARAM]

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        min_temperature = self.parameters().get(self, AlertOnTemperatureOutOfRange.MIN_TEMPERATURE_PARAM.name(), 16)
        max_temperature = self.parameters().get(self, AlertOnTemperatureOutOfRange.MAX_TEMPERATURE_PARAM.name(), 30)
        notification_step_value = self.parameters().get(
            self, AlertOnTemperatureOutOfRange.NOTIFICATION_STEP_VALUE_PARAM.name(), 2)

        if max_temperature <= min_temperature:
            raise ValueError('maxTemperature must be greater than minTemperature')

        self.rangeAlert = RangeViolationAlert(min_temperature, max_temperature,
                                              notification_step_value, "temperature", "C", "TEMPERATURE", 30, False)

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        # noinspection PyUnresolvedReferences
        percentage = event_info.get_device().get_temperature()
        self.rangeAlert.update_state(percentage, zone, zone_manager)

        return True
