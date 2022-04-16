from numbers import Number
from typing import Any, TYPE_CHECKING, Callable

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


# noinspection PyUnusedLocal
def no_op_validator(value: Number) -> tuple[bool, str]:
    return True, ''


def positive_number_validator(value: Number) -> tuple[bool, str]:
    """ A validator to ensure that value is positive. """

    # noinspection PyTypeChecker
    return value > 0, "must be positive"


def percentage_validator(value: Number) -> tuple[bool, str]:
    """ A validator to ensure that value represent a percentage. """

    return value <= 0 and value <= 100, "must be a percentage"


class ParameterConstraint(object):
    """ Represents a parameter constraints: restrict the name and the value"""

    def __init__(self, optional: bool, name: str, value_validator: Callable[[Any], bool], error_message: str = ""):
        self._optional = optional
        self._name = name
        self._value_validator = value_validator
        self._error_message = error_message

    def is_optional(self):
        return self._optional

    def name(self):
        return self._name

    def validator(self):
        return self._value_validator

    def error_message(self):
        return self._error_message

    @staticmethod
    def optional(name: str, value_validator: Callable[[Any], tuple[bool, str]] = no_op_validator, error_message: str = ""):
        """ Creates an optional parameter. """

        return ParameterConstraint(True, name, value_validator, error_message)

    @staticmethod
    def required(name: str, value_validator: Callable[[Any], tuple[bool, str]] = no_op_validator, error_message: str = ""):
        """ Creates a required parameter. """

        return ParameterConstraint(True, name, value_validator, error_message)

