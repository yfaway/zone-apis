from zone_api.alert import Alert
from zone_api.core.devices.water_leak_sensor import WaterLeakSensor
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action


@action(events=[ZoneEvent.WATER_LEAK_STATE_CHANGED], devices=[WaterLeakSensor], unique_instance=True)
class AlertOnWaterLeak:
    """
    Send a critical alert if a water leak is detected.
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

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        sensor = zone.get_device_by_event(event_info)

        if sensor.is_water_detected():
            self._notified = True
            alert_message = f'Water leak detected in {zone.get_name()}.'
            alert_module = alert_message
            alert = Alert.create_critical_alert(alert_message, None, [],
                                                alert_module, self._interval_between_alerts_in_minutes)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)

        elif self._notified:
            alert_message = f'No more water leak detected in {zone.get_name()}.'
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)
            self._notified = False

        return True
