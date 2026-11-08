from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from numbers import Number
from typing import Any, Dict, Final, List, Tuple, Type, Union
from collections.abc import Callable

from zone_api.openhab.websocket_client import OpenHabWebSocketClient
from zone_api.models import (
    BaseItem,
    ColorItem,
    ContactItem,
    DateTimeItem,
    DimmerItem,
    NumberItem,
    PlayerItem,
    StringItem,
    SwitchItem,
)


class OpenHabBaseItem(BaseItem):
    """Base model mirroring the OpenHAB REST item payload."""

    def __init__(self, payload: Dict[str, Any]):
        self._raw: Dict[str, Any] = payload or {}

        # Common fields from the OpenHAB REST API.
        name = self._raw.get('name') or ""
        self.type: str = self._raw.get('type') or ""
        state = self._raw.get('state')
        super().__init__(name=name, state=state)
        self.label: str | None = self._raw.get('label')
        self.category: str | None = self._raw.get('category')
        self.tags: List[str] = self._raw.get('tags') or []
        self.group_names: List[str] = self._raw.get('groupNames') or []
        self.link: str | None = self._raw.get('link')
        self.state_description: Dict[str, Any] | None = self._raw.get('stateDescription')
        self.metadata: Dict[str, Any] = self._raw.get('metadata') or {}
        self.editable: bool = bool(self._raw.get('editable'))
        self.command_description: Dict[str, Any] | None = self._raw.get('commandDescription')
        self.members: List[str] = self._raw.get('members') or []
        self.read_only: bool = bool(self._raw.get('readOnly'))
        self.unit: str | None = self._raw.get('unit')
        self.unit_symbol: str | None = self._raw.get('unitSymbol')
        self.min: Any = self._raw.get('min')
        self.max: Any = self._raw.get('max')
        self.step: Any = self._raw.get('step')
        self.pattern: str | None = self._raw.get('pattern')
        self.options: List[Dict[str, Any]] | None = self._raw.get('options')
        self.filters: List[Dict[str, Any]] | None = self._raw.get('filters')
        self.unit: Union[str, None]
        self._openhab_connection: OpenHabWebSocketClient

        # Import any unknown extra fields using snake_case naming.
        for key, value in self._raw.items():
            snake_key = self._to_snake_case(key)
            if not hasattr(self, snake_key):
                setattr(self, snake_key, value)

    def update_value_from_openhab(self, value: Any) -> None:
        self.state = value

    def _set_value(self, openhab_type: str, value: Any) -> None:
        self.state = value

        background_loop = asyncio.get_event_loop() 
        asyncio.run_coroutine_threadsafe(
            self._openhab_connection.send_command(self.name, openhab_type, value),
            background_loop)

    @staticmethod
    def _to_snake_case(value: str) -> str:
        result = []
        for i, ch in enumerate(value):
            if ch.isupper() and i > 0:
                prev = value[i - 1]
                if prev.islower() or prev.isdigit():
                    result.append('_')
            result.append(ch.lower())
        return ''.join(result)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'OpenHabBaseItem':
        item_type = payload.get('type')
        item_class, unit = get_item_class(item_type)

        item = item_class(payload)
        item.unit = unit
        return item

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._raw)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, type={self.type!r}, state={self.state!r})"


class OpenHabSwitchItem(OpenHabBaseItem, SwitchItem):
    def on(self) -> None:
        self._set_value('OnOff', 'ON')

    def off(self) -> None:
        self._set_value('OnOff', 'OFF')

    def is_on(self) -> bool:
        return self.state == 'ON'

    def is_off(self) -> bool:
        return self.state == 'OFF'


class OpenHabNumberItem(OpenHabBaseItem, NumberItem):
    def get_value(self) -> float:
        if self.state is None:
            raise ValueError(f"State is None for item '{self.name}', cannot convert to float.")
        try:
            if self.unit_symbol:
                # Remove the unit symbol from the state string if present
                state_str = str(self.state).replace(self.unit_symbol, '').strip()
                return float(state_str)
            else:
                return float(self.state)
        except (ValueError, TypeError):
            print(self.unit)
            print(self.pattern)
            print(self._raw)
            raise ValueError(f"Cannot convert state '{self.state}' to float for item '{self.name}'.")

    def set_value(self, value: Any) -> None:
        self._set_value('Decimal', value)


class OpenHabStringItem(OpenHabBaseItem, StringItem):
    def get_value(self) -> str:
        if self.state is None:
            raise ValueError(f"State is None for item '{self.name}', cannot convert to string.")
        try:
            return str(self.state)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot convert state '{self.state}' to string for item '{self.name}'.")

    def set_value(self, value: Any) -> None:
        self._set_value('String', value)


class OpenHabContactItem(OpenHabBaseItem, ContactItem):
    def is_open(self) -> bool:
        return self.state == 'OPEN'

    def is_closed(self) -> bool:
        return self.state == 'CLOSED'


class OpenHabDimmerItem(OpenHabNumberItem, DimmerItem):
    def percentage(self) -> float:
        return self.get_value()

    def set_percentage(self, value: float) -> None:
        self._set_value('Percent', value)


class OpenHabDateTimeItem(OpenHabBaseItem, DateTimeItem):
    """
    Represents a DateTime item in OpenHAB, which holds a string value. Hence, the get and set method has to do some
    marshalling to convert the string to a datetime object and vice versa. The format used is ISO 8601 with milliseconds
    and timezone. Example: "2023-08-15T14:30:00.000+0200".
    """

    def get_value(self) -> datetime:
        return datetime.strptime(self.state, "%Y-%m-%dT%H:%M:%S.%f%z")

    def set_value(self, value: datetime) -> None:
        formatted_date = value.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + value.strftime("%z")
        self._set_value('DateTime', formatted_date)

class OpenHabColorItem(OpenHabBaseItem, ColorItem):
    def set_value(self, value: Any) -> None:
        self.state = value
        # todo send the values over to OH


class OpenHabPlayerItem(OpenHabBaseItem, PlayerItem):
    def pause(self) -> None:
        self._set_value('PlayPause', 'PAUSE')

    def play(self) -> None:
        self._set_value('PlayPause', 'PLAY')

    def is_playing(self) -> bool:
        return self.state == "PLAY"


class OpenHabGroupItem(OpenHabBaseItem):
    pass


class OpenHabUnknownItem(OpenHabBaseItem):
    pass


_ITEM_TYPE_MAP: Dict[str, Type[OpenHabBaseItem]] = {
    'Switch': OpenHabSwitchItem,
    'Number': OpenHabNumberItem,
    'String': OpenHabStringItem,
    'Contact': OpenHabContactItem,
    'Dimmer': OpenHabDimmerItem,
    'DateTime': OpenHabDateTimeItem,
    'Color': OpenHabColorItem,
    'Player': OpenHabPlayerItem,
    'Group': OpenHabGroupItem,
    'Rollershutter': OpenHabDimmerItem,
}


def get_item_class(item_type: str | None) -> Tuple[Type[OpenHabBaseItem], Union[str, None]]:
    if item_type is None:
        return OpenHabUnknownItem, None

    type = _ITEM_TYPE_MAP.get(item_type, OpenHabUnknownItem)
    if type is not OpenHabUnknownItem:
        return type, None
    elif item_type == 'Number:Temperature':
        return OpenHabNumberItem, 'Temperature'
    else:
        return OpenHabUnknownItem, None


def item_from_payload(payload: Dict[str, Any]) -> OpenHabBaseItem:
    return OpenHabBaseItem.from_payload(payload)
