import unittest

from zone_api.core.action import Action
from zone_api.core.map_parameters import MapParameters


class MapParameterTest(unittest.TestCase):
    class MyAction(Action):
        pass

    def testCtor_nullMap_throwException(self):
        with self.assertRaises(ValueError) as cm:
            # noinspection PyTypeChecker
            MapParameters(None)

        self.assertEqual('values must not be none', cm.exception.args[0])

    def testGet_nullAction_throwException(self):
        params = MapParameters(dict())

        with self.assertRaises(ValueError) as cm:
            params.get(None, "aKey")

        self.assertEqual('action must not be null', cm.exception.args[0])

    def testGet_keyExists_returnsExpectedValue(self):
        params = MapParameters({"MyAction.myKey": 1})
        self.assertEqual(params.get(MapParameterTest.MyAction(), 'myKey'), 1)

    def testGet_keyDoesNotExistAndNoDefault_returnsNone(self):
        params = MapParameters({})
        self.assertEqual(params.get(MapParameterTest.MyAction(), 'myKey'), None)

    def testGet_keyDoesNotExistAndWithDefault_returnsDefault(self):
        params = MapParameters({})
        self.assertEqual(params.get(MapParameterTest.MyAction(), 'myKey', 1), 1)
