from zone_api import platform_encapsulator as pe
from zone_api.core.actions.alert_on_security_alarm_triggered import AlertOnSecurityAlarmTriggered
from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class AlertOnSecurityAlarmTriggeredTest(DeviceTest):
    """ Unit tests for AlertOnSecurityAlarmTriggered. """

    def setUp(self):
        self.alarmPartition, items = self.create_alarm_partition()
        self.set_items(items)
        super(AlertOnSecurityAlarmTriggeredTest, self).setUp()

        self.action = AlertOnSecurityAlarmTriggered()
        self.zone1 = Zone('foyer', [self.alarmPartition]).add_action(self.action)
        self.zm = create_zone_manager([self.zone1])

    def testOnAction_triggered_returnsTrueAndSendAlert(self):
        pe.set_switch_state(self.get_items()[0], True)
        self.sendEventAndAssertAlertContainMessage('Security system is on alarm.')

    def testOnAction_noLongerTriggered_returnsTrueAndSendsInfoAlert(self):
        # initially below threshold
        pe.set_switch_state(self.get_items()[0], True)
        self.sendEventAndAssertAlertContainMessage('Security system is on alarm.')

        # now back to normal
        pe.set_switch_state(self.get_items()[0], False)
        self.sendEventAndAssertAlertContainMessage('Security system is NO LONGER in alarm')

    def sendEventAndAssertAlertContainMessage(self, message):
        event_info = EventInfo(ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED, self.get_items()[0], self.zone1,
                               self.zm, pe.get_event_dispatcher(), None, self.alarmPartition)
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(message in self.zm.get_alert_manager()._lastEmailedSubject)
