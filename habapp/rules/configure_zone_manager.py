import HABApp
# from importlib import reload
# from aaa_modules import zone_parser
# reload(zone_parser)

from aaa_modules import zone_parser as zp
from aaa_modules import platform_encapsulator as pe


class ConfigureZoneManagerRule(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.run_soon(self.configure_zone_manager)

    # noinspection PyMethodMayBeStatic
    def configure_zone_manager(self):
        zm = zp.parse()
        pe.add_zone_manager_to_context(zm)

        pe.log_info(str(pe.get_zone_manager_from_context()))


ConfigureZoneManagerRule()
