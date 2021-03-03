from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.alert_on_water_leak import AlertOnWaterLeak
from aaa_modules.layout_model.devices.water_leak_sensor import WaterLeakSensor
from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone, Level
from aaa_modules.layout_model.zone_event import ZoneEvent
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager


class AlertWaterLeakTest(DeviceTest):
    """ Unit tests for AlertOnWaterLeak. """

    def setUp(self):
        items = [pe.create_switch_item('gas_state')]
        self.set_items(items)
        super(AlertWaterLeakTest, self).setUp()

        self.action = AlertOnWaterLeak()
        self.zone1 = Zone('great room', [], Level.FIRST_FLOOR) \
            .add_action(self.action) \
            .add_device(WaterLeakSensor(items[0]))

        self.zm = create_zone_manager([self.zone1])

    def testOnAction_leakDetected_returnsTrueAndSendAlert(self):
        pe.set_switch_state(self.get_items()[0], True)
        self.sendEventAndAssertAlertContainMessage('Water leak detected in')

    def testOnAction_noLongerTriggered_returnsTrueAndSendsInfoAlert(self):
        # initially leak detected
        pe.set_switch_state(self.get_items()[0], True)
        self.sendEventAndAssertAlertContainMessage('Water leak detected in')

        # now back to normal
        pe.set_switch_state(self.get_items()[0], False)
        self.sendEventAndAssertAlertContainMessage('No more water leak detected in')

    def sendEventAndAssertAlertContainMessage(self, message):
        event_info = EventInfo(ZoneEvent.WATER_LEAK_STATE_CHANGED, self.get_items()[0], self.zone1,
                               self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(message in self.zm.get_alert_manager()._lastEmailedSubject)
