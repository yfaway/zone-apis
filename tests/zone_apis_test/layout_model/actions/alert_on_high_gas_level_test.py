from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone, Level
from aaa_modules.layout_model.zone_event import ZoneEvent
from aaa_modules.layout_model.devices.gas_sensor import SmokeSensor
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager

from aaa_modules.layout_model.actions.alert_on_high_gas_level import AlertOnHighGasLevel


class AlertOnHighGasLevelTest(DeviceTest):
    """ Unit tests for alert_on_high_gas_level.py. """

    def setUp(self):
        items = [pe.create_switch_item('gas_state'), pe.create_number_item('gas_value'), ]
        self.set_items(items)
        super(AlertOnHighGasLevelTest, self).setUp()

        self.action = AlertOnHighGasLevel()
        self.zone1 = Zone('great room', [], Level.FIRST_FLOOR) \
            .add_action(self.action) \
            .add_device(SmokeSensor(items[1], items[0]))   # index reverse order intentionally

        self.zm = create_zone_manager([self.zone1])

    def testOnAction_zoneDoesNotContainSensor_returnsFalse(self):
        event_info = EventInfo(ZoneEvent.GAS_TRIGGER_STATE_CHANGED, self.get_items()[0], Zone('innerZone'),
                               None, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_crossThreshold_returnsTrueAndSendAlert(self):
        pe.set_switch_state(self.get_items()[0], True)
        self.sendEventAndAssertAlertContainMessage('above normal level')

    def testOnAction_noLongerTriggered_returnsTrueAndSendsInfoAlert(self):
        # initially below threshold
        pe.set_switch_state(self.get_items()[0], True)
        self.sendEventAndAssertAlertContainMessage('above normal level')

        # now back to normal
        pe.set_switch_state(self.get_items()[0], False)
        self.sendEventAndAssertAlertContainMessage('back to normal')

    def sendEventAndAssertAlertContainMessage(self, message):
        event_info = EventInfo(ZoneEvent.GAS_TRIGGER_STATE_CHANGED, self.get_items()[0], self.zone1,
                               self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(message in self.zm.get_alert_manager()._lastEmailedSubject)
