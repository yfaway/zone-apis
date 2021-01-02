from typing import Type

from aaa_modules.alert_manager import AlertManager
from aaa_modules.layout_model.zone import Zone, ZoneEvent
from aaa_modules.layout_model.device import Device


class ImmutableZoneManager:
    """
    Similar to ZoneManager, but this class contains read-only methods. 
    Instances of this class is passed to the method Action#onAction.
    """

    def __init__(self, get_zones_fcn, get_zone_by_id_fcn, get_devices_by_type_fcn, alert_manager: AlertManager = None):
        self.get_zones_fcn = get_zones_fcn
        self.get_zone_by_id_fcn = get_zone_by_id_fcn
        self.get_devices_by_type_fcn = get_devices_by_type_fcn
        self.alert_manager = alert_manager

    def set_alert_manager(self, alert_manager: AlertManager):
        """ Sets the alert manager and returns a new instance of this class. """

        params = {'get_zones_fcn': self.get_zones_fcn,
                  'get_zone_by_id_fcn': self.get_zone_by_id_fcn,
                  'get_devices_by_type_fcn': self.get_devices_by_type_fcn,
                  'alert_manager': alert_manager}
        return ImmutableZoneManager(**params)

    def get_alert_manager(self) -> AlertManager:
        return self.alert_manager

    def get_containing_zone(self, device):
        """
        Returns the first zone containing the device or None if the device
        does not belong to a zone.

        :param Device device: the device
        :rtype: Zone or None
        """
        if device is None:
            raise ValueError('device must not be None')

        for zone in self.get_zones():
            if zone.hasDevice(device):
                return zone

        return None

    def get_zones(self):
        """
        Returns a new list contains all zone.

        :rtype: list(Zone)
        """
        return self.get_zones_fcn()

    def get_zone_by_id(self, zone_id):
        """
        Returns the zone associated with the given zoneId.

        :param string zone_id: the value returned by Zone::getId()
        :return: the associated zone or None if the zoneId is not found
        :rtype: Zone
        """
        return self.get_zone_by_id_fcn(zone_id)

    def get_devices_by_type(self, cls: Type):
        """
        Returns a list of devices in all zones matching the given type.

        :param Device cls: the device type
        :rtype: list(Device)
        """
        return self.get_devices_by_type_fcn(cls)

    def dispatch_event(self, zone_event: ZoneEvent, open_hab_events, item, enforce_item_in_zone=True):
        """
        Dispatches the event to the zones.

        :param item:
        :param ZoneEvent zone_event:
        :param events open_hab_events:
        :param bool enforce_item_in_zone: if set to true, the actions won't be
            triggered if the zone doesn't contain the item.
        """
        self.update_device_last_activated_time(item)

        return_values = [
            z.dispatch_event(zone_event, open_hab_events, item, self, enforce_item_in_zone)
            for z in self.get_zones()]
        return any(return_values)

    # noinspection PyUnusedLocal
    def on_network_device_connected(self, events, item):
        """
        Dispatches the network device connected (to local network) to each zone.

        :return: True if at least one zone processed the event; False otherwise
        :rtype: bool
        """
        self.update_device_last_activated_time(item)

        return True

    def on_switch_turned_on(self, events, item):
        """
        Dispatches the switch turned on event to each zone.

        :return: True if at least one zone processed the event; False otherwise
        :rtype: bool
        """
        self.update_device_last_activated_time(item)

        return_values = [z.on_switch_turned_on(events, item, self) for z in self.get_zones()]
        return any(return_values)

    def on_switch_turned_off(self, events, item):
        """
        Dispatches the switch turned off event to each zone.

        :return: True if at least one zone processed the event; False otherwise
        :rtype: bool
        """
        return_values = []
        for z in self.get_zones():
            return_values.append(z.on_switch_turned_off(events, item, self))
        return any(return_values)

    def on_timer_expired(self, events, item):
        """
        Dispatches the timer expiry event to each zone.

        :param scope.events events: the global events object
        :param Item item:
        :return: True if at least one zone processed the event; False otherwise
        :rtype: bool
        """
        return_values = [z.onTimerExpired(events, item) for z in self.get_zones()]
        return any(return_values)

    def update_device_last_activated_time(self, item):
        """
        Determine if the item is associated with a managed device. If yes,
        update it last activated time to the current epoch second.
        """
        for zone in self.get_zones():
            devices = [d for d in zone.getDevices() if d.containsItem(item)]
            for d in devices:
                # noinspection PyProtectedMember
                d._update_last_activated_timestamp()

    def __str__(self):
        value = u""
        for z in self.get_zones():
            value = f"{value}\n{str(z)}"

        return value
