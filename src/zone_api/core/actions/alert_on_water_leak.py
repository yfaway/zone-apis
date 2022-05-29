from typing import List

from zone_api.alert import Alert
from zone_api.core.devices.water_leak_sensor import WaterLeakSensor
from zone_api.core.parameters import ParameterConstraint, positive_number_validator, Parameters
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action


@action(events=[ZoneEvent.WATER_LEAK_STATE_CHANGED], devices=[WaterLeakSensor], unique_instance=True)
class AlertOnWaterLeak(Action):
    """
    Send a critical alert if a water leak is detected.
    """

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [ParameterConstraint.optional('intervalBetweenAlertsInMinutes', positive_number_validator)]

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._interval_between_alerts_in_minutes = self.parameters().get(
            self, self.supported_parameters()[-1].name(), 15)
        self._alert = None

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        # noinspection PyTypeChecker
        sensor: WaterLeakSensor = zone.get_device_by_event(event_info)

        if sensor.is_water_detected():
            alert_message = f'Water leak detected in {zone.get_name()}.'
            alert_module = alert_message
            self._alert = Alert.create_critical_alert(alert_message, None, [],
                                                      alert_module, self._interval_between_alerts_in_minutes)
            zone_manager.get_alert_manager().process_alert(self._alert, zone_manager)

        elif self._alert is not None:
            alert_message = f'No more water leak detected in {zone.get_name()}.'
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)
            self._alert.cancel()

        return True
