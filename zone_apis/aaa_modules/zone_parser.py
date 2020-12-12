import re

import HABApp
from HABApp.core import Items
from HABApp.core.events import ValueChangeEvent
from HABApp.openhab.items import ContactItem, StringItem, SwitchItem

from aaa_modules import platform_encapsulator as PE
from aaa_modules.layout_model.devices.motion_sensor import MotionSensor


def create_motion_sensor(item) -> MotionSensor:
    """
    Creates a MotionSensor and register for change event.
    :param item: SwitchItem
    :return: MotionSensor
    """
    sensor = MotionSensor(item)

    def handler(event: ValueChangeEvent):
        if PE.is_in_on_state(item):
            sensor.on_triggered(event)

    item.listen_event(handler, ValueChangeEvent)

    PE.log_error(sensor.__unicode__())

    return sensor


def parse() -> list:
    mappings = {
        '.*MotionSensor$': create_motion_sensor
    }

    items = Items.get_all_items()
    for item in items:
        # PE.log_error("** i: {}".format(item))
        for pattern in mappings.keys():
            if re.match(pattern, item.name) is not None:
                sensor_item = mappings[pattern](item)
                PE.log_error(sensor_item.getItemName())

    # items = HABApp.core.Items.get_all_items()
    PE.log_error("count: {}".format(len(items)))

    return items
