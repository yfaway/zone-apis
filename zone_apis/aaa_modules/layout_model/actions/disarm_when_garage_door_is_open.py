from threading import Timer

from aaa_modules import security_manager as sm
from aaa_modules.layout_model.devices.contact import GarageDoor
from aaa_modules.layout_model.devices.network_presence import NetworkPresence
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.action import action


@action(events=[ZoneEvent.CONTACT_OPEN], devices=[GarageDoor], external=True)
class DisarmWhenGarageDoorIsOpen:
    """
    Automatically disarm after the garage door is open and a network device is connected to WiFi.
    (indicates that a owner has just got home).
    """

    def __init__(self, interval_in_seconds=10, max_interval_count=9):
        self.interval_in_seconds = interval_in_seconds
        self.max_interval_count = max_interval_count

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info):
        events = event_info.get_event_dispatcher()
        zone_manager = event_info.get_zone_manager()

        if not sm.has_security_system(zone_manager):
            return False

        if sm.is_unarmed(zone_manager):
            return False

        network_devices = zone_manager.get_devices_by_type(NetworkPresence)
        if len(network_devices) == 0:
            return False

        timer_count = 0

        def timer_handler():
            nonlocal timer_count

            owner_detected = False
            for n in network_devices:
                if n.is_occupied(3 * 60):
                    owner_detected = True
                    break

            if owner_detected:
                sm.disarm(zone_manager, events)
                self.log_info("Owner arrives home; disarmed.")
            elif timer_count < self.max_interval_count:
                timer_count += 1

                self.timer = Timer(self.interval_in_seconds, timer_handler)
                self.timer.start()
            else:
                self.log_info("No owner detected; won't disarm.")

        timer_handler()

        return True
