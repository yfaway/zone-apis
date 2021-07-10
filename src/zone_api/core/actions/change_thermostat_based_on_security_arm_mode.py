from typing import List

from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.thermostat import Thermostat
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action


@action(events=[ZoneEvent.PARTITION_ARMED_AWAY, ZoneEvent.PARTITION_DISARMED_FROM_AWAY],
        devices=[AlarmPartition])
class ChangeThermostatBasedOnSecurityArmMode:
    """
    Change the thermostat to AWAY mode if the house is armed-away.
    Resume the regular schedule if the house is disarmed (from away mode).
    """

    def on_action(self, event_info: EventInfo):
        zone_manager = event_info.get_zone_manager()

        thermostats: List[Thermostat] = zone_manager.get_devices_by_type(Thermostat)
        if len(thermostats) == 0:
            self.log_warning("Missing thermostat.")
            return False

        if not zone_manager.is_in_vacation():
            if event_info.get_event_type() == ZoneEvent.PARTITION_DISARMED_FROM_AWAY:
                thermostats[0].resume()
            else:
                thermostats[0].set_away_mode()
        else:
            self.log_info("In vacation mode -> not changing the thermostat state.")

        return True
