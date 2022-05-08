from zone_api import platform_encapsulator as pe
from zone_api.core.actions.alert_on_bad_computer_states import AlertOnBadComputerStates
from zone_api.core.devices.computer import Computer
from zone_api.core.event_info import EventInfo
from zone_api.core.map_parameters import MapParameters
from zone_api.core.zone import Zone, Level
from zone_api.core.zone_event import ZoneEvent
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class AlertOnBadComputerStatesTest(DeviceTest):
    """ Unit tests for AlertOnBadComputerStates. """

    def setUp(self):
        items = [pe.create_number_item('cpu_temp'), pe.create_number_item('gpu_temp')]
        self.set_items(items)
        super(AlertOnBadComputerStatesTest, self).setUp()

        self.action = AlertOnBadComputerStates(MapParameters({}))

        self.zone1 = Zone('office', [], Level.FIRST_FLOOR) \
            .add_action(self.action) \
            .add_device(Computer("Desktop", items[0], items[1]))

        self.zm = create_zone_manager([self.zone1])

    def testOnAction_cpuTemperatureAboveThreshold_returnsTrueAndSendAlert(self):
        pe.set_number_value(self.get_items()[0], 80)
        self.sendEventAndAssertAlertContainMessage(
            ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED, self.get_items()[0],
            'CPU temperature for Computer: Desktop at 80 is above the threshold of 70 degree.')

    def testOnAction_cpuTemperatureBackToNormal_returnsTrueAndSendsInfoAlert(self):
        # initially cross threshold
        pe.set_number_value(self.get_items()[0], 80)
        self.sendEventAndAssertAlertContainMessage(
            ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED, self.get_items()[0], 'above the threshold')

        # now back to normal
        pe.set_number_value(self.get_items()[0], 60)
        self.sendEventAndAssertAlertContainMessage(
            ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED, self.get_items()[0], 'is back to normal')
        self.assertTrue(self.action._alerts[0] is None)

    def testOnAction_gpuTemperatureAboveThreshold_returnsTrueAndSendAlert(self):
        pe.set_number_value(self.get_items()[1], 80)
        self.sendEventAndAssertAlertContainMessage(
            ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED, self.get_items()[1],
            'GPU temperature for Computer: Desktop at 80 is above the threshold of 70 degree.')

    def testOnAction_gpuTemperatureBackToNormal_returnsTrueAndSendsInfoAlert(self):
        # initially cross threshold
        pe.set_number_value(self.get_items()[1], 80)
        self.sendEventAndAssertAlertContainMessage(
            ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED, self.get_items()[1], 'above the threshold')

        # now back to normal
        pe.set_number_value(self.get_items()[1], 60)
        self.sendEventAndAssertAlertContainMessage(
            ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED, self.get_items()[1], 'is back to normal')
        self.assertTrue(self.action._alerts[1] is None)

    def sendEventAndAssertAlertContainMessage(self, event: ZoneEvent, item, message):
        event_info = EventInfo(event, item, self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(message in self.zm.get_alert_manager()._lastEmailedSubject)
