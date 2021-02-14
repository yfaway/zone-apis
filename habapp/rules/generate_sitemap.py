from collections import OrderedDict

import HABApp

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.devices.contact import Door
from aaa_modules.layout_model.devices.gas_sensor import Co2GasSensor, NaturalGasSensor, SmokeSensor
from aaa_modules.layout_model.devices.humidity_sensor import HumiditySensor
from aaa_modules.layout_model.devices.illuminance_sensor import IlluminanceSensor
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor
from aaa_modules.layout_model.devices.plug import Plug
from aaa_modules.layout_model.devices.switch import Light, Fan
from aaa_modules.layout_model.devices.temperature_sensor import TemperatureSensor
from aaa_modules.layout_model.devices.tv import Tv
from aaa_modules.layout_model.devices.wled import Wled


class GenerateSitemap(HABApp.Rule):
    """ Returns a string containing the sitemap frames for all the zones. """

    def __init__(self):
        super().__init__()

        # self.run_in(15, self.generate)

    # noinspection PyMethodMayBeStatic
    def generate(self):
        zm = pe.get_zone_manager_from_context()

        global_str = ''
        for z in zm.get_zones():
            item_count = 0

            if z.get_display_icon() is None:
                zone_icon = ''
            else:
                zone_icon = z.get_display_icon()

            inner_str = 'Text label="{}" icon="{}" {{\n'.format(z.get_name(), zone_icon)
            inner_str += '  Frame label="{}" {{\n'.format(z.get_name())

            # retain key order
            mappings = OrderedDict([
                (TemperatureSensor, 'Text item={} icon="temperature"'),
                (HumiditySensor, 'Text item={} icon="humidity"'),
                (Door, 'Text item={} icon="door"'),
                (Light, 'Switch item={} icon="light"'),
                (Wled, 'Switch item={} icon="rgb"'),
                (Fan, 'Switch item={} icon="fan"'),
                (Plug, 'Switch item={} icon="poweroutlet"'),
                (IlluminanceSensor, 'Text item={}'),
                (MotionSensor, 'Switch item={}'),
                (Co2GasSensor, 'Text item={} icon="carbondioxide"'),
                (NaturalGasSensor, 'Text item={} icon="gas"'),
                (SmokeSensor, 'Text item={} icon="fire"'),
                (Tv, 'Switch item={} icon="screen"'),
            ])

            for cls in mappings.keys():
                item_string = '    {}\n'.format(mappings[cls])

                for d in z.get_devices_by_type(cls):
                    inner_str += item_string.format(d.get_item_name())
                    item_count += 1

            inner_str += '  }\n'
            inner_str += '}\n'

            if item_count > 0:
                global_str += inner_str

        pe.log_info(global_str)


GenerateSitemap()
