from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Final, Union, cast

"""
A set of classes that represent different types of items in the OpenHAB system. These classes however are not bound to
OpenHAB and can be used in other contexts such as unit testing. There is a anoter set of classes in
zone_api.openhab.oh_models that are bound to OpenHAB and should be used when interacting with it. Those classes
are subclasses of the classes in this file and add OpenHAB specific functionality.
"""

class BaseItem:
    def __init__(self, name: str, state: Any = None):
        self.name = name
        self.state = state
        self._event_handlers: Dict[OpenHabEvent, Callable[[Any], Any]] = {}

    def listen_event(self, callback: Callable[[Any], Any],
                     event_type: OpenHabEvent) -> None:
        self._event_handlers[event_type] = callback

    def get_name(self):
        return self.name

    def get_value(self):
        return self.state

    def get_state(self):
        return self.state

    def get_event_handler(self, event_type) -> Union[Callable[[Any], Any], None]:
        return self._event_handlers.get(event_type) or None


class SwitchItem(BaseItem):
    def on(self) -> None:
        self.state = 'ON'

    def off(self) -> None:
        self.state = 'OFF'

    def is_on(self) -> bool:
        return self.state == 'ON'

    def is_off(self) -> bool:
        return self.state == 'OFF'


class NumberItem(BaseItem):
    def get_value(self) -> float:
        return cast(float, self.state)

    def set_value(self, value: float) -> None:
        self.state = value


class StringItem(BaseItem):
    def get_value(self) -> str:
        return cast(str, self.state)

    def set_value(self, value: str) -> None:
        self.state = value


class ContactItem(BaseItem):
    def is_open(self) -> bool:
        return self.state == 'OPEN'

    def is_closed(self) -> bool:
        return self.state == 'CLOSED'

    def set_open(self) -> None:
        self.state = 'OPEN'

    def set_closed(self) -> None:
        self.state = 'CLOSED'


class DimmerItem(SwitchItem):
    def is_on(self) -> bool:
        if self.state == 'ON':
            return True
        else:
            return self.percentage() > 0

    def is_off(self) -> bool:
        return self.state == 'OFF' or self.percentage() == 0

    def percentage(self) -> float:
        if self.state == 'ON':
            return 100
        elif self.state == 'OFF':
            return 0
        else:
            return int(self.state)

    def set_percentage(self, value: int) -> None:
        self.state = str(value)


class DateTimeItem(BaseItem):
    def get_value(self) -> datetime:
        return datetime.strptime(self.state, "%Y-%m-%dT%H:%M:%S.%f%z")

    def set_value(self, value: datetime) -> None:
        formatted_date = value.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + value.strftime("%z")
        self.state = formatted_date


class ColorItem(BaseItem):
    def set_value(self, value: Any) -> None:
        self.state = value


class PlayerItem(BaseItem):
    def pause(self) -> None:
        self.state = 'PAUSE'

    def play(self) -> None:
        self.state = 'PLAY'

    def is_playing(self) -> bool:
        return self.state == "PLAY"

class OpenHabEvent(Enum):
    ItemStateChanged = 'ItemStateChangedEvent' # the item state changed; i.e. new value differs from the old one.
    ItemStateUpdated = 'ItemStateUpdatedEvent' # the item state is updated, even if the value didn't change
    ItemCommandReceived = 'ItemCommandEvent' # a command is sent to the item


class ValueChangeEvent:
    def __init__(self, name: str, new_value: Any, old_value: Any) -> None:
        self.name: Final = name
        self.value: Final = new_value
        self.old_value: Final = old_value

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name: {self.name:s}, value: {self.value}, old_value: {self.old_value}>'

class ValueUpdateEvent:
    def __init__(self, name: str, value: Any) -> None:
        self.name: Final = name
        self.value: Final = value

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name: {self.name:s}, value: {self.value}>'

class ItemCommandEvent(ValueUpdateEvent):
    pass