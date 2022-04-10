from typing import Mapping, Any, TYPE_CHECKING

from zone_api.core.parameters import Parameters

if TYPE_CHECKING:
    from zone_api.core.action import Action


class MapParameters(Parameters):
    """
    An implementation of Parameters backed by a dictionary.
    """

    def __init__(self, values: Mapping[str, Any]):
        if values is None:
            raise ValueError("values must not be none")

        self.values = values

    def get(self, action: 'Action', key: str, default: Any = None):
        """ @Override """
        if not action:
            raise ValueError("action must not be null")

        action_name = action.__class__.__name__
        full_key = f"{action_name}.{key}"

        if full_key in self.values.keys():
            return self.values.get(full_key)
        else:
            return default
