from zone_api.alert import Alert
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action
from zone_api.core.devices.gas_sensor import GasSensor


@action(events=[ZoneEvent.GAS_TRIGGER_STATE_CHANGED], devices=[GasSensor], unique_instance=True)
class AlertOnHighGasLevel:
    """
    Send a critical alert if the gas sensor is triggered (i.e. the reading
    is above the threshold).
    """

    def __init__(self, interval_between_alerts_in_minutes=15):
        """
        Ctor

        :raise ValueError: if any parameter is invalid
        """
        if interval_between_alerts_in_minutes <= 0:
            raise ValueError('intervalBetweenAlertsInMinutes must be positive')

        self._interval_between_alerts_in_minutes = interval_between_alerts_in_minutes
        self._alert = None

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        gas_sensor = zone.get_device_by_event(event_info)
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
