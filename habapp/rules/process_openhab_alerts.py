import HABApp
from HABApp.core.events import ValueChangeEvent, ValueChangeEventFilter
from HABApp.openhab.items import StringItem

from zone_api import platform_encapsulator as pe
from zone_api.alert import Alert
from zone_api.alert_manager import AlertManager


class ProcessOpenHabAlerts(HABApp.Rule):
    """
    Process alerts from OH's Xtend rules.
    This rule is temporary and will be removed when all OH rules are moved over to HABApp.
    """

    def __init__(self):
        super().__init__()

        item = StringItem.get_item('VT_AlertSender')
        self.listen_event(item, item_changed, ValueChangeEventFilter())


def item_changed(event: ValueChangeEvent):
    json = event.value
    alert = Alert.from_json(json)

    zm = pe.get_zone_manager_from_context()
    if not zm.get_alert_manager().process_alert(alert, zm):
        pe.log_info("Cannot send OH alert.")


ProcessOpenHabAlerts()
