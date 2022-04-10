from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from zone_api.core.action import Action


class Parameters(object):
    """
    An base class to provide retrieve the parameter for an action.
    """

    def get(self, action: 'Action', name: str, default: Any = None):
        """
        Returns the named parameter for the given action. If none is available, returns the default value.
        This base class always return the default value.
        """
        return default
