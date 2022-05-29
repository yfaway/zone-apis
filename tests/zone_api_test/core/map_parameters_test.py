import unittest
from typing import List

from zone_api.core.action import Action
from zone_api.core.map_parameters import MapParameters
from zone_api.core.parameters import percentage_validator, positive_number_validator, ParameterConstraint


class MapParameterTest(unittest.TestCase):
    class MyAction(Action):
        @staticmethod
        def supported_parameters() -> List[ParameterConstraint]:
            return [ParameterConstraint.optional('value1', positive_number_validator),
                    ParameterConstraint.optional('value2', percentage_validator, "is bad")
                    ]

    def testCtor_nullMap_throwException(self):
        with self.assertRaises(ValueError) as cm:
            # noinspection PyTypeChecker
            MapParameters(None)

        self.assertEqual('values must not be none', cm.exception.args[0])

    def testCtor_emptyKey_raiseException(self):
        with self.assertRaises(ValueError) as cm:
            MapParameters({'': 15})

        self.assertEqual('Must be of format: action_type_name.key - ', cm.exception.args[0])

    def testCtor_missionActionTypeInKey_raiseException(self):
        with self.assertRaises(ValueError) as cm:
            MapParameters({'aKey': 15})

        self.assertEqual('Must be of format: action_type_name.key - aKey', cm.exception.args[0])

    def testGet_nullAction_throwException(self):
        params = MapParameters(dict())

        with self.assertRaises(ValueError) as cm:
            # noinspection PyTypeChecker
            params.get(None, "aKey")

        self.assertEqual('action must not be null', cm.exception.args[0])

    def testGet_keyExists_returnsExpectedValue(self):
        params = MapParameters({"MyAction.myKey": 1})
        self.assertEqual(params.get(MapParameterTest.MyAction(MapParameters({})), 'myKey'), 1)

    def testGet_keyDoesNotExistAndNoDefault_returnsNone(self):
        params = MapParameters({})
        self.assertEqual(params.get(MapParameterTest.MyAction(MapParameters({})), 'myKey'), None)

    def testGet_keyDoesNotExistAndWithDefault_returnsDefault(self):
        params = MapParameters({})
        self.assertEqual(params.get(MapParameterTest.MyAction(MapParameters({})), 'myKey', 1), 1)

    def testValidate_actionDoesNotDeclareParameters_returnsTrue(self):
        class MyActionWithNoParams(Action):
            pass

        params = MapParameters({'MyAction.value1': 2})
        (validated, errors) = params.validate([MyActionWithNoParams, MapParameterTest.MyAction])
        self.assertTrue(validated)
        self.assertEqual(len(errors), 0)

    def testValidate_validValues_returnsTrue(self):
        params = MapParameters({'MyAction.value1': 2, 'MyAction.value2': 2})
        (validated, errors) = params.validate([MapParameterTest.MyAction])

        self.assertTrue(validated)
        self.assertEqual(len(errors), 0)

    def testValidate_containsInvalidAction_returnsFalse(self):
        params = MapParameters({'MyAction.value1': 2, 'MyAction.value2': 2, 'NotMyAction.key': 15})
        (validated, errors) = params.validate([MapParameterTest.MyAction])

        self.assertFalse(validated)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], "Unsupported action types: NotMyAction")

    def testValidate_valueNotValidatedDefaultErrorMessage_returnsFalse(self):
        params = MapParameters({'MyAction.value1': -2})
        (validated, errors) = params.validate([MapParameterTest.MyAction])

        self.assertFalse(validated)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], "value1 must be positive")

    def testValidate_valueNotValidatedWithErrorMessage_returnsFalse(self):
        params = MapParameters({'MyAction.value2': -2})
        (validated, errors) = params.validate([MapParameterTest.MyAction])

        self.assertFalse(validated)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], f"value2 {MapParameterTest.MyAction.supported_parameters()[1].error_message()}")

    def testValidate_multipleValueNotValidated_returnsFalse(self):
        params = MapParameters({'MyAction.value1': -2, 'MyAction.value2': -2})
        (validated, errors) = params.validate([MapParameterTest.MyAction])

        self.assertFalse(validated)
        self.assertEqual(len(errors), 2)

    def testValidate_keyNotSupported_returnsFalse(self):
        params = MapParameters({'MyAction.badKey1': 2, 'MyAction.badKey2': 2})
        (validated, errors) = params.validate([MapParameterTest.MyAction])

        self.assertFalse(validated)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], "Unsupported keys: badKey1, badKey2")
