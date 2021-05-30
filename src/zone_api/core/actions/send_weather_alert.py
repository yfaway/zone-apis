from zone_api import platform_encapsulator as pe
from zone_api.alert import Alert
from zone_api.core.devices.weather import Weather
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.environment_canada import EnvCanada
from zone_api.core.action import action


@action(events=[ZoneEvent.WEATHER_ALERT_CHANGED], devices=[Weather])
class SendWeatherAlert:
    def __init__(self, city: str = 'Ottawa'):
        self._city = city

    def on_action(self, event_info: EventInfo):
        zone_manager = event_info.get_zone_manager()

        alert_message, url, _ = EnvCanada.retrieve_alert(self._city)

        if alert_message is not None:
            subject = f"[Weather Alert] {event_info.get_device().get_alert()}"
            body = f"{alert_message}\nLink: {url}"

            alert = Alert.create_info_alert(subject, body)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)

            return True
        else:
            pe.log_info("No weather alert exists.")
            return False
