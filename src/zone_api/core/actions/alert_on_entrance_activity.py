import os

from zone_api.alert_manager import *

from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.parameters import Parameters
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action
from zone_api.core.devices.camera import Camera
from zone_api.core.devices.contact import Door
from zone_api import platform_encapsulator as pe


@action(events=[ZoneEvent.MOTION], devices=[Camera], internal=False, external=True)
class AlertOnEntranceActivity(Action):
    """
    The alert is triggered from a PIR motion sensor. The motion sensor sometimes generate false
    positive event. This is remedied by determining if the camera also detects motion (through the
    image differential). If both the PIR sensor and the camera detect motions, sends an alert
    if the system is armed-away or if the activity is during the night.

    The alert is suppressed if the zone's door was just opened. This indicates the occupant walking
    out of the house, and thus shouldn't trigger the event.
    """

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        current_epoch = time.time()

        door_open_period_in_seconds = 10
        for door in zone.get_devices_by_type(Door):
            if door.was_recently_activated(door_open_period_in_seconds):
                pe.log_info("A door was just open for zone {}; ignore motion event.".format(
                    zone.get_name()))
                return

        # noinspection PyTypeChecker
        camera: Camera = zone.get_first_device_by_type(Camera)
        if camera is None:
            pe.log_info("No camera found for zone {}".format(zone.get_name()))
            return

        # if not camera.has_motion_event():
        #    pe.log_info("Camera doesn't indicate motion event; likely a false positive PIR event.")
        #    return

        offset_seconds = 5
        max_number_of_seconds = 15
        attachment_paths = camera.get_snapshot_images(current_epoch, max_number_of_seconds, offset_seconds)

        if len(attachment_paths) > 0:
            time_struct = time.localtime()
            hour = time_struct[3]

            subject = 'Activity detected at the {} area.'.format(zone.get_name())
            body = (f"Motion sensor triggered while the house is armed away. Review {len(attachment_paths)} snapshot "
                    f"images below.")

            armed_away = False
            security_partition: AlarmPartition = zone_manager.get_first_device_by_type(AlarmPartition)
            if security_partition is not None and security_partition.is_armed_away():
                armed_away = True

            if armed_away or hour <= 6:
                alert = Alert.create_warning_alert(subject, body, attachment_paths)
            else:
                alert = Alert.create_audio_warning_alert(subject)

            self.send_notification(zone_manager, alert)

            for path in attachment_paths:  # delete the snapshot images
                os.remove(path)

            return True
        else:
            pe.log_warning("No images from {} camera.".format(zone.get_name()))
            return False
