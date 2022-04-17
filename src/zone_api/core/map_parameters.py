from typing import Mapping, Any, TYPE_CHECKING, Type, List

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

    def keys(self, action_type: Type) -> List[str]:
        """ @Override """
        prefix = action_type.__name__
        return [key[len(prefix) + 1:] for key in self.values.keys() if key.startswith(prefix)]

    def get_by_type(self, action_type: Type, key: str, default: Any = None):
        """ @Override """
        if not action_type:
            raise ValueError("action_type must not be null")

        action_name = action_type.__name__
        full_key = f"{action_name}.{key}"

        if full_key in self.values.keys():
            return self.values.get(full_key)
        else:
            return default
