from threading import Timer

from aaa_modules.alert import Alert
from aaa_modules.layout_model.zone import ZoneEvent
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition
from aaa_modules.layout_model.devices.contact import Door
from aaa_modules import platform_encapsulator as pe


@action(events=[ZoneEvent.CONTACT_CLOSED], devices=[Door], internal=False, external=True)
class ArmAfterFrontDoorClosed:
    """
    Automatically arm the house if a front door was closed and there was no
    activity in the house for x number of seconds.
    Once armed, an alert will be sent out.
    """

    def __init__(self, max_elapsed_time_in_seconds:float = 15 * 60):
        """
        Ctor

        :param int max_elapsed_time_in_seconds: the elapsed time in second since
            a door has been closed at which point the timer will determine if
            there was any previous activity in the house. If not, the security
            system is armed.
        :raise ValueError: if any parameter is invalid
        """

        if max_elapsed_time_in_seconds <= 0:
            raise ValueError('maxElapsedTimeInSeconds must be positive')

        self.timer = None
        self.max_elapsed_time_in_seconds = max_elapsed_time_in_seconds

    def onAction(self, event_info):
        events = event_info.getEventDispatcher()
        zone = event_info.getZone()
        zone_manager = event_info.getZoneManager()

        if zone.getName() == "Patio":  # todo: add Zone::isBack()
            return False

        security_partitions = zone_manager.get_devices_by_type(AlarmPartition)
        if len(security_partitions) == 0:
            return False

        if not security_partitions[0].is_unarmed():
            return False

        for door in zone.getDevicesByType(Door):
            if door.is_closed():
                if self.timer is not None:
                    self.timer.cancel()

                def arm_and_send_alert():
                    # Don't know why list comprehension version like below 
                    # doesn't work, Jython just hang on this statement:
                    # if not any(z.isOccupied(elapsedTime) for z in zoneManager.getZones()):
                    # Below is a work around.
                    occupied = False
                    active_device = None

                    for z in zone_manager.get_zones():
                        if z.isExternal():
                            continue

                        # motion sensor switches off after around 3', need to
                        # that into account.
                        motion_delay_in_sec = 3 * 60
                        delay_time_in_sec = self.max_elapsed_time_in_seconds + motion_delay_in_sec

                        (occupied, active_device) = z.isOccupied([], delay_time_in_sec)
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
