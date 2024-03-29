import datetime
from copy import copy
import time
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from zone_api.core.zone import Zone

from zone_api import platform_encapsulator as pe


class Device(object):
    """
    The base class that all other sensors and switches derive from.
    """

    def __init__(self, openhab_item, additional_items=None, battery_powered=False, wifi=False, auto_report=False,
                 battery_percentage_item=None):
        """
        Ctor

        :param Item openhab_item:
        :param bool battery_powered: indicates if the device is powered by battery.
        :param bool wifi: indicates if the device communicates by WiFi.
        :param bool auto_report: indicates if the device periodically reports its value.
        :param NumberItem battery_percentage_item: the remaining battery percentage or None if not applicable
        :raise ValueError: if any parameter is invalid
        """
        if additional_items is None:
            additional_items = []

        if openhab_item is None:
            raise ValueError('openhabItem must not be None')

        self.item = openhab_item
        self.battery_powered = battery_powered
        self.battery_percentage_item = battery_percentage_item
        self.wifi = wifi
        self.auto_report = auto_report
        self.last_activated_timestamp = None
        self.zone_manager = None
        self.channel = None
        self._additional_items = [i for i in additional_items if i is not None]

        if battery_percentage_item is not None and battery_percentage_item not in self._additional_items:
            self._additional_items.append(battery_percentage_item)

    def contains_item(self, item):
        """
        Returns true if this device contains the specified item.
        """
        their_name = pe.get_item_name(item)
        for item in self.get_all_items():
            if pe.get_item_name(item) == their_name:
                return True

        return False

    def get_item(self):
        """
        Returns the backed OpenHab item.

        :rtype: Item
        """
        return self.item

    def get_item_name(self):
        """
        Returns the backed OpenHab item name.

        :rtype: str
        """
        return pe.get_item_name(self.item)

    def get_friendly_item_name(self, zone: 'Zone'):
        """ Returns the friend item name that excludes the zone name (if contained). Also replace hyphen with space. """
        name = self.get_item_name()
        index = name.find(zone.get_name())
        if index != -1:
            name = name[index + len(zone.get_name()) + 1:]

        name = name.replace("_", " ")

        return name

    def get_all_items(self):
        """ Return a list of all items in this device. """
        return [self.item] + self._additional_items

    def set_channel(self, channel: str):
        """
        Set the OpenHab channel string (configured in the item metadata).

        :return: A NEW object with the additional newly set channel.
        """
        new_obj = copy(self)
        new_obj.channel = channel

        return new_obj

    def get_channel(self) -> str:
        """
        Returns the OpenHab channel string linked with the item.

        :rtype: str the channel string or None if the item is not linked to a channel
        """
        return self.channel

    def set_battery_powered(self, bool_value):
        """
        :return: A NEW object with the batteryPowered attribute set to the
                specified value
        """
        new_obj = copy(self)
        new_obj.battery_powered = bool_value

        return new_obj

    def is_battery_powered(self):
        """
        Returns True if the device is powered by a batter; False otherwise.

        :rtype: Boolean
        """

        return self.battery_powered

    def get_battery_percentage(self) -> Union[float, None]:
        """ Returns the remaining battery percentage, or None if the device is not powered by battery. """
        if self.battery_percentage_item is None:
            return None
        else:
            # noinspection PyTypeChecker
            return pe.get_number_value(self.battery_percentage_item)

    def set_use_wifi(self, bool_value):
        """
        :return: A NEW object with the wifi attribute set to the specified value
        """
        new_obj = copy(self)
        new_obj.wifi = bool_value

        return new_obj

    def use_wifi(self):
        """
        Returns True if the device communicates using WiFi.

        :rtype: Boolean
        """
        return self.wifi

    def set_auto_report(self, bool_value):
        """
        :return: A NEW object with the autoReport attribute set to the specified value.
        """
        new_obj = copy(self)
        new_obj.auto_report = bool_value

        return new_obj

    def is_auto_report(self):
        """
        Returns True if the device periodically sends its value.

        :rtype: Boolean
        """
        return self.auto_report

    def set_zone_manager(self, zone_manager):
        """
        :return: A NEW object with the zoneManager attribute set to the
            specified value.
        """
        new_obj = copy(self)
        new_obj.zone_manager = zone_manager

        return new_obj

    def get_zone_manager(self):
        """
        Returns the zone the device belong to or None if the device does not
        belong to any zone.

        :rtype: Zone
        """
        return self.zone_manager

    def is_occupied(self, seconds_from_last_event=5 * 60):
        """
        Returns boolean indicating if the present state of the device might
        indicate that the zone is occupied.

        :rtype: bool
        """
        return False

    def get_last_activated_timestamp(self):
        """
        Returns the timestamp in epoch seconds of the last event generated by
        the device.

        :rtype: int the last activated epoch second or None if not no event has
            been generated.
        """
        return self.last_activated_timestamp

    def reset_value_states(self):
        """
        Reset the underlying OpenHab item state.

        This method can be used when the physical device mal-functions and
        no longer sends the value update. A watch dog process can determine
        that the device is offline and invoke this method to reset the states.

        Devices that have more than one underlying OpenHab values must override
        this method.
        """
        pass

    def was_recently_activated(self, seconds) -> bool:
        """
        :param int seconds: the past duration (from the current time) to
            determine if the device was activated.
        :rtype: bool True if the device was activated during the specified
            seconds; False otherwise.
        """
        prev_timestamp = self.get_last_activated_timestamp()
        if prev_timestamp is None:
            return False
        else:
            return (time.time() - prev_timestamp) <= seconds

    def update_last_activated_timestamp(self):
        """ Set the lastActivatedTimestamp field to the current epoch second. """
        self.last_activated_timestamp = time.time()

    def __str__(self):
        value = u"{}: {}".format(self.__class__.__name__, self.get_item_name())

        if len(self._additional_items) > 0:
            value += " ({} additional items)".format(len(self._additional_items))

        if self.is_battery_powered():
            value += ", battery powered"
            if self.get_battery_percentage() is not None:
                value += u" ({}%)".format(self.get_battery_percentage())

        if self.use_wifi():
            value += ", wifi"

        if self.is_auto_report():
            value += ", auto report"

        if self.last_activated_timestamp is not None:
            diff_in_seconds = time.time() - self.last_activated_timestamp
            value += ", last activated: {} ({})".format(self.last_activated_timestamp,
                                                        str(datetime.timedelta(seconds=diff_in_seconds)))

        return value
