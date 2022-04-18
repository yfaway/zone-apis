import re
from typing import Mapping, Any, TYPE_CHECKING, Type, List, Set

from zone_api.core.parameters import Parameters

if TYPE_CHECKING:
    from zone_api.core.action import Action


class MapParameters(Parameters):
    """
    An implementation of Parameters backed by a dictionary.
    """

    def __init__(self, values: Mapping[str, Any]):
        """
        Creates a new object with the provided map.
        :raise ValueError: if the key does not confirm to this pattern: ActionTypeName.key.
        """
        if values is None:
            raise ValueError("values must not be none")

        pattern = re.compile(r'\w+\.\S+')
        for key in values.keys():
            if not pattern.match(key):
                raise ValueError(f"Must be of format: action_type_name.key - {key}")

        self.values = values

    def keys(self, action_type: Type) -> List[str]:
        """ @Override """
        prefix = action_type.__name__
        return [key[len(prefix) + 1:] for key in self.values.keys() if key.startswith(prefix)]

    def unique_action_type_names(self) -> Set[str]:
        """ @Override """
        action_type_names = []
        for key in self.values.keys():
            idx = key.find('.')
            if idx == -1:
                raise ValueError(f"Must be of format: action_type_name.key - {key}")

            action_type_names.append(key[0: idx])

        return set(action_type_names)

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
