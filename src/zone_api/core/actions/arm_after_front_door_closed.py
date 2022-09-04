from threading import Timer
from typing import List

from zone_api.alert import Alert
from zone_api.core.devices.plug import Plug
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.parameters import ParameterConstraint, positive_number_validator, Parameters
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.contact import Door
from zone_api import platform_encapsulator as pe


@action(events=[ZoneEvent.DOOR_CLOSED], devices=[Door], internal=False, external=True)
class ArmAfterFrontDoorClosed(Action):
    """
    Automatically arm the house if a front door was closed and there was no
    activity in the house for x number of seconds.
    Once armed, an alert will be sent out.
    """

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        """
        maxElapsedTimeInSeconds: the elapsed time in second since a door has been closed at which point the timer
        will determine if there was any previous activity in the house. If not, the security system is armed. Note that
        a motion sensor might not switched to OFF until a few minutes later; do take this into consideration.
        """
        return Action.supported_parameters() + \
               [ParameterConstraint.optional('maximumElapsedTimeInSeconds', positive_number_validator)]

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self.timer = None
        self.max_elapsed_time_in_seconds = self.parameters().get(self, self.supported_parameters()[-1].name(), 15 * 60)

    def on_action(self, event_info):
        events = event_info.get_event_dispatcher()
        zone = event_info.get_zone()
        zone_manager: ImmutableZoneManager = event_info.get_zone_manager()

        if zone.get_name() == "Patio":  # todo: add Zone::isBack()
            return False

        security_partition = zone_manager.get_first_device_by_type(AlarmPartition)
        if security_partition is None:
            return False

        if not security_partition.is_unarmed():
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
                    elif not security_partition.is_unarmed():
                        pe.log_info('Auto-arm cancelled (already armed).')
                    else:
                        security_partition.arm_away(events)

                        msg = 'The house has been automatically armed-away (front door closed and no activity)'
                        alert = Alert.create_warning_alert(msg)
                        self.send_notification(zone_manager, alert)

                self.timer = Timer(self.max_elapsed_time_in_seconds, arm_and_send_alert)
                self.timer.start()

        return True
