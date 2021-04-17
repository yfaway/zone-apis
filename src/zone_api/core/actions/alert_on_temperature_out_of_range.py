from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action
from zone_api.core.actions.range_violation_alert import RangeViolationAlert
from zone_api.core.devices.temperature_sensor import TemperatureSensor


@action(events=[ZoneEvent.TEMPERATURE_CHANGED], devices=[TemperatureSensor], internal=True, unique_instance=True)
class AlertOnTemperatureOutOfRange:
    """
    Send an warning alert if the temperature is outside the range.
    @see RangeViolationAlert.
    """

    def __init__(self, min_temperature=16, max_temperature=30, notification_step_value=2):
        """
        Ctor

        :param int min_temperature: the minimum temperature in percentage.
        :param int max_temperature: the maximum temperature in percentage.
        :param int notification_step_value: the value at which point a notification email will be
            sent. E.g. with the default maxTemperature of 50 and the step value of 3, the first
            notification is at 53, and the next one is 56.
        :raise ValueError: if any parameter is invalid
        """

        if min_temperature <= 0:
            raise ValueError('minTemperature must be positive')

        if max_temperature <= 0:
            raise ValueError('maxTemperature must be positive')

        if max_temperature <= min_temperature:
            raise ValueError('maxTemperature must be greater than minTemperature')

        if notification_step_value <= 0:
            raise ValueError('notificationStepValue must be positive')

        self.rangeAlert = RangeViolationAlert(min_temperature, max_temperature,
                                              notification_step_value, "temperature", "C", "TEMPERATURE", 30, False)

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        percentage = event_info.get_device().get_temperature()
        self.rangeAlert.update_state(percentage, zone, zone_manager)

        return True
