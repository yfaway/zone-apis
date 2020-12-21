import HABApp
#from importlib import reload
#from aaa_modules import zone_parser
#reload(zone_parser)

from aaa_modules import zone_parser as zp
from aaa_modules import platform_encapsulator as pe


# Rules are classes that inherit from HABApp.Rule
class ConfigureZoneManagerRule(HABApp.Rule):
    def __init__(self):
        super().__init__()

        # Use run_soon to schedule things directly after instantiation,
        # don't do blocking things in __init__
        self.run_soon(self.configure_zone_manager)

    def configure_zone_manager(self):
        zm = zp.parse()
        pe.log_error(str(zm))


# Rules
ConfigureZoneManagerRule()
