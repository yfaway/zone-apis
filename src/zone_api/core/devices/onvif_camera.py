import requests
import tempfile
import time
from typing import List

from zone_api import platform_encapsulator as pe
from zone_api.core.devices.camera import Camera


class OnvifCamera(Camera):
    """
    Represents an ONVIF camera that provides an RTSP stream.
    """

    def __init__(self, camera_name_item, image_url_item, mjpeg_url_item, ffmpeg_control_item):
        """
        Ctor

        :param StringItem camera_name_item: a dummy item; won't be used by this device.
        :raise ValueError: if cameraNameItem is invalid
        """
        Camera.__init__(self, camera_name_item, image_url_item, mjpeg_url_item)

        self._ffmpeg_control_item = ffmpeg_control_item

    def is_ffmpeg_on(self) -> bool:
        return pe.is_in_on_state(self._ffmpeg_control_item)

    def turn_on_ffmpeg(self):
        pe.set_switch_state(self._ffmpeg_control_item, True)

    def turn_off_ffmpeg(self):
        pe.set_switch_state(self._ffmpeg_control_item, False)

    def get_snapshot_images(self, time_in_epoch_seconds=time.time(),
                            max_number_of_seconds=15, offset_seconds=5) -> List[str]:
        """
        Retrieve the still camera image paths. The caller is responsible to delete the images afterward.

        :param float time_in_epoch_seconds: the pivot time to calculate the start and end times for the still images.
                Not relevant for ONVIF cam; this function always return future images from the time the fcn is called.
        :param int max_number_of_seconds: the maximum # of seconds to retrieve the images for
        :param int offset_seconds: the # of seconds before the epochSeconds to retrieve the images for
                Not possible for ONVIF cam as no previous images are retrieved on demand when this function is called.
        :return: list of snapshot URLs
        :rtype: list(str)
        """

        paths = []
        tmp = tempfile.gettempdir()

        step_second = 2
        for index in range(1, max_number_of_seconds, step_second):  # wait every step seconds
            img_data = requests.get(self.image_url).content

            image_path = f"{tmp}/snapshot_{index}.jpg"
            with open(image_path, 'wb') as handler:
                handler.write(img_data)

            paths.append(image_path)

            time.sleep(step_second)

        return paths
