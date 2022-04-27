import HABApp
import os
import yaml
# from importlib import reload
# from zone_api import zone_parser
# reload(zone_parser)

from zone_api import zone_parser as zp
from zone_api import platform_encapsulator as pe
from zone_api.core.devices.activity_times import ActivityType, ActivityTimes
from zone_api.core.map_parameters import MapParameters


class ConfigureZoneManagerRule(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.run.soon(self.configure_zone_manager)

    # noinspection PyMethodMayBeStatic
    def configure_zone_manager(self):
        time_map = {
            ActivityType.WAKE_UP: '6:35 - 9',
            ActivityType.LUNCH: '12:00 - 13:30',
            ActivityType.QUIET: '14:00 - 16:00, 20:00 - 22:59',
            ActivityType.DINNER: '17:50 - 20:00',
            ActivityType.SLEEP: '23:00 - 7:00',
            ActivityType.AUTO_ARM_STAY: '20:00 - 2:00',
            ActivityType.TURN_OFF_PLUGS: '23:00 - 2:00',
        }

        # When running on the PI
        config_file = '/home/pi/git/zone-apis/habapp/zone-api-config.yml'
        if not os.path.exists(config_file):  # In development machine
            config_file = './habapp/zone-api-config.yml'
            if not os.path.exists(config_file):
                raise ValueError("Missing zone-api-config.yml file.")

        pe.log_info(f"Reading zone-api configuration from '{config_file}'")

        zm = zp.parse(ActivityTimes(time_map), self._read_zone_api_configurations(config_file))
        pe.add_zone_manager_to_context(zm)

        pe.log_info(str(pe.get_zone_manager_from_context()))

    @staticmethod
    def _read_zone_api_configurations(config_file: str) -> MapParameters:
        flat_map = {}
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

            all_action_params = config['action-parameters']
            for action_name in all_action_params.keys():
                action_params = all_action_params[action_name]
                for key in action_params.keys():
                    flat_key = f"{action_name}.{key}"
                    flat_map[flat_key] = action_params[key]

        return MapParameters(flat_map)


ConfigureZoneManagerRule()
