from aaa_modules.alert import Alert
from aaa_modules.layout_model.zone import ZoneEvent
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.gas_sensor import GasSensor


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
        self._notified = False

    def onAction(self, event_info):
        zone = event_info.getZone()
        zone_manager = event_info.getZoneManager()

        gas_sensor = zone.getDeviceByEvent(event_info)
        gas_type = gas_sensor.__class__.__name__

        if gas_sensor.is_triggered():
            self._notified = True
            alert_message = f'The {zone.getName()} {gas_type} at {gas_sensor.get_value()} is above normal level.'
            alert = Alert.create_critical_alert(alert_message, None, [],
                                                gas_type, self._interval_between_alerts_in_minutes)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)

        elif self._notified:
            alert_message = f'The {zone.getName()} {gas_type} is back to normal.'
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)

        return True
