from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.security_alert_in_vacation_mode import SecurityAlertInVacationMode
from aaa_modules.layout_model.devices.contact import Window, Door
from aaa_modules.layout_model.devices.thermostat import EcobeeThermostat
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone
from aaa_modules.layout_model.zone_event import ZoneEvent
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager


class SecurityAlertInVacationModeTest(DeviceTest):
    """ Unit tests for SecurityAlertInVacationMode. """

    def setUp(self):
        self.alarmPartition, items = self.create_alarm_partition()
        items = items + [pe.create_switch_item('door'), pe.create_switch_item('window'),
                         pe.create_string_item('EcobeeName'), pe.create_string_item('EcobeeState')]
        self.set_items(items)
        super(SecurityAlertInVacationModeTest, self).setUp()

        self.door = Door(items[-4])
        self.window = Window(items[-3])
        self.thermostat = EcobeeThermostat(items[-2], items[-1])

        self.action = SecurityAlertInVacationMode()
        self.zone1 = Zone('foyer', [self.alarmPartition, self.thermostat]).add_action(self.action)
        self.zone2 = Zone('Porch', [self.door, self.window])
        self.zm = create_zone_manager([self.zone1, self.zone2])

    def testOnAction_armAwayNotInVacationMode_returnsFalse(self):
        self.send_event_and_assert_false_action_result(ZoneEvent.PARTITION_ARMED_AWAY)

    def testOnAction_disarmFromAwayNotInVacationMode_returnsFalse(self):
        self.send_event_and_assert_false_action_result(ZoneEvent.PARTITION_DISARMED_FROM_AWAY)

    def testOnAction_armAwayInVacationMode_returnsFalse(self):
        self.send_event_and_assert_alert_contain_message(ZoneEvent.PARTITION_ARMED_AWAY, "PARTITION_ARMED_AWAY")

    def testOnAction_disarmFromAwayInVacationMode_returnsFalse(self):
        self.send_event_and_assert_alert_contain_message(ZoneEvent.PARTITION_DISARMED_FROM_AWAY,
                                                         "PARTITION_DISARMED_FROM_AWAY")

    def testOnAction_doorOpenNotInVacationMode_returnsFalse(self):
        self.send_contact_event_and_assert_false_action_result(ZoneEvent.DOOR_OPEN, self.door)

    def testOnAction_doorOpenInVacationMode_returnsFalse(self):
        self.send_contact_event_and_assert_alert_contain_message(ZoneEvent.DOOR_OPEN,
                                                                 self.door, "Porch event: DOOR_OPEN")

    def testOnAction_windowClosedNotInVacationMode_returnsFalse(self):
        self.send_contact_event_and_assert_false_action_result(ZoneEvent.WINDOW_CLOSED, self.window)

    def testOnAction_windowClosedInVacationMode_returnsFalse(self):
        self.send_contact_event_and_assert_alert_contain_message(ZoneEvent.WINDOW_CLOSED,
                                                                 self.window, "Porch event: WINDOW_CLOSED")

    def send_event_and_assert_alert_contain_message(self, event, message):
        pe.set_string_value(self.get_items()[-1], 'vacation')

        event_info = EventInfo(event, self.get_items()[0], self.zone1,
                               self.zm, pe.get_event_dispatcher(), None, self.alarmPartition)
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(message in self.zm.get_alert_manager()._lastEmailedSubject)

    def send_event_and_assert_false_action_result(self, event: ZoneEvent):
        event_info = EventInfo(event, self.get_items()[0], self.zone1,
                               self.zm, pe.get_event_dispatcher(), None, self.alarmPartition)
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def send_contact_event_and_assert_alert_contain_message(self, event, sensor, message):
        pe.set_string_value(self.get_items()[-1], 'vacation')

        event_info = EventInfo(event, sensor.get_item(), self.zone1,
                               self.zm, pe.get_event_dispatcher(), self.zone2, sensor)
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(message in self.zm.get_alert_manager()._lastEmailedSubject)
        #self.assertEquals(message, self.zm.get_alert_manager()._lastEmailedSubject)

    def send_contact_event_and_assert_false_action_result(self, event: ZoneEvent, sensor):
        event_info = EventInfo(event, sensor.get_item(), self.zone1,
                               self.zm, pe.get_event_dispatcher(), self.zone2, sensor)
        value = self.action.on_action(event_info)
        self.assertFalse(value)
