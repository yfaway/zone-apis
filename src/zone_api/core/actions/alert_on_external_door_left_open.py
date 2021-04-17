from threading import Timer

from zone_api.alert import Alert
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action
from zone_api.core.devices.contact import Door


@action(events=[ZoneEvent.DOOR_OPEN, ZoneEvent.DOOR_CLOSED],
        devices=[Door], internal=False, external=True)
class AlertOnExternalDoorLeftOpen:
    """
    Send an warning alert if a door on an external zone has been left open for
    a period of time.
    Triggered when a door is open (--> start the timer), or when a door is
    closed (--> stop the timer)
    """

    def __init__(self, max_elapsed_time_in_seconds: float = 15 * 60):
        """
        Ctor

        :param int max_elapsed_time_in_seconds: the elapsed time in second since
            a door has been open, and at which point an alert will be sent
        :raise ValueError: if any parameter is invalid
        """

        if max_elapsed_time_in_seconds <= 0:
            raise ValueError('maxElapsedTimeInSeconds must be positive')

        self.timers = {}
        self.maxElapsedTimeInSeconds = max_elapsed_time_in_seconds

    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        def send_alert():
            alert_message = 'The {} door has been opened for {} minutes.'.format(
                zone.get_name(), int(self.maxElapsedTimeInSeconds / 60))

            zone_manager.get_alert_manager().process_alert(Alert.create_warning_alert(alert_message), zone_manager)

        for door in zone.get_devices_by_type(Door):
            timer = self.timers[door] if door in self.timers else None

            if door.is_open():
                if timer is not None:
                    timer.cancel()
                    del self.timers[door]

                timer = Timer(self.maxElapsedTimeInSeconds, send_alert)
                timer.start()
                self.timers[door] = timer
            else:
                if timer is not None:
                    if timer.is_alive():
                        timer.cancel()
                    else:  # alert door now closed if a warning was previous sent
                        msg = f'The {zone.get_name()} door is now closed.'
                        alert = Alert.create_warning_alert(msg)
                        zone_manager.get_alert_manager().process_alert(alert, zone_manager)

                    del self.timers[door]

        return True

    def has_running_timer(self):
        """
        Returns true if at least one timer is running.
        """
        return any(t.is_alive() for t in self.timers.values())
