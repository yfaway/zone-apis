import time

from zone_api.alert_manager import AlertManager
from zone_api import platform_encapsulator as pe

from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.contact import Door
from zone_api_test.core.device_test import DeviceTest, create_zone_manager

from zone_api.core.actions.alert_on_external_door_left_open import AlertOnExternalDoorLeftOpen


class AlertOnExternalDoorLeftOpenTest(DeviceTest):
    """ Unit tests for alert_on_external_door_left_open.py. """

    def setUp(self):
        items = [pe.create_switch_item('Door1'), pe.create_switch_item('Door2')]

        self.set_items(items)
        super(AlertOnExternalDoorLeftOpenTest, self).setUp()

        self.action = AlertOnExternalDoorLeftOpen()
        self.zone1 = Zone.create_external_zone('porch').add_device(Door(items[0]))
        self.zone2 = Zone.create_external_zone('garage').add_device(Door(items[1]))
        self.alertManager = AlertManager()

        self.zm = create_zone_manager([self.zone1, self.zone2])

    def testOnAction_notAnExternalZone_returnsFalse(self):
        event_info = EventInfo(ZoneEvent.DOOR_OPEN,self.get_items()[0],
                               Zone('innerZone').add_action(self.action), self.zm,
                               pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_externalZoneWithNoDoor_returnsFalseAndTimerStarted(self):
        event_info = EventInfo(ZoneEvent.DOOR_OPEN, self.get_items()[0],
                               Zone.create_external_zone('aZone').add_action(self.action),
                               self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_aDoorIsOpen_returnsTrue(self):
        pe.set_switch_state(self.get_items()[0], True)

        self.action = AlertOnExternalDoorLeftOpen(0.1)
        self.zone1 = self.zone1.add_action(self.action)
        event_info = EventInfo(ZoneEvent.DOOR_OPEN, self.get_items()[0], self.zone1, self.zm,
                               pe.get_event_dispatcher())
        value = self.action.on_action(event_info)

        self.assertTrue(value)
        self.assertTrue(self.action.has_running_timer())

        time.sleep(0.3)  # wait for the production code timer
        self.assertTrue("door" in self.zm.get_alert_manager()._lastEmailedSubject)

    def testOnAction_aDoorWasOpenButClosedSoonAfter_returnsTrueAndTimerCancelled(self):
        pe.set_switch_state(self.get_items()[0], True)

        self.zone1 = self.zone1.add_action(self.action)
        event_info = EventInfo(ZoneEvent.DOOR_OPEN, self.get_items()[0], self.zone1, self.zm,
                               pe.get_event_dispatcher())

        value = self.action.on_action(event_info)

        self.assertTrue(value)
        self.assertTrue(self.action.has_running_timer())

        # simulate door closed
        pe.set_switch_state(self.get_items()[0], False)
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertFalse(self.action.has_running_timer())
