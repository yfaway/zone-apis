import HABApp

from zone_api import platform_encapsulator as pe
from zone_api.core.immutable_zone_manager import ImmutableZoneManager


class GenerateWifiItemMappings(HABApp.Rule):
    """ Returns a string containing the list of WiFi item names for a Selection in sitemap (OpenHab Basic UI). """

    def __init__(self):
        super().__init__()

        # self.run.at(10, self.generate)

    # noinspection PyMethodMayBeStatic
    def generate(self):
        zm: ImmutableZoneManager = pe.get_zone_manager_from_context()

        global_str = '""="None"'
        for z in zm.get_zones():
            for device in z.get_devices():
                if not device.is_auto_report():
                    continue

                key = device.get_item_name()
                value = f"{z.get_name()}: {device.get_friendly_item_name(z)}"

                global_str += f', "{key}"="{value}"'

        global_str = f"[{global_str}]"

        pe.log_info(global_str)


GenerateWifiItemMappings()
