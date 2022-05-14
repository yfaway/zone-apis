import HABApp
import os
import yaml
# from importlib import reload
# from zone_api import zone_parser
# reload(zone_parser)

from zone_api import zone_parser as zp
from zone_api import platform_encapsulator as pe


class ConfigureZoneManagerRule(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.run.soon(self.configure_zone_manager)

    # noinspection PyMethodMayBeStatic
    def configure_zone_manager(self):
        # When running on the PI
        config_file = '/home/pi/git/zone-apis/habapp/zone-api-config.yml'
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


ConfigureZoneManagerRule()
