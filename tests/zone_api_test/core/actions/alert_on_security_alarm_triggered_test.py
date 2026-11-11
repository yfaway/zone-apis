from zone_api import platform_encapsulator as pe
from zone_api.core.actions.alert_on_security_alarm_triggered import AlertOnSecurityAlarmTriggered
from zone_api.core.devices.contact import Door
from zone_api.core.event_info import EventInfo
from zone_api.core.map_parameters import MapParameters
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager
from zone_api.models import SwitchItem


class AlertOnSecurityAlarmTriggeredTest(DeviceTest):
    """ Unit tests for AlertOnSecurityAlarmTriggered. """

    def setUp(self):
        self.alarm_partition, items = self.create_alarm_partition()
        items = items + [SwitchItem('Door', "OFF"), SwitchItem('Tripped', "OFF")]

        self.set_items(items)
        super(AlertOnSecurityAlarmTriggeredTest, self).setUp()

        self.action = AlertOnSecurityAlarmTriggered(MapParameters({}))

        self.door = Door(items[-2], items[-1])
        self.zone1 = Zone('Foyer', [self.alarm_partition, self.door]).add_action(self.action)
        self.zm = create_zone_manager([self.zone1])

    def testOnAction_triggered_returnsTrueAndSendAlert(self):
        self.alarm_partition.get_item().on()
        self.get_items()[-1].on() # tripped
        self.sendEventAndAssertAlertContainMessage(
            ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED, self.alarm_partition.get_item(),
            'Security system is on alarm (Foyer Door).')

    def testOnAction_noLongerTriggered_returnsTrueAndSendsInfoAlert(self):
        self.testOnAction_triggered_returnsTrueAndSendAlert()  # set up the regular alarm first.

        # now back to normal
        self.alarm_partition.get_item().off()
        self.sendEventAndAssertAlertContainMessage(
            ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED, self.alarm_partition.get_item(),
            'Security system is NO LONGER in alarm')

    def testOnAction_fireKeyTriggered_returnsTrueAndSendAlert(self):
        item = self.alarm_partition.get_panel_fire_key_alarm_item()
        item.on()
        self.sendEventAndAssertAlertContainMessage(
            ZoneEvent.PARTITION_FIRE_ALARM_STATE_CHANGED, item, 'Security system is on FIRE alarm.')

    def testOnAction_fireAlarmNoLongerTriggered_returnsTrueAndSendAlert(self):
        self.testOnAction_fireKeyTriggered_returnsTrueAndSendAlert()  # set up the fire alarm first.

        item = self.alarm_partition.get_panel_fire_key_alarm_item()
        item.off()
        self.sendEventAndAssertAlertContainMessage(
            ZoneEvent.PARTITION_FIRE_ALARM_STATE_CHANGED, item, "Security system is NO LONGER in FIRE alarm")

    def sendEventAndAssertAlertContainMessage(self, event, item, message):
        event_info = EventInfo(event, item, self.zone1, self.zm, pe.get_event_dispatcher(), None, self.alarm_partition)
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(message in self.zm.get_alert_manager()._lastEmailedSubject)
