from zone_api.core.devices.switch import Switch
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action


@action(events=[ZoneEvent.STARTUP], devices=[], zone_name_pattern='.*Virtual.*')
class SetSwitchTimerAfterStartup:
    """
    After the system starts up, if a switch was already on but having no active timer, that means it was turned on
    before the system. In that case, reset the timer so that the switch will turn off eventually.
    """

    # noinspection PyMethodMayBeStatic
    def on_startup(self, event_info: EventInfo):
        zm = event_info.get_zone_manager()
        for z in zm.get_zones():
            for d in z.get_devices_by_type(Switch):
                switch: Switch = d
                if switch.is_on():
                    self.log_info(f"Set timer for switch {switch.get_item_name()}.")
                    switch.turn_on(event_info.get_event_dispatcher())

    def on_action(self, event_info):
        # no-op as this action is only triggered st start-up.
        pass
