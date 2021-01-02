from aaa_modules.layout_model.zone import Level, ZoneEvent
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.actions.range_violation_alert import RangeViolationAlert
from aaa_modules.layout_model.devices.humidity_sensor import HumiditySensor


@action(events=[ZoneEvent.HUMIDITY_CHANGED], devices=[HumiditySensor], internal=True, unique_instance=True)
class AlertOnHumidityOutOfRange:
    """
    Send an warning alert if the humidity is outside the range.
    @see RangeViolationAlert.
    """

    def __init__(self, min_humidity: int = 35, max_humidity: int = 50, notification_step_value: int = 3):
        """
        Ctor

        :param int min_humidity: the minimum humidity in percentage.
        :param int max_humidity: the maximum humidity in percentage.
        :param int notification_step_value: the value at which point a notification email will be sent.
            E.g. with the default maxHumidity of 50 and the step value of 3, the first notification is at 53,
            and the next one is 56.
        :raise ValueError: if any parameter is invalid
        """

        if min_humidity <= 0:
            raise ValueError('minHumidity must be positive')

        if max_humidity <= 0:
            raise ValueError('maxHumidity must be positive')

        if max_humidity <= min_humidity:
            raise ValueError('maxHumidity must be greater than minHumidity')

        if notification_step_value <= 0:
            raise ValueError('notificationStepValue must be positive')

        self.rangeAlert = RangeViolationAlert(min_humidity, max_humidity,
                                              notification_step_value, "humidity", "%", "HUMIDITY", 60, True)

    def onAction(self, event_info):
        zone = event_info.getZone()
        zone_manager = event_info.getZoneManager()

        percentage = self.get_first_device(event_info).get_humidity()
        self.rangeAlert.updateState(percentage, zone, zone_manager)

        return True