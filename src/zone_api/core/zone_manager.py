from threading import Timer
from typing import List, Union, Type

from zone_api import platform_encapsulator as pe
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.zone import Zone


class ZoneManager:
    """
    Contains a set of Zone instances.
    """

    def __init__(self):
        self.zones = {}  # map from string zoneId to Zone
        self.auto_report_watch_dog_timer = None

    def add_zone(self, zone: Zone):
        """
        Adds a zone.

        :param Zone zone: a Zone instance
        """
        if zone is None:
            raise ValueError('zone must not be None')

        self.zones[zone.get_id()] = zone

        return self

    def remove_zone(self, zone: Zone):
        """
        Removes a zone.

        :param Zone zone: a Zone instance
        """
        if zone is None:
            raise ValueError('zone must not be None')

        self.zones.pop(zone.get_id())

        return self

    def remove_all_zones(self):
        """ Removes all zone. """
        self.zones.clear()
        return self

    def get_zones(self) -> List[Zone]:
        """
        Returns a new list contains all zone.

        :rtype: list(Zone)
        """
        zones = [z for z in self.zones.values()]
        zones.sort(key=lambda z: z.get_display_order())

        return zones

    def get_zone_by_id(self, zone_id: str) -> Union[None, Zone]:
        """
        Returns the zone associated with the given zoneId.

        :param string zone_id: the value returned by Zone::get_id()
        :return: the associated zone or None if the zoneId is not found
        :rtype: Zone
        """
        zone = self.zones[zone_id] if zone_id in self.zones else None
        return zone

    def get_devices_by_type(self, cls: Type):
        """
        Returns a list of devices in all zones matching the given type.

        :param Type cls: the device type
        :rtype: list(Device)
        """
        if cls is None:
            raise ValueError('cls must not be None')

        devices = []
        for zone in self.zones.values():
            devices = devices + zone.get_devices_by_type(cls)

        return devices

    def start_auto_report_watch_dog(self, timer_interval_in_seconds=10 * 60,
                                    inactive_interval_in_seconds=10 * 60):
        """
        Starts a timer that run every timerIntervalInSeconds. When the timer is
        triggered, it will scan auto-report devices (Devices::isAutoReport),
        and if any of them hasn't been triggered in the last
        inactiveIntervalInSeconds, it will reset the item value.

        This method is safe to call multiple times (a new timer will be started
        and any old timer is cancelled).

        :param int timer_interval_in_seconds: the timer duration
        :param int inactive_interval_in_seconds: the inactive duration after which
            the device's value will be reset.
        :rtype: None
        """

        def reset_failed_auto_report_devices():
            devices = []
            for z in self.get_zones():
                [devices.append(d) for d in z.get_devices()
                 if d.is_auto_report() and
                 not d.was_recently_activated(inactive_interval_in_seconds)]

            if len(devices) > 0:
                item_names = []
                for d in devices:
                    item_names.append(d.get_item_name())
                    d.reset_value_states()

                pe.log_warning(
                    "AutoReport Watchdog: {} failed auto-report devices: {}".format(
                        len(devices), item_names))
            else:
                pe.log_debug("AutoReport Watchdog: no failed auto-report devices")

            # restart the timer
            self.auto_report_watch_dog_timer = Timer(
                timer_interval_in_seconds, reset_failed_auto_report_devices)
            self.auto_report_watch_dog_timer.start()

        self.stop_auto_report_watch_dog()

        self.auto_report_watch_dog_timer = Timer(
            timer_interval_in_seconds, reset_failed_auto_report_devices)
        self.auto_report_watch_dog_timer.start()
        pe.log_info("Started auto-report watchdog timer.")

    def stop_auto_report_watch_dog(self):
        if self.auto_report_watch_dog_timer is not None \
                and self.auto_report_watch_dog_timer.is_alive():
            self.auto_report_watch_dog_timer.cancel()
            self.auto_report_watch_dog_timer = None

    def get_immutable_instance(self) -> ImmutableZoneManager:
        """
        Return an immutable zone manager instance that contains the same data as in this object.
        :rtype: ImmutableZoneManager
        """
        return ImmutableZoneManager(self.get_zones,
                                    self.get_zone_by_id,
                                    self.get_devices_by_type)
