import time
from zone_api import platform_encapsulator as pe
from zone_api.alert import Alert
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.contact import Door, Window
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action


@action(events=[ZoneEvent.PARTITION_RECEIVE_ARM_AWAY, ZoneEvent.PARTITION_RECEIVE_ARM_STAY],
        devices=[AlarmPartition], unique_instance=True)
class AlertOnFailureToArm(Action):
    """
    Send a info alert if an external door / windows was open when the system receives arm command.
    """

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        # Wait for the user to close the door first; otherwise we will get a lot of false notification in the regular
        # use case - arm before head out.
        if not pe.is_in_unit_tests():
            time.sleep(15)  # 15 secs

        alert_message = None

        for z in zone_manager.get_zones():
            doors = [d for d in z.get_devices_by_type(Door) if d.is_connected_to_security_system() and d.is_open()]
            if len(doors) > 0:
                alert_message = f'Cannot arm; a door is open in the {zone.get_name()} area.'
                break

            windows = [w for w in z.get_devices_by_type(Window) if w.is_connected_to_security_system() and w.is_open()]
            if len(windows) > 0:
                alert_message = f'Cannot arm; a window is open in the {zone.get_name()} area.'
                break

        if alert_message is not None:
            alert = Alert.create_info_alert(alert_message)
            self.send_notification(zone_manager, alert)

        return True
