import unittest
from datetime import datetime
from typing import List, Tuple
from unittest.mock import MagicMock

from HABApp.core.Items import ItemAlreadyExistsError

from zone_api import platform_encapsulator as pe
from zone_api.alert_manager import AlertManager
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.zone import Zone
from zone_api.core.zone_manager import ZoneManager


# noinspection PyProtectedMember
def create_zone_manager(zones: List[Zone]) -> ImmutableZoneManager:
    zm = ZoneManager()
    for zone in zones:
        zm.add_zone(zone)

    yaml_string = """
        system:
          alerts:
            email:
              owner-email-addresses:
                - user1@gmail.com
                - user2@gmail.com
              admin-email-addresses:
                - admin1@gmail.com"""

    import io
    import yaml
    config = yaml.safe_load(io.StringIO(yaml_string))
    alert_manager = AlertManager.test_instance(config)
    alert_manager._process_further_actions_for_critical_alert = MagicMock()

    immutable_zm = zm.get_immutable_instance().set_alert_manager(alert_manager)

    return immutable_zm


class DeviceTest(unittest.TestCase):
    """
    Base test class for Device derived sensors.
    """

    def setUp(self):
        """ Adds the items to the registry. """

        pe.set_in_unit_tests(True)

        for item in self.items:
            try:
                pe.register_test_item(item)
            except ItemAlreadyExistsError:
                pass

    def tearDown(self):
        """ Removes the items from the registry. """
        for item in self.items:
            pe.unregister_test_item(item)

        pe.set_in_unit_tests(False)

    def set_items(self, items: list) -> None:
        """
        Configures the test items to register / unregister before and after each test.
        :param items: list of items
        """
        self.items = items

    def get_items(self) -> list:
        return self.items

    # noinspection PyMethodMayBeStatic
    def create_audio_sink(self, suffix='1') -> Tuple[ChromeCastAudioSink, List]:
        """ Returns an audio sink and its items. """
        items = [pe.create_player_item(f'_testPlayer_{suffix}'),
                 pe.create_number_item(f'_testVolume_{suffix}'),
                 pe.create_string_item(f'_testTitle_{suffix}'),
                 pe.create_switch_item(f'_testIdling_{suffix}'),
                 ]
        sink = ChromeCastAudioSink('sinkName', items[0], items[1], items[2], items[3])
        sink._set_test_mode()

        return sink, items

    # noinspection PyMethodMayBeStatic
    def create_outside_time_range(self) -> str:
        """ Creates a time range string that is outside the current time."""
        now = datetime.now()
        start_hour = (now.hour + 1) % 24
        end_hour = (start_hour + 1) % 24

        return f'{start_hour} - {end_hour}'

    # noinspection PyMethodMayBeStatic
    def create_alarm_partition(self):
        items = [pe.create_switch_item('AlarmStatus'), pe.create_number_item('_AlarmMode'),
                 pe.create_string_item("send-command"), pe.create_switch_item('fire-alarm')]
        alarm_partition = AlarmPartition(*items)

        return alarm_partition, items
