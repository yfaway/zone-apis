from typing import List

from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition
from aaa_modules.layout_model.devices.thermostat import Thermostat
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.action import action


@action(events=[ZoneEvent.PARTITION_ARMED_AWAY, ZoneEvent.PARTITION_DISARMED_FROM_AWAY],
        devices=[AlarmPartition])
class ChangeThermostatBasedOnSecurityArmMode:
    """
    Change the thermostat to AWAY mode if the house is armed-away.
    Resume the regular schedule if the house is disarmed (from away mode).
    """

    def on_action(self, event_info):
        zone_manager = event_info.get_zone_manager()

        thermostats: List[Thermostat] = zone_manager.get_devices_by_type(Thermostat)
        if len(thermostats) == 0:
            self.log_warning("Missing thermostat.")
            return False

        if event_info.get_event_type() == ZoneEvent.PARTITION_DISARMED_FROM_AWAY:
            thermostats[0].resume()
        else:
            thermostats[0].set_away_mode()

        return True
