from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager
from aaa_modules import platform_encapsulator as pe

from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone, Level, ZoneEvent
from aaa_modules.layout_model.devices.humidity_sensor import HumiditySensor

from aaa_modules.layout_model.actions.alert_on_humidity_out_of_range import AlertOnHumidityOutOfRange


class AlertOnHumidityOutOfRangeTest(DeviceTest):
    """ Unit tests for alert_on_humidity_out_of_range.py. """

    def setUp(self):
        items = [pe.create_number_item('humidity_sensor')]
        self.set_items(items)
        super(AlertOnHumidityOutOfRangeTest, self).setUp()

        self.action = AlertOnHumidityOutOfRange(35, 50, 3)
        self.zone1 = Zone('great room', [], Level.FIRST_FLOOR).addDevice(HumiditySensor(items[0]))

        self.zm = create_zone_manager([self.zone1])

    def testOnAction_zoneDoesNotContainSensor_returnsFalse(self):
        event_info = EventInfo(ZoneEvent.HUMIDITY_CHANGED, self.get_items()[0], Zone('innerZone'),
                               None, pe.get_event_dispatcher())
        value = AlertOnHumidityOutOfRange().onAction(event_info)
        self.assertFalse(value)

    def testOnAction_zoneIsExternal_returnsFalse(self):
        zone = Zone.create_external_zone('porch').addDevice(HumiditySensor(self.get_items()[0]))
        event_info = EventInfo(ZoneEvent.HUMIDITY_CHANGED, self.get_items()[0], zone,
                               None, pe.get_event_dispatcher())
        value = AlertOnHumidityOutOfRange().onAction(event_info)
        self.assertFalse(value)

    def testOnAction_humidityJustBelowMinThresholdButAboveNoticeThreshold_sendsNoAlert(self):
        pe.set_number_value(self.get_items()[0], 34)
        self.sendEventAndAssertNoAlert()

    def testOnAction_lowHumidityAtFirstThreshold_TrueAndSendAlert(self):
        pe.set_number_value(self.get_items()[0], 32)
        self.sendEventAndAssertAlertContainMessage('below the threshold')

    def testOnAction_lowHumidityButNotYetAtSecondThreshold_doNotSendAlert(self):
        pe.set_number_value(self.get_items()[0], 32)
        self.sendEventAndAssertAlertContainMessage('below the threshold')

        self.zm.get_alert_manager().reset()
        pe.set_number_value(self.get_items()[0], 33)
        self.sendEventAndAssertNoAlert()

    def testOnAction_lowHumidityAtSecondThreshold_sendAlert(self):
        pe.set_number_value(self.get_items()[0], 32)
        self.sendEventAndAssertAlertContainMessage('below the threshold')

        pe.set_number_value(self.get_items()[0], 29)
        self.sendEventAndAssertAlertContainMessage('below the threshold')

    def testOnAction_humidityJustAboveMinThresholdButAboveNoticeThreshold_sendsNoAlert(self):
        pe.set_number_value(self.get_items()[0], 51)
        self.sendEventAndAssertNoAlert()

    def testOnAction_highHumidityAtFirstThreshold_TrueAndSendAlert(self):
        pe.set_number_value(self.get_items()[0], 53)
        self.sendEventAndAssertAlertContainMessage('above the threshold')

    def testOnAction_highHumidityButNotYetAtSecondThreshold_doNotSendAlert(self):
        pe.set_number_value(self.get_items()[0], 53)
        self.sendEventAndAssertAlertContainMessage('above the threshold')

        self.zm.get_alert_manager().reset()
        pe.set_number_value(self.get_items()[0], 54)
        self.sendEventAndAssertNoAlert()

    def testOnAction_highHumidityAtSecondThreshold_sendAlert(self):
        pe.set_number_value(self.get_items()[0], 54)
        self.sendEventAndAssertAlertContainMessage('above the threshold')

        pe.set_number_value(self.get_items()[0], 56)
        self.sendEventAndAssertAlertContainMessage('above the threshold')

    def testOnAction_humidityWithinThreshold_returnsTrueAndSendsNoAlert(self):
        pe.set_number_value(self.get_items()[0], 40)
        self.sendEventAndAssertNoAlert()

    def testOnAction_humidityBackToNormal_returnsTrueAndSendsInfoAlert(self):
        # initially below threshold
        pe.set_number_value(self.get_items()[0], 20)
        self.sendEventAndAssertAlertContainMessage('below the threshold')

        # now back to normal
        pe.set_number_value(self.get_items()[0], 40)
        self.sendEventAndAssertAlertContainMessage('back to the normal range')

    def sendEventAndAssertNoAlert(self):
        event_info = EventInfo(ZoneEvent.HUMIDITY_CHANGED, self.get_items()[0], self.zone1,
                               self.zm, pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertEqual(None, self.zm.get_alert_manager()._lastEmailedSubject)

    def sendEventAndAssertAlertContainMessage(self, message):
        event_info = EventInfo(ZoneEvent.HUMIDITY_CHANGED, self.get_items()[0], self.zone1,
                               self.zm, pe.get_event_dispatcher())
        value = self.action.onAction(event_info)
        self.assertTrue(value)
        self.assertTrue(message in self.zm.get_alert_manager()._lastEmailedSubject)
