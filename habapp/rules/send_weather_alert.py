import HABApp
from HABApp.core.events import ValueChangeEvent
from HABApp.openhab.items import StringItem

from aaa_modules import platform_encapsulator as pe
from aaa_modules.alert import Alert
from aaa_modules.environment_canada import EnvCanada


class SendWeatherAlert(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.weather_item = StringItem.get_item('VT_Weather_Alert_Title')
        self.weather_item.listen_event(self.weather_alert_changed, ValueChangeEvent)

    # noinspection PyUnusedLocal
    def weather_alert_changed(self, event: ValueChangeEvent):
        alert_message, url, _ = EnvCanada.retrieve_alert('Ottawa')

        if alert_message is not None:
            subject = f"[Weather Alert] {self.weather_item.get_value()}"
            date_item = StringItem.get_item('VT_Weather_Alert_Date').get_value()
            body = f"{alert_message}\nLink: {url}\nPublished Date: {date_item}"

            alert = Alert.create_info_alert(subject, body)
            zm = pe.get_zone_manager_from_context()
            zm.get_alert_manager().process_alert(alert, zm)
        else:
            pe.log_info("No weather alert exists.")


SendWeatherAlert()
