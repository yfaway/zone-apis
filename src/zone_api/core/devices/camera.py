from datetime import datetime, timedelta
import os.path
import time

from zone_api.core.device import Device


class Camera(Device):
    """
    Represents a network camera.
    """

    def __init__(self, camera_name_item, camera_name, image_location='/home/pi/motion-os'):
        """
        Ctor

        :param StringItem camera_name_item: a dummy item; won't be used by this device.
        :param str camera_name: the optional file location of the still images
        :param str image_location: the optional file location of the still images
        :raise ValueError: if cameraNameItem is invalid
        """
        Device.__init__(self, camera_name_item)

        self._camera_name = camera_name
        self._image_location = image_location

    def has_motion_event(self):
        """
        Sleep for 10 seconds to wait for the images to be flushed to the file
        system. After that, check to see if there is any snapshot. If yes,
        return true.
        :rtype: bool
        """
        current_epoch = time.time()
        time.sleep(10)
        urls = self.get_snapshot_urls(current_epoch, 6, 5)
        return len(urls) > 0

    def get_snapshot_urls(self, time_in_epoch_seconds=time.time(),
                          max_number_of_seconds=15, offset_seconds=5):
        """
        Retrieve the still camera image URLs.
        :param float time_in_epoch_seconds: the pivot time to calculate the start
            and end times for the still images.
        :param int max_number_of_seconds: the maximum # of seconds to retrieve the
            images for
        :param int offset_seconds: the # of seconds before the epochSeconds to
            retrieve the images for
        :return: list of snapshot URLs or empty list if there is no snapshot
        :rtype: list(str)
        """
        return retrieve_snapshots_from_file_system(
            max_number_of_seconds, offset_seconds, time_in_epoch_seconds,
            self._camera_name, self._image_location)

    def __str__(self):
        """
        @override
        """
        return u"{}, cameraName: {}, imageLocation: {}".format(
            super(Camera, self).__str__(), self._camera_name, self._image_location)


def retrieve_snapshots_from_file_system(max_number_of_seconds=15, offset_seconds=5, epoch_seconds: float = time.time(),
                                        camera='Camera1', image_location='/home/pi/motion-os'):
    """
    Retrieve the still camera images from the specified folder. The image files
    must be in this folder structure:
        {year}-{month}-{day}/{hour}-{minute}-{sec}
    Example: 2019-11-06/22-54-02.jpg.
    If any of the field is less than 10, then it must be padded by '0'. These
    are the structures written out by MotionEyeOS.

    :param int max_number_of_seconds: the maximum # of seconds to retrieve the
        images for
    :param int offset_seconds: the # of seconds before the epochSeconds to
        retrieve the images for
    :param str camera: the name of the camera
    :param int epoch_seconds: the time the motion triggered time
    :param str image_location:
    :return: list of snapshot URLs or empty list if there is no snapshot
    :rtype: list(str)
    """

    def pad(x: int):
        return "0{}".format(x) if x < 10 else x

    urls = []

    if image_location.endswith('/'):
        image_location = image_location[:-1]

    current_time = datetime.fromtimestamp(epoch_seconds)
    path = "{}/{}/{}-{}-{}".format(image_location, camera, current_time.year,
                                   current_time.month, pad(current_time.day))

    for second in range(-offset_seconds, max_number_of_seconds - offset_seconds):
        delta = timedelta(seconds=second)
        instant = current_time + delta
        file_name = "{}-{}-{}.jpg".format(pad(instant.hour),
                                          pad(instant.minute), pad(instant.second))
        path_and_filename = "{}/{}".format(path, file_name)

        if os.path.exists(path_and_filename):
            url = "file://{}".format(path_and_filename)
            urls.append(url)

    return urls
