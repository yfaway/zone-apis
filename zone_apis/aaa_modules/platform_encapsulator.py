try:
    import HABApp
except ImportError:
    from org.slf4j import Logger, LoggerFactory
    from org.eclipse.smarthome.core.types import UnDefType
    from org.eclipse.smarthome.core.library.types import DecimalType
    from org.eclipse.smarthome.core.library.items import StringItem
    from org.eclipse.smarthome.core.library.types import OnOffType
    from org.eclipse.smarthome.core.library.types import OpenClosedType

    from core.jsr223 import scope
    from core.testing import run_test

    logger = LoggerFactory.getLogger("org.eclipse.smarthome.model.script.Rules")
    inHabApp = False
else:
    import logging
    from HABApp.core.items import Item
    from HABApp.openhab.items import ContactItem, StringItem, SwitchItem
    from HABApp.openhab.definitions import OnOffValue
    from HABApp.core.events import ValueChangeEvent

    inHabApp = True
    logger = logging.getLogger('ZoneApis')


class PlatformEncapsulator:
    """
    Abstract away the OpenHab classes.
    """

    @staticmethod
    def isStateAvailable(state):
        """
        :return: True if the state is not of type UndefType.
        """

        return not isinstance(state, UnDefType)

    @staticmethod
    def isInStateOn(state):
        """
        :param State state:
        :return: True if the state is ON.
        """

        return OnOffType.ON == state

    @staticmethod
    def isInStateOff(state):
        """
        :param State state:
        :return: True if the state is OFF.
        """

        return OnOffType.OFF == state

    @staticmethod
    def isInStateOpen(state):
        """
        :param State state:
        :return: True if the state is OPEN.
        """

        return OpenClosedType.OPEN == state

    @staticmethod
    def isInStateClosed(state):
        """
        :param State state:
        :return: True if the state is CLOSED.
        """

        return OpenClosedType.CLOSED == state

    @staticmethod
    def getIntegerStateValue(item, defaultVal):
        """
        :param Item item:
        :param * defaultVal: the value to return if the state is not available
        :return: the integer state value or defaultVal is the state is not
            available.
        :rtype: int
        """

        if PlatformEncapsulator.isStateAvailable(item.getState()):
            return item.getState().intValue()
        else:
            return defaultVal

    @staticmethod
    def setDecimalState(item, decimalValue):
        """
        :param NumberItem item:
        :param int decimalValue:
        """
        item.setState(DecimalType(decimalValue))

    @staticmethod
    def setOnState(item):
        """
        :param SwitchItem item:
        """
        item.setState(OnOffType.ON)

    @staticmethod
    def setOffState(item):
        """
        :param SwitchItem item:
        """
        item.setState(OnOffType.OFF)

    @staticmethod
    def getLogger():
        """
        Returns the logger.

        :rtype: Logger
        """
        return logger

    @staticmethod
    def logDebug(message):
        """ Log a debug message. """

        logger.debug(message)

    @staticmethod
    def logInfo(message):
        """ Log an info message. """

        logger.info(message)

    @staticmethod
    def logWarning(message):
        """ Log an warning message. """

        logger.warn(message)

    @staticmethod
    def logError(message):
        """ Log an error message. """

        logger.error(message)

    @staticmethod
    def createStringItem(name):
        return StringItem(name)

    @staticmethod

    @staticmethod
    def runUnitTest(className):
        """ Run the unit test. """
        run_test(className, logger)


def is_in_habapp() -> bool:
    return inHabApp


def register_test_item(item: Item) -> None:
    """ Register the given item with the runtime. """
    if is_in_habapp():
        HABApp.core.items.Item.get_create_item(item.name, item.get_value())
    else:
        scope.itemRegistry.remove(item.getName())
        scope.itemRegistry.add(item)


def unregister_test_item(item) -> None:
    """ Unregister the given item with the runtime. """
    HABApp.core.Items.pop_item(item.name)


def is_in_on_state(item: SwitchItem):
    """
    :param SwitchItem item:
    :return: True if the state is ON.
    """
    return item.is_on()


def create_switch_item(name: str, on=False) -> SwitchItem:
    """
    :param name: the item name
    :param on: if True, the state is ON, else the state is OFF
    :return: SwitchItem
    """
    return SwitchItem(name, OnOffValue.ON if on else OnOffValue.OFF)


def change_switch_state(item: SwitchItem, on: bool):
    item.set_value(OnOffValue.ON if on else OnOffValue.OFF)


def register_value_change_event(item: Item, handler):
    item.listen_event(handler, ValueChangeEvent)

def log_error(message):
    """ Log an error message. """

    logger.error(message)

def get_channel(item) -> str:
    """
    Returns the OpenHab channel string linked with the item.

    :rtype: str the channel string or None if the item is not linked to
    a channel
    """
    if (inHabApp):
        return None
    else:
        from core import osgi
        from org.eclipse.smarthome.core.items import MetadataKey
        meta_registry = osgi.get_service("org.eclipse.smarthome.core.items.MetadataRegistry")

        channel_meta = meta_registry.get(
            MetadataKey('channel', item.getName()))
        if None != channel_meta:
            return channel_meta.value
        else:
            return None
