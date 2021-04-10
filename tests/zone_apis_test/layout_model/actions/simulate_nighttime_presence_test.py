import time
from threading import Thread

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.actions.simulate_nighttime_presence import SimulateNighttimePresence
from aaa_modules.layout_model.devices.astro_sensor import AstroSensor
from aaa_modules.layout_model.devices.switch import Light
from aaa_modules.layout_model.devices.thermostat import EcobeeThermostat

from aaa_modules.layout_model.event_info import EventInfo
from aaa_modules.layout_model.zone import Zone
from aaa_modules.layout_model.zone_event import ZoneEvent
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager


class SimulateNighttimePresenceTest(DeviceTest):
    """ Unit tests for SimulateNighttimePresence. """

    def setUp(self):
        items = [pe.create_switch_item('_testLight1'),
                 pe.create_switch_item('_testLight2'),
                 pe.create_string_item('_testAstroItem'),
                 pe.create_string_item('_testThermostatName'),
                 pe.create_string_item('_testThermostatState')
                 ]
        self.set_items(items)
        super(SimulateNighttimePresenceTest, self).setUp()

        self.light1_item, self.light2_item, self.astro_item, self.thermostat_name, self.thermostat_state = items

        self.light1 = Light(self.light1_item, 2)
        self.light2 = Light(self.light2_item, 2)
        self.astro = AstroSensor(self.astro_item)
        self.thermostat = EcobeeThermostat(self.thermostat_name, self.thermostat_state)

        self.action = SimulateNighttimePresence(1/60, 3/60)
        self.zone1 = Zone("foyer", [self.light1])
        self.zone2 = Zone("great-room", [self.light2, self.astro, self.thermostat])

        self.izm = create_zone_manager([self.zone1, self.zone2])

    def tearDown(self):
        pe.set_string_value(self.thermostat_state, 'not vacation')
        self.action.cancel_timer()

        super(SimulateNighttimePresenceTest, self).tearDown()

    def testOnAction_lightOnEventButNotInVacation_returnsFalse(self):
        event_info = EventInfo(ZoneEvent.ASTRO_LIGHT_ON, self.astro_item, self.zone2,
                               self.izm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_vacationOnEventButNotInLightOnTime_returnsFalse(self):
        pe.set_string_value(self.thermostat_state, EcobeeThermostat.VACATION_EVENT_TYPE)
        pe.set_string_value(self.astro_item, "DAY")
        event_info = EventInfo(ZoneEvent.VACATION_MODE_ON, self.thermostat_state, self.zone2,
                               self.izm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertFalse(value)

    def testOnAction_vacationOnEvent_returnsTrue(self):
        pe.set_string_value(self.thermostat_state, EcobeeThermostat.VACATION_EVENT_TYPE)
        pe.set_string_value(self.astro_item, "EVENING")

        event_info = EventInfo(ZoneEvent.VACATION_MODE_ON, self.thermostat_state, self.zone2,
                               self.izm, pe.get_event_dispatcher(), self.thermostat)
        self.invoke_and_assert_simulation_running(event_info)

    def testOnAction_lightOnEvent_returnsTrue(self):
        pe.set_string_value(self.thermostat_state, EcobeeThermostat.VACATION_EVENT_TYPE)
        pe.set_string_value(self.astro_item, "EVENING")

        event_info = EventInfo(ZoneEvent.ASTRO_LIGHT_ON, self.astro_item, self.zone2,
                               self.izm, pe.get_event_dispatcher(), self.astro)
        self.invoke_and_assert_simulation_running(event_info)

        #time.sleep(6)  # wait for timer to kick in for multiple iterations
        #self.assertTrue(self.action.iteration_count > 1)
        #self.action.cancel_timer()

    def testOnAction_lightOffEvent_returnsTrue(self):
        pe.set_string_value(self.thermostat_state, EcobeeThermostat.VACATION_EVENT_TYPE)
        pe.set_string_value(self.astro_item, "EVENING")

        # turn on light simulation first
        event_info = EventInfo(ZoneEvent.ASTRO_LIGHT_ON, self.astro_item, self.zone2,
                               self.izm, pe.get_event_dispatcher(), self.astro)
        self.invoke_and_assert_simulation_running(event_info)

        # light off
        event_info = EventInfo(ZoneEvent.ASTRO_LIGHT_OFF, self.astro_item, self.zone2,
                               self.izm, pe.get_event_dispatcher(), self.astro)
        self.invoke_and_assert_simulation_turned_off(event_info)

    def testOnAction_bedTimeEvent_returnsTrue(self):
        pe.set_string_value(self.thermostat_state, EcobeeThermostat.VACATION_EVENT_TYPE)
        pe.set_string_value(self.astro_item, AstroSensor.BED_TIME)

        # turn on light simulation first
        event_info = EventInfo(ZoneEvent.ASTRO_LIGHT_ON, self.astro_item, self.zone2,
                               self.izm, pe.get_event_dispatcher(), self.astro)
        self.invoke_and_assert_simulation_running(event_info)

        # light off
        event_info = EventInfo(ZoneEvent.ASTRO_BED_TIME, self.astro_item, self.zone2,
                               self.izm, pe.get_event_dispatcher(), self.astro)
        self.invoke_and_assert_simulation_turned_off(event_info)

    def testOnAction_vacationModeOffEvent_returnsTrue(self):
        pe.set_string_value(self.thermostat_state, EcobeeThermostat.VACATION_EVENT_TYPE)
        pe.set_string_value(self.astro_item, "EVENING")

        # turn on light simulation first
        event_info = EventInfo(ZoneEvent.ASTRO_LIGHT_ON, self.astro_item, self.zone2,
                               self.izm, pe.get_event_dispatcher(), self.astro)
        self.invoke_and_assert_simulation_running(event_info)

        # light off
        event_info = EventInfo(ZoneEvent.VACATION_MODE_OFF, self.thermostat_state, self.zone2,
                               self.izm, pe.get_event_dispatcher(), self.thermostat)
        self.invoke_and_assert_simulation_turned_off(event_info)

    def invoke_and_assert_simulation_running(self, event_info):
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.light1.is_on() or self.light2.is_on())

    def invoke_and_assert_simulation_turned_off(self, event_info):
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(not self.light1.is_on() and not self.light2.is_on())
        self.assertTrue(self.action.timer is None)
