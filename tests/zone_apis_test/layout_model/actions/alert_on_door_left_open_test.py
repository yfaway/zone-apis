import time

from aaa_modules.alert_manager import AlertManager
from aaa_modules import platform_encapsulator as pe

from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone, ZoneEvent
from aaa_modules.layout_model.devices.contact import Door
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager

from aaa_modules.layout_model.actions.alert_on_door_left_open import AlertOnExternalDoorLeftOpen


class AlertOnExternalDoorLeftOpenTest(DeviceTest):
    """ Unit tests for alert_on_door_left_open.py. """

    def setUp(self):
        items = [pe.create_switch_item('Door1'), pe.create_switch_item('Door2')]

        self.set_items(items)
        super(AlertOnExternalDoorLeftOpenTest, self).setUp()

        self.zone1 = Zone.create_external_zone('porch').addDevice(Door(items[0]))
        self.zone2 = Zone.create_external_zone('garage').addDevice(Door(items[1]))
        self.alertManager = AlertManager()

        self.zm = create_zone_manager([self.zone1, self.zone2])

    def testOnAction_notAnExternalZone_returnsFalse(self):
        event_info = EventInfo(ZoneEvent.CONTACT_OPEN, self.get_items()[0], Zone('innerZone'), self.zm,
                               pe.get_event_dispatcher())
        value = AlertOnExternalDoorLeftOpen().onAction(event_info)
        self.assertFalse(value)

    def testOnAction_externalZoneWithNoDoor_returnsFalseAndTimerStarted(self):
        event_info = EventInfo(ZoneEvent.CONTACT_OPEN, self.get_items()[0],
                               Zone.create_external_zone('aZone'), self.zm, pe.get_event_dispatcher())
        value = AlertOnExternalDoorLeftOpen().onAction(event_info)
        self.assertFalse(value)

    def testOnAction_aDoorIsOpen_returnsTrue(self):
        pe.set_switch_state(self.get_items()[0], True)

        event_info = EventInfo(ZoneEvent.CONTACT_OPEN, self.get_items()[0], self.zone1, self.zm,
                               pe.get_event_dispatcher())
        action = AlertOnExternalDoorLeftOpen(0.1)
        value = action.onAction(event_info)

        self.assertTrue(value)
        self.assertTrue(action.has_running_timer())

        time.sleep(0.3)  # wait for the production code timer
        self.assertTrue("door" in self.zm.get_alert_manager()._lastEmailedSubject)

    def testOnAction_aDoorWasOpenButClosedSoonAfter_returnsTrueAndTimerCancelled(self):
        pe.set_switch_state(self.get_items()[0], True)

        event_info = EventInfo(ZoneEvent.CONTACT_OPEN, self.get_items()[0], self.zone1, self.zm,
                               pe.get_event_dispatcher())

        action = AlertOnExternalDoorLeftOpen()
        value = action.onAction(event_info)

        self.assertTrue(value)
        self.assertTrue(action.has_running_timer())

        # simulate door closed
        pe.set_switch_state(self.get_items()[0], False)
        value = action.onAction(event_info)
        self.assertTrue(value)
        self.assertFalse(action.has_running_timer())
