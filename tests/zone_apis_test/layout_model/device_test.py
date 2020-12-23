import unittest
from typing import List

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.zone import Zone
from aaa_modules.layout_model.zone_manager import ZoneManager


def create_zone_manager(zones: List[Zone]) -> ZoneManager:
    zm = ZoneManager()
    for zone in zones:
        zm.add_zone(zone)

    return zm


class DeviceTest(unittest.TestCase):
    """
    Base test class for Device derived sensors.
    """

    def setUp(self):
        """ Adds the items to the registry. """

        pe.set_in_unit_tests(True)

        for item in self.items:
            pe.register_test_item(item)

    def tearDown(self):
        """ Removes the items from the registry. """
        for item in self.items:
            pe.unregister_test_item(item)

        pe.set_in_unit_tests(False)

    def set_items(self, items: list) -> None:
        """
        Configures the test items to register / unregister before and after each test.
        :param items: list of items
        """
        self.items = items

    def get_items(self) -> list:
        return self.items

    def getMockedEventDispatcher(self):
        return MockedEventDispatcher(scope.itemRegistry)


class MockedEventDispatcher:
    """
    Mocked the scope.events object to directly change the state of the item
    instead of going through the event bus. This reduces the wait time, and 
    more importantly, makes sendCommand synchronous (no need to inject
    time.sleep() to wait for the command to finish).

    The itemRegistry needs to be passed in, as it is not retrievable from
    'scope' if the current thread is not the main thread.
    """

    def __init__(self, itemRegistry):
        self.itemRegistry = itemRegistry

        from core.jsr223 import scope
        from org.eclipse.smarthome.core.library.items import DimmerItem
        from org.eclipse.smarthome.core.library.items import NumberItem
        from org.eclipse.smarthome.core.library.types import DecimalType
        from org.eclipse.smarthome.core.library.types import OnOffType
        from org.eclipse.smarthome.core.library.types import PercentType

    def sendCommand(self, itemName, command):
        item = self.itemRegistry.getItem(itemName)

        if command == "ON":
            item.setState(OnOffType.ON)
        elif command == "OFF":
            item.setState(OnOffType.OFF)
        elif isinstance(item, DimmerItem):
            item.setState(PercentType(command))
        elif isinstance(item, NumberItem):
            item.setState(DecimalType(command))
        else:
            raise ValueError("Unsupported command value '{}'".format(command))
