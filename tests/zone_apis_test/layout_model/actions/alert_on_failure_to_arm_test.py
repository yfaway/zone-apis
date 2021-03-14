from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.alert_on_failure_to_arm import AlertOnFailureToArm
from aaa_modules.layout_model.devices.contact import Door, Window
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone
from aaa_modules.layout_model.zone_event import ZoneEvent
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager


class AlertOnFailureToArmTest(DeviceTest):
    """ Unit tests for AlertOnFailureToArm. """

    def setUp(self):
        self.alarmPartition, items = self.create_alarm_partition()

        items = items + [pe.create_switch_item('door'), pe.create_switch_item('window')]
        self.set_items(items)
        super(AlertOnFailureToArmTest, self).setUp()

        self.door = Door(items[-2])
        self.window = Window(items[-1])

        self.action = AlertOnFailureToArm()

        self.zone1 = Zone('foyer', [self.alarmPartition]).add_action(self.action)
        self.zone2 = Zone.create_external_zone('foyer').add_device(self.door).add_device(self.window)

        self.zm = create_zone_manager([self.zone1, self.zone2])

    def testOnAction_noDoorOpen_returnsTrueAndNoAlert(self):
        event_info = EventInfo(ZoneEvent.PARTITION_RECEIVE_ARM_AWAY, self.alarmPartition.get_arm_mode_item(),
                               self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.zm.get_alert_manager()._lastEmailedSubject is None)

    def testOnAction_doorIsOpen_returnsTrueAndSendsInfoAlert(self):
        pe.set_switch_state(self.door.get_item(), True)
        self.sendEventAndAssertAlertContainMessage(ZoneEvent.PARTITION_RECEIVE_ARM_AWAY, 'a door is open')

    def testOnAction_windowIsOpen_returnsTrueAndSendsInfoAlert(self):
        pe.set_switch_state(self.window.get_item(), True)
        self.sendEventAndAssertAlertContainMessage(ZoneEvent.PARTITION_RECEIVE_ARM_STAY, 'a window is open')

    def sendEventAndAssertAlertContainMessage(self, event: ZoneEvent, message):
        event_info = EventInfo(event, self.alarmPartition.get_arm_mode_item(), self.zone1, self.zm,
                               pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(message in self.zm.get_alert_manager()._lastEmailedSubject)
