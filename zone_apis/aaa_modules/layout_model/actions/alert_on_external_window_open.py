from aaa_modules.alert import Alert
from aaa_modules.layout_model.devices.contact import Window
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.action import action


@action(events=[ZoneEvent.WINDOW_OPEN, ZoneEvent.WINDOW_CLOSED],
        devices=[Window], internal=False, external=True)
class AlertOnExternalWindowOpen:
    """
    Send an info alert when the window is open / closed.
    """

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        if event_info.get_event_type() == ZoneEvent.WINDOW_OPEN:
            alert_message = f'[Security] The {zone.get_name()} window is open.'
        else:
            alert_message = f'[Security] The {zone.get_name()} window is now closed.'

        alert = Alert.create_info_alert(alert_message)
        zone_manager.get_alert_manager().process_alert(alert, zone_manager)

        return True
