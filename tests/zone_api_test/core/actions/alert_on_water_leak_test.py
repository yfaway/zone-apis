from zone_api import platform_encapsulator as pe
from zone_api.core.actions.alert_on_water_leak import AlertOnWaterLeak
from zone_api.core.devices.water_leak_sensor import WaterLeakSensor
from zone_api.core.event_info import EventInfo
from zone_api.core.map_parameters import MapParameters
from zone_api.core.zone import Zone, Level
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class AlertWaterLeakTest(DeviceTest):
    """ Unit tests for AlertOnWaterLeak. """

    def setUp(self):
        items = [pe.create_switch_item('gas_state')]
        self.set_items(items)
        super(AlertWaterLeakTest, self).setUp()

        self.action = AlertOnWaterLeak(MapParameters({}))
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
