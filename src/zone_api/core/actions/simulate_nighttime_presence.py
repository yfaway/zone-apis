import random
from threading import Timer

from zone_api import platform_encapsulator as pe
from zone_api.core.action import action
from zone_api.core.devices.astro_sensor import AstroSensor
from zone_api.core.devices.switch import Light
from zone_api.core.event_info import EventInfo
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.zone_event import ZoneEvent

ON_EVENTS = [ZoneEvent.VACATION_MODE_ON, ZoneEvent.ASTRO_LIGHT_ON]
OFF_EVENTS = [ZoneEvent.ASTRO_LIGHT_OFF, ZoneEvent.ASTRO_BED_TIME, ZoneEvent.VACATION_MODE_OFF]

DISPLAY_ITEM_NAME = 'Out_Light_Simulation'


@action(events=ON_EVENTS + OFF_EVENTS, external_events=ON_EVENTS + OFF_EVENTS, devices=[AstroSensor])
class SimulateNighttimePresence:
    """
    When on vacation mode, after the sunset and before bed time, randomly turn on a managed light for a random period.
    After the period expires, randomly select another light (could be the same one again) and turn it on. Repeat this
    process until the vacation mode ends or until bed time.
    If the OH switch item DISPLAY_ITEM_NAME is present, set its value to True if light simulation is running.
    """

    def __init__(self, min_light_on_duration_in_minutes=3, max_light_on_duration_in_minutes=8):
        """ Ctor """
        self.min_light_on_duration_in_minutes = min_light_on_duration_in_minutes
        self.max_light_on_duration_in_minutes = max_light_on_duration_in_minutes

        # noinspection PyTypeChecker
        self.timer: Timer = None

        # noinspection PyTypeChecker
        self.light: Light = None

        self.iteration_count = 0  # for unit testing; how many times we have looped.

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info: EventInfo):
        zm: ImmutableZoneManager = event_info.get_zone_manager()

        if event_info.get_event_type() in ON_EVENTS:
            if not zm.is_light_on_time() or not zm.is_in_vacation():
                return False

            def turn_on_random_light():
                self.iteration_count += 1

                if self.light is not None:  # turn off the previous light.
                    self.light.turn_off(event_info.get_event_dispatcher())

                self.light = random.choice(zm.get_devices_by_type(Light))
                self.light.turn_on(event_info.get_event_dispatcher())

                duration_in_seconds = random.randint(self.min_light_on_duration_in_minutes * 60,
                                                     self.max_light_on_duration_in_minutes * 60)
                self.log_info(f"turning on {self.light.get_item_name()} for "
                              f"{int(duration_in_seconds / 60)} minutes")

                if not zm.is_light_on_time() or not zm.is_in_vacation():
                    return

                self.timer = Timer(duration_in_seconds, turn_on_random_light)
                self.timer.start()

            if self.timer is None:  # is simulation is already running
                self.log_info("Starting light simulation.")

                turn_on_random_light()

                if pe.has_item(DISPLAY_ITEM_NAME):
                    pe.set_switch_state(DISPLAY_ITEM_NAME, True)

        else:  # events to turn off simulation mode
            self.cancel_timer()

            if self.light is not None:
                self.light.turn_off(event_info.get_event_dispatcher())
                self.light = None

        return True

    def cancel_timer(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

            self.iteration_count = 0

            self.log_info("Canceled light simulation mode.")

        if pe.has_item(DISPLAY_ITEM_NAME):
            pe.set_switch_state(DISPLAY_ITEM_NAME, False)
