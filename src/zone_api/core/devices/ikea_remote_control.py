from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device


class IkeaRemoteControl(Device):
    """
    Represents an IKEA E1524/E1810 remote control.
    https://www.zigbee2mqtt.io/devices/E1524_E1810.html
    """

    def __init__(self, power_item, brightness_up_click_item, brightness_up_hold_item, brightness_down_click_item,
                 brightness_down_hold_item, left_click_item, left_hold_item, right_click_item, right_hold_item,
                 battery_percentage_item):
        additional_devices = [brightness_up_click_item, brightness_up_hold_item, brightness_down_click_item,
                              brightness_down_hold_item, left_click_item, left_hold_item, right_click_item,
                              right_hold_item, battery_percentage_item]
        super().__init__(openhab_item=power_item, additional_items=additional_devices,
                         battery_powered=True, battery_percentage_item=battery_percentage_item)

    def reset_value_states(self):
        """ Override to set all switch states to false. """
        for item in self.get_all_items():
            if pe.is_in_on_state(item):
                pe.set_switch_state(item, False)
