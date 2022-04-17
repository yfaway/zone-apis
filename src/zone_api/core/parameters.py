from numbers import Number
from typing import Any, TYPE_CHECKING, Callable, List, Tuple, Type

if TYPE_CHECKING:
    from zone_api.core.action import Action


class Parameters(object):
    """
    An base class to provide retrieve the parameter for an action.
    """

    def keys(self, action_type: Type) -> List[str]:
        """ Returns all the keys available for the provided action type. """
        raise NotImplemented()

    # noinspection PyMethodMayBeStatic
    def get_by_type(self, action_type: Type, name: str, default: Any = None):
        """
        Returns the named parameter for the given action type. If none is available, returns the default value.
        This base class always return the default value.
        The subclass shall overrides this method.
        """
        raise NotImplemented()

    def get(self, action: 'Action', name: str, default: Any = None):
        """ Returns the named parameter for the given action via Parameters::get_by_type() """

        if not action:
            raise ValueError("action must not be null")

        return self.get_by_type(action.__class__, name, default)

    def validate(self, action_type: Type) -> Tuple[bool, List[str]]:
        """
        Validates if the values contained in this object matches with the action_type's declared available types
        via action_type::supported_parameters() function.
        Also returns error if a key is not supported by the action type.

        :return: a tuple of boolean value and a list of errors
        """
        if not hasattr(action_type, 'supported_parameters'):
            return True, []

        error_messages = []
        # noinspection PyUnresolvedReferences
        constraints: List[ParameterConstraint] = action_type.supported_parameters()
        for constraint in constraints:
            value = self.get_by_type(action_type, constraint.name())
            if value is not None:  # parameter is defined
                (qualified, error) = constraint.validator()(value)
                if not qualified:  # value doesn't pass the constraint validator function
                    if constraint.error_message() is not None:
                        error_messages.append(f"{constraint.name()} {constraint.error_message()}")
                    else:
                        error_messages.append(f"{constraint.name()} {error}")

        # Check if any key is not supported
        available_keys = self.keys(action_type)
        for constraint in constraints:
            if constraint.name() in available_keys:
                available_keys.remove(constraint.name())

        if len(available_keys) > 0:
            error_messages.append("Unsupported keys: " + ', '.join(available_keys))

        if len(error_messages) > 0:
            return False, error_messages
        else:
            return True, []


# noinspection PyUnusedLocal
def no_op_validator(value: Number) -> tuple[bool, str]:
    return True, ''


def positive_number_validator(value: Number) -> tuple[bool, str]:
    """ A validator to ensure that value is positive. """

    # noinspection PyTypeChecker
    return value > 0, "must be positive"


def percentage_validator(value: Number) -> tuple[bool, str]:
    """ A validator to ensure that value represent a percentage. """

    return 0 <= value <= 100, "must be a percentage"


class ParameterConstraint(object):
    """ Represents a parameter constraints: restrict the name and the value"""

    def __init__(self, optional: bool, name: str, value_validator: Callable[[Any], tuple[bool, str]],
                 error_message: str = None):
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
    def optional(name: str, value_validator: Callable[[Any], tuple[bool, str]] = no_op_validator,
                 error_message: str = None):
        """ Creates an optional parameter. """

        return ParameterConstraint(True, name, value_validator, error_message)

    @staticmethod
    def required(name: str, value_validator: Callable[[Any], tuple[bool, str]] = no_op_validator,
                 error_message: str = None):
        """ Creates a required parameter. """

        return ParameterConstraint(True, name, value_validator, error_message)
