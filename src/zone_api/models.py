from __future__ import annotations

from datetime import datetime
from typing import Any, cast

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


class DimmerItem(NumberItem):
    def percentage(self) -> float:
        return cast(int, self.state)

    def set_percentage(self, value: int) -> None:
        self.state = value


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
