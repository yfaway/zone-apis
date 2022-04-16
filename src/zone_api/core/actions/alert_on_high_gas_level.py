from typing import List

from zone_api.alert import Alert
from zone_api.core.parameters import Parameters, ParameterConstraint, positive_number_validator
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action
from zone_api.core.devices.gas_sensor import GasSensor


@action(events=[ZoneEvent.GAS_TRIGGER_STATE_CHANGED], devices=[GasSensor], unique_instance=True)
class AlertOnHighGasLevel(Action):
    """
    Send a critical alert if the gas sensor is triggered (i.e. the reading
    is above the threshold).
    """

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._interval_between_alerts_in_minutes = self.parameters().get(self, 'intervalBetweenAlertsInMinutes', 15)
        self._alert = None

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return [ParameterConstraint.optional('intervalBetweenAlertsInMinutes', positive_number_validator, "must be positive")]

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        # noinspection PyTypeChecker
        gas_sensor: GasSensor = zone.get_device_by_event(event_info)
        gas_type = gas_sensor.__class__.__name__

        if gas_sensor.is_triggered():
            alert_message = f'The {zone.get_name()} {gas_type} at {gas_sensor.get_value()} is above normal level.'
            self._alert = Alert.create_warning_alert(alert_message, None, [],
                                                     gas_type, self._interval_between_alerts_in_minutes)
            zone_manager.get_alert_manager().process_admin_alert(self._alert)

        elif self._alert is not None:
            alert_message = f'The {zone.get_name()} {gas_type} is back to normal.'
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_admin_alert(alert)
            self._alert.cancel()

        return True
