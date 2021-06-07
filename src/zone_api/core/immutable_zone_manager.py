import threading
import time
from typing import Type, List

from schedule import Scheduler

from zone_api import platform_encapsulator as pe
from zone_api.alert_manager import AlertManager
from zone_api.core.devices.astro_sensor import AstroSensor
from zone_api.core.devices.vacation import Vacation
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.device import Device


class ImmutableZoneManager:
    """
    Similar to ZoneManager, but this class contains read-only methods. Instances of this class is
    passed to the method Action#on_action.

    Provide the follow common services:
      - Alert processing.
      - Scheduler.

    Instance of this class has life cycle:
      - start() should be called first to indicate that the zones have been fully populated (outside
        the scope of the class).
      - stop() should be called when the object is no longer used.
    """

    def __init__(self, get_zones_fcn, get_zone_by_id_fcn, get_devices_by_type_fcn,
                 alert_manager: AlertManager = None):
        self.get_zones_fcn = get_zones_fcn
        self.get_zone_by_id_fcn = get_zone_by_id_fcn
        self.get_devices_by_type_fcn = get_devices_by_type_fcn
        self.alert_manager = alert_manager
        self.scheduler = Scheduler()

        # noinspection PyTypeChecker
        self.cease_continuous_run: threading.Event = None

        # map from primary item name to zone for quick look-up.
        self.item_name_to_zone = {}
        self.fully_initialized = False

    def start(self):
        """
        Indicates that the zones are fully populated. The following actions will take place:
          1. Map device item name to zone.
          2. Start scheduler (if not in a unit test).
          3. Send event ZoneEvent.STARTUP to each action.
        """
        for z in self.get_zones():
            for d in z.get_devices():
                self.item_name_to_zone[d.get_item_name()] = z

        if not pe.is_in_unit_tests():
            self._start_scheduler()

        self.fully_initialized = True

        for z in self.get_zones():
            z.dispatch_event(ZoneEvent.STARTUP, pe.get_event_dispatcher(), None, None, self)

    def stop(self):
        """
        Indicates that this object is no longer being used.
        """
        self._cancel_scheduler()
        self.fully_initialized = False

    def set_alert_manager(self, alert_manager: AlertManager):
        """ Sets the alert manager and returns a new instance of this class. """

        params = {'get_zones_fcn': self.get_zones_fcn,
                  'get_zone_by_id_fcn': self.get_zone_by_id_fcn,
                  'get_devices_by_type_fcn': self.get_devices_by_type_fcn,
                  'alert_manager': alert_manager}
        return ImmutableZoneManager(**params)

    def get_alert_manager(self) -> AlertManager:
        return self.alert_manager

    def get_scheduler(self) -> Scheduler:
        """ Returns the Scheduler instance """
        return self.scheduler

    def _start_scheduler(self, interval_in_seconds=1) -> threading.Event:
        """ Runs the scheduler in a separate thread. """

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not self.cease_continuous_run.is_set():
                    self.scheduler.run_pending()
                    time.sleep(interval_in_seconds)

                pe.log_info("Cancelled the scheduler service.")

        if self.cease_continuous_run is None:
            self.cease_continuous_run = threading.Event()
            continuous_thread = ScheduleThread()
            continuous_thread.start()

            pe.log_info("Started the scheduler service.")

        return self.cease_continuous_run

    def _cancel_scheduler(self):
        """ Cancel the scheduler thread if it was started. """
        if self.cease_continuous_run is not None:
            self.cease_continuous_run.set()

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
            if zone.has_device(device):
                return zone

        return None

    def get_zones(self) -> List[Zone]:
        """
        Returns a new list contains all zone.

        :rtype: list(Zone)
        """
        return self.get_zones_fcn()

    def get_zone_by_id(self, zone_id):
        """
        Returns the zone associated with the given zone_id.

        :param string zone_id: the value returned by Zone::get_id()
        :return: the associated zone or None if the zone_id is not found
        :rtype: Zone
        """
        return self.get_zone_by_id_fcn(zone_id)

    def get_zone_by_item_name(self, item_name):
        """
        Returns the zone associated with the given item_name.

        :param str item_name:
        :return: the associated zone or None if the item_name is not found
        :rtype: Zone
        """
        return self.item_name_to_zone[item_name] if item_name in self.item_name_to_zone.keys() else None

    def get_devices_by_type(self, cls: Type):
        """
        Returns a list of devices in all zones matching the given type.

        :param Device cls: the device type
        :rtype: list(Device)
        """
        return self.get_devices_by_type_fcn(cls)

    def is_in_vacation(self):
        """ Returns true if at least one device indicates that the house is in vacation mode, vie Vacation class. """
        for z in self.get_zones():
            for d in z.get_devices_by_type(Vacation):
                if d.is_in_vacation():
                    return True

        return False

    def is_light_on_time(self):
        """
        Returns True if it is light-on time; returns false if it is no. Returns None if there is no AstroSensor to
        determine the time.

        :rtype: bool or None
        """
        has_astro_sensors = False
        for z in self.get_zones():
            astro_sensors = z.get_devices_by_type(AstroSensor)
            if len(astro_sensors) > 0:
                has_astro_sensors = True
                value = any(s.is_light_on_time() for s in astro_sensors)
                if value:
                    return True

        if not has_astro_sensors:
            return None
        else:
            return False

    def get_first_device_by_type(self, cls: type):
        """
        Returns the first device matching the given type, or None if there is no device.

        :param type cls: the device type
        """
        devices = self.get_devices_by_type(cls)
        return devices[0] if len(devices) > 0 else None

    def dispatch_event(self, zone_event: ZoneEvent, open_hab_events, device: Device, item):
        """
        Dispatches the event to the zones.

        :param Device device: the device containing the triggered item; a device may contain multiple items.
        :param Any item: the triggered item.
        :param ZoneEvent zone_event:
        :param events open_hab_events:
        """
        # noinspection PyProtectedMember
        device.update_last_activated_timestamp()

        return_values = []

        # Small optimization: dispatch directly to the applicable zone first if we can determine
        # the zone id from the item name.
        owning_zone: Zone = self.get_zone_by_item_name(pe.get_item_name(item))
        if owning_zone is not None:
            value = owning_zone.dispatch_event(zone_event, open_hab_events, device, item, self, owning_zone)
            return_values.append(value)

        # Then continue to dispatch to other zones even if a priority zone has been dispatched to.
        # This allows action to process events from other zones.
        for z in self.get_zones():
            if z is not owning_zone:
                value = z.dispatch_event(zone_event, open_hab_events, device, item, self, owning_zone)
                return_values.append(value)

        return any(return_values)

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def on_network_device_connected(self, events, device, item):
        """
        Dispatches the network device connected (to local network) to each zone.

        :return: True if at least one zone processed the event; False otherwise
        :rtype: bool
        """
        # noinspection PyProtectedMember
        device.update_last_activated_timestamp()

        return True

    def on_switch_turned_on(self, events, device, item):
        """
        Dispatches the switch turned on event to each zone.

        :return: True if at least one zone processed the event; False otherwise
        :rtype: bool
        """
        # noinspection PyProtectedMember
        device.update_last_activated_timestamp()

        return_values = [z.on_switch_turned_on(events, item, self) for z in self.get_zones()]
        return any(return_values)

    # noinspection PyUnusedLocal
    def on_switch_turned_off(self, events, device, item):
        """
        Dispatches the switch turned off event to each zone.

        :return: True if at least one zone processed the event; False otherwise
        :rtype: bool
        """
        return_values = []
        for z in self.get_zones():
            return_values.append(z.on_switch_turned_off(events, item, self))
        return any(return_values)

    def __str__(self):
        value = u""
        for z in self.get_zones():
            value = f"{value}\n{str(z)}"

        return value
