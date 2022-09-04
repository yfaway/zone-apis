from typing import List

from zone_api.core.parameters import Parameters, ParameterConstraint, positive_number_validator
from zone_api.core.zone import Level
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action
from zone_api.core.actions.range_violation_alert import RangeViolationAlert
from zone_api.core.devices.humidity_sensor import HumiditySensor


@action(events=[ZoneEvent.HUMIDITY_CHANGED], devices=[HumiditySensor], internal=True,
        levels=[Level.FIRST_FLOOR], unique_instance=True)
class AlertOnHumidityOutOfRange(Action):
    """
    Send an warning alert if the humidity is outside the range.
    @see RangeViolationAlert.
    """

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        min_humidity = self.parameters().get(self, 'minimumHumidity', 35)
        max_humidity = self.parameters().get(self, 'maximumHumidity', 50)
        notification_step_value = self.parameters().get(self, 'notificationStepValue', 3)

        if max_humidity <= min_humidity:
            raise ValueError('maxHumidity must be greater than minHumidity')

        self.rangeAlert = RangeViolationAlert(min_humidity, max_humidity,
                                              notification_step_value, "humidity", "%", "HUMIDITY", 60)

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [ParameterConstraint.optional('minimumHumidity', positive_number_validator, "must be positive"),
                ParameterConstraint.optional('maximumHumidity', positive_number_validator, "must be positive"),
                ParameterConstraint.optional('notificationStepValue', positive_number_validator, "must be positive")]

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        # noinspection PyTypeChecker
        sensor: HumiditySensor = event_info.get_device()
        percentage = sensor.get_humidity()
        self.rangeAlert.update_state(self, percentage, zone, zone_manager)

        return True
