from zone_api.alert import Alert
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.contact import Door, Window
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action


@action(events=[ZoneEvent.PARTITION_RECEIVE_ARM_AWAY, ZoneEvent.PARTITION_RECEIVE_ARM_STAY],
        devices=[AlarmPartition], unique_instance=True)
class AlertOnFailureToArm:
    """
    Send a info alert if an external door / windows was open when the system receives arm command.
    """

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        alert_message = None

        external_zones = [z for z in zone_manager.get_zones() if z.is_external() or z == zone]
        for z in external_zones:
            doors = [d for d in z.get_devices_by_type(Door) if d.is_open()]
            if len(doors) > 0:
                alert_message = f'Cannot arm; a door is open in the {zone.get_name()} area.'
                break

            windows = [w for w in z.get_devices_by_type(Window) if w.is_open()]
            if len(windows) > 0:
                alert_message = f'Cannot arm; a window is open in the {zone.get_name()} area.'
                break

        if alert_message is not None:
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)

        return True
