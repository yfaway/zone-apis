from threading import Timer

from zone_api.alert import Alert
from zone_api.core.devices.plug import Plug
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.contact import Door
from zone_api import platform_encapsulator as pe


@action(events=[ZoneEvent.DOOR_CLOSED], devices=[Door], internal=False, external=True)
class ArmAfterFrontDoorClosed:
    """
    Automatically arm the house if a front door was closed and there was no
    activity in the house for x number of seconds.
    Once armed, an alert will be sent out.
    """

    def __init__(self, max_elapsed_time_in_seconds: float = 15 * 60):
        """
        Ctor

        :param int max_elapsed_time_in_seconds: the elapsed time in second since a door has been
            closed at which point the timer will determine if there was any previous activity in
            the house. If not, the security system is armed. Note that a motion sensor might not
            switched to OFF until a few minutes later; do take this into consideration.
        :raise ValueError: if any parameter is invalid
        """

        if max_elapsed_time_in_seconds <= 0:
            raise ValueError('maxElapsedTimeInSeconds must be positive')

        self.timer = None
        self.max_elapsed_time_in_seconds = max_elapsed_time_in_seconds

    def on_action(self, event_info):
        events = event_info.get_event_dispatcher()
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        if zone.get_name() == "Patio":  # todo: add Zone::isBack()
            return False

        security_partitions = zone_manager.get_devices_by_type(AlarmPartition)
        if len(security_partitions) == 0:
            return False

        if not security_partitions[0].is_unarmed():
            return False

        for door in zone.get_devices_by_type(Door):
            if door.is_closed():
                if self.timer is not None:
                    self.timer.cancel()

                def arm_and_send_alert():
                    occupied = False
                    active_device = None

                    for z in zone_manager.get_zones():
                        if z.is_external():
                            continue

                        (occupied, active_device) = z.is_occupied([Plug], self.max_elapsed_time_in_seconds)
                        if occupied:
                            break

                    if occupied:
                        pe.log_info('Auto-arm cancelled (activities detected @ {}).'.format(
                            active_device))
                    else:
                        security_partitions[0].arm_away(events)

                        msg = 'The house has been automatically armed-away (front door closed and no activity)'
                        alert = Alert.create_warning_alert(msg)
                        zone_manager.get_alert_manager().process_alert(alert, zone_manager)

                self.timer = Timer(self.max_elapsed_time_in_seconds, arm_and_send_alert)
                self.timer.start()

        return True
