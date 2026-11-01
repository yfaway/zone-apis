from __future__ import annotations

from numbers import Number
from typing import Any, Dict, List, Tuple, Type, Union
from collections.abc import Callable


class BaseItem:
    """Base model mirroring the OpenHAB REST item payload."""

    def __init__(self, payload: Dict[str, Any]):
        self._raw: Dict[str, Any] = payload or {}

        # Common fields from the OpenHAB REST API.
        self.name: str = self._raw.get('name') or ""
        self.type: str = self._raw.get('type') or ""
        self.state: Any = self._raw.get('state')
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
        self.min: Any = self._raw.get('min')
        self.max: Any = self._raw.get('max')
        self.step: Any = self._raw.get('step')
        self.pattern: str | None = self._raw.get('pattern')
        self.options: List[Dict[str, Any]] | None = self._raw.get('options')
        self.filters: List[Dict[str, Any]] | None = self._raw.get('filters')
        self.unit: Union[str, None]

        # Import any unknown extra fields using snake_case naming.
        for key, value in self._raw.items():
            snake_key = self._to_snake_case(key)
            if not hasattr(self, snake_key):
                setattr(self, snake_key, value)

    def listen_event(self, callback: Callable[[Any], Any],
                     event_filter: Any) -> None:
        pass 

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
    def from_payload(cls, payload: Dict[str, Any]) -> 'BaseItem':
        item_type = payload.get('type')
        item_class, unit = get_item_class(item_type)

        item = item_class(payload)
        item.unit = unit
        return item

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._raw)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, type={self.type!r}, state={self.state!r})"


class SwitchItem(BaseItem):
    def on(self) -> None:
        self.state = "ON"

    def off(self) -> None:
        self.state = "OFF"


class NumberItem(BaseItem):
    def get_value(self) -> float | None:
        if self.state is None:
            return None
        try:
            return float(self.state)
        except (ValueError, TypeError):
            return None

    def set_value(self, value: Any) -> None:
        self.state = value


class StringItem(BaseItem):
    def set_value(self, value: Any) -> None:
        self.state = value


class ContactItem(BaseItem):
    pass


class DimmerItem(NumberItem):
    def percentage(self) -> int | None:
        if self.state is None:
            return None
        try:
            return int(self.state)
        except (ValueError, TypeError):
            return None

    def set_percentage(self, value: int) -> None:
        self.state = value


class DateTimeItem(BaseItem):
    def set_value(self, value: Any) -> None:
        self.state = value


class ColorItem(BaseItem):
    def set_value(self, value: Any) -> None:
        self.state = value


class PlayerItem(BaseItem):
    def pause(self) -> None:
        self.state = "PAUSE"

    def play(self) -> None:
        self.state = "PLAY"

    def is_playing(self) -> bool:
        return self.state == "PLAY"

class GroupItem(BaseItem):
    pass


class UnknownItem(BaseItem):
    pass


_ITEM_TYPE_MAP: Dict[str, Type[BaseItem]] = {
    'Switch': SwitchItem,
    'Number': NumberItem,
    'String': StringItem,
    'Contact': ContactItem,
    'Dimmer': DimmerItem,
    'DateTime': DateTimeItem,
    'Color': ColorItem,
    'Player': PlayerItem,
    'Group': GroupItem,
    'Rollershutter': DimmerItem,
}


def get_item_class(item_type: str | None) -> Tuple[Type[BaseItem], Union[str, None]]:
    if item_type is None:
        return UnknownItem, None

    type = _ITEM_TYPE_MAP.get(item_type, UnknownItem)
    if type is not UnknownItem:
        return type, None
    elif item_type == 'Number:Temperature':
        return NumberItem, 'Temperature'
    else:
        return UnknownItem, None


def item_from_payload(payload: Dict[str, Any]) -> BaseItem:
    return BaseItem.from_payload(payload)
