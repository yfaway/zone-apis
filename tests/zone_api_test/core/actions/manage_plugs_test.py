from zone_api import platform_encapsulator as pe
from zone_api.core.actions.manage_plugs import ManagePlugs
from zone_api.core.devices.activity_times import ActivityTimes, ActivityType
from zone_api.core.devices.plug import Plug

from zone_api.core.event_info import EventInfo
from zone_api.core.zone import Zone
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class ManagePlugsTest(DeviceTest):
    """ Unit tests for ManagePlugs. """

    def setUp(self):
        items = [pe.create_switch_item('AlarmStatus'), pe.create_number_item('_AlarmMode'),
                 pe.create_switch_item('_Motion1'),
                 pe.create_switch_item('_Plug1'),
                 ]
        self.set_items(items)
        super(ManagePlugsTest, self).setUp()

        self.alarmPartition = AlarmPartition(items[0], items[1])
        self.motionSensor = MotionSensor(items[2])
        self.plug = Plug(items[3])
        self.always_on_plug2 = Plug(items[3])

    def testOnAction_motionTriggeredInWakeupTimePeriod_turnOn(self):
        self.plug.turn_off(pe.get_event_dispatcher())

        self.zm = self._setup_zone_manager({ActivityType.WAKE_UP: '0:00 - 23:59', })

        event_info = EventInfo(ZoneEvent.MOTION, self.motionSensor.get_item(),
                               self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.plug.is_on())

    def testOnAction_motionTriggeredNotInWakeupTimePeriod_notTurnOn(self):
        self.plug.turn_off(pe.get_event_dispatcher())

        self.zm = self._setup_zone_manager({ActivityType.WAKE_UP: '4:00 - 5:00', })

        event_info = EventInfo(ZoneEvent.MOTION, self.motionSensor.get_item(),
                               self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertFalse(self.plug.is_on())

    def testOnAction_timerTriggeredInRightPeriod_turnsOffPlugs(self):
        self.plug.turn_on(pe.get_event_dispatcher())
        self.zm = self._setup_zone_manager({ActivityType.TURN_OFF_PLUGS: '0:00 - 23:59', })

        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertFalse(self.plug.is_on())

    def testOnAction_timerTriggeredInRightPeriod_notTurningOffAlwaysOnPlugs(self):
        self.plug = Plug(self.plug.get_item(), None, True)
        self.plug.turn_on(pe.get_event_dispatcher())
        self.zm = self._setup_zone_manager({ActivityType.TURN_OFF_PLUGS: '0:00 - 23:59', })

        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.plug.is_on())

    def testOnAction_timerTriggeredNotInRightPeriod_armStay(self):
        self.plug.turn_on(pe.get_event_dispatcher())
        self.zm = self._setup_zone_manager({ActivityType.TURN_OFF_PLUGS: self.create_outside_time_range()})

        event_info = EventInfo(ZoneEvent.TIMER, None,
                               self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.plug.is_on())

    def testOnAction_armedAway_turnOff(self):
        self.plug.turn_on(pe.get_event_dispatcher())

        self.zm = self._setup_zone_manager({ActivityType.WAKE_UP: '0:00 - 23:59', })

        event_info = EventInfo(ZoneEvent.PARTITION_ARMED_AWAY, self.alarmPartition.get_item(),
                               self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertFalse(self.plug.is_on())

    def testOnAction_armedAway_notTurningOffAlwaysOnPlug(self):
        self.plug = Plug(self.plug.get_item(), None, True)
        self.plug.turn_on(pe.get_event_dispatcher())

        self.zm = self._setup_zone_manager({ActivityType.WAKE_UP: '0:00 - 23:59', })

        event_info = EventInfo(ZoneEvent.PARTITION_ARMED_AWAY, self.alarmPartition.get_item(),
                               self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.plug.is_on())

    def testOnAction_disarmedNotInTurnOffPeriod_turnOff(self):
        self.zm = self._setup_zone_manager({ActivityType.TURN_OFF_PLUGS: self.create_outside_time_range()})

        event_info = EventInfo(ZoneEvent.PARTITION_DISARMED_FROM_AWAY, self.alarmPartition.get_item(),
                               self.zone1, self.zm, pe.get_event_dispatcher())
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertTrue(self.plug.is_on())

    def testOnAction_disarmedInTurnOffPeriod_turnOff(self):
        self.zm = self._setup_zone_manager({ActivityType.TURN_OFF_PLUGS: '0 - 23:59'})

        event_info = EventInfo(ZoneEvent.PARTITION_DISARMED_FROM_AWAY, self.alarmPartition.get_item(),
                               self.zone1, self.zm, pe.get_event_dispatcher(), self.zone1, self.alarmPartition)
        value = self.action.on_action(event_info)
        self.assertTrue(value)
        self.assertFalse(self.plug.is_on())

    def _setup_zone_manager(self, time_map):
        self.activity_times = ActivityTimes(time_map)

        self.action = ManagePlugs()
        self.zone1 = Zone('foyer', [self.plug, self.motionSensor, self.alarmPartition, self.activity_times]) \
            .add_action(self.action)

        return create_zone_manager([self.zone1])
