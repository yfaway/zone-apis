from aaa_modules.alert_manager import *

from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition
from aaa_modules.layout_model.zone import ZoneEvent
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.camera import Camera
from aaa_modules.layout_model.devices.contact import Door
from aaa_modules import platform_encapsulator as pe


@action(events=[ZoneEvent.MOTION], devices=[Camera], internal=False, external=True)
class AlertOnEntranceActivity:
    """
    The alert is triggered from a PIR motion sensor. The motion sensor sometimes generate false
    positive event. This is remedied by determining if the camera also detects motion (through the
    image differential). If both the PIR sensor and the camera detect motions, sends an alert
    if the system is armed-away or if the activity is during the night.

    The alert is suppressed if the zone's door was just opened. This indicates the occupant walking
    out of the house, and thus shouldn't triggered the event.
    """

    def __init__(self):
        pass

    def onAction(self, event_info):
        zone = event_info.getZone()
        zone_manager = event_info.getZoneManager()

        current_epoch = time.time()

        door_open_period_in_seconds = 10
        for door in zone.getDevicesByType(Door):
            if door.wasRecentlyActivated(door_open_period_in_seconds):
                pe.log_info("A door was just open for zone {}; ignore motion event.".format(
                    zone.getName()))
                return

        cameras = zone.getDevicesByType(Camera)
        if len(cameras) == 0:
            pe.log_info("No camera found for zone {}".format(zone.getName()))
            return

        camera = cameras[0]
        if not camera.has_motion_event():
            pe.log_info("Camera doesn't indicate motion event; likely a false positive PIR event.")
            return

        time.sleep(10)  # wait for a bit to retrieve more images

        offset_seconds = 5
        max_number_of_seconds = 15
        attachment_urls = camera.get_snapshot_urls(current_epoch,
                                                   max_number_of_seconds, offset_seconds)

        if len(attachment_urls) > 0:
            time_struct = time.localtime()
            hour = time_struct[3]

            msg = 'Activity detected at the {} area.'.format(
                zone.getName(), len(attachment_urls))

            armed_away = False
            security_partitions = zone_manager.get_devices_by_type(AlarmPartition)
            if len(security_partitions) > 0 and security_partitions[0].is_armed_away():
                armed_away = True

            if armed_away or hour <= 6:
                alert = Alert.create_warning_alert(msg, None, attachment_urls)
            else:
                alert = Alert.create_audio_warning_alert(msg)

            zone_manager.get_alert_manager().process_alert(alert)

            return True
        else:
            pe.log_info("No images from {} camera.".format(zone.getName()))
            return False
