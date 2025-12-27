import HABApp
import os
import yaml
# from importlib import reload
# from zone_api import zone_parser
# reload(zone_parser)

from zone_api import zone_parser as zp
from zone_api import platform_encapsulator as pe
from zone_api.core.immutable_zone_manager import ImmutableZoneManager


class ConfigureZoneManagerRule(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.run.soon(self.configure_zone_manager)

    # noinspection PyMethodMayBeStatic
    def configure_zone_manager(self):
        # When running on the PI
        config_file = '/home/yf/git/zone-apis/habapp/zone-api-config.yml'
        if not os.path.exists(config_file):  # In development machine
            config_file = './habapp/zone-api-config.yml'
            if not os.path.exists(config_file):
                raise ValueError("Missing zone-api-config.yml file.")

        pe.log_info(f"Reading zone-api configuration from '{config_file}'")

        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

        zm = zp.parse(config)
        pe.add_zone_manager_to_context(zm)

        pe.log_info(str(pe.get_zone_manager_from_context()))

    @staticmethod
    def _test_text_to_speech(msg: str):
        pe.play_text_to_speech_message('chromecast:audio:greatRoom', msg)

    @staticmethod
    def _test_invoking_action(zm: ImmutableZoneManager):
        from zone_api.core.event_info import EventInfo
        from zone_api.core.zone_event import ZoneEvent
        from zone_api.core.zone import Zone
        from zone_api.core.devices.motion_sensor import MotionSensor
        from zone_api.core.actions.announce_morning_weather_and_play_music import AnnounceMorningWeatherAndPlayMusic
        from zone_api.core.map_parameters import MapParameters

        kitchen: Zone = next((x for x in zm.get_internal_zones() if x.name == 'Kitchen'), None)
        event_info = EventInfo(ZoneEvent.MOTION, kitchen.get_first_device_by_type(MotionSensor).get_item(), kitchen,
                               pe.get_zone_manager_from_context(), pe.get_event_dispatcher())
        pe.log_info("Invoking action...")
        AnnounceMorningWeatherAndPlayMusic(MapParameters({})).on_action(event_info)

ConfigureZoneManagerRule()
