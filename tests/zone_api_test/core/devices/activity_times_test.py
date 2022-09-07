import time
import datetime

from zone_api_test.core.device_test import DeviceTest
from zone_api.core.devices.activity_times import ActivityTimes, ActivityType


class ActivityTimesTest(DeviceTest):
    """ Unit tests for ActivityTimes. """

    def setUp(self):
        self.set_items([])
        super(ActivityTimesTest, self).setUp()

        time_map = {
            ActivityType.WAKE_UP: '6 - 9',
            ActivityType.LUNCH: '12:00 - 13:30',
            ActivityType.QUIET: '14:00 - 16:00, 20:00 - 22:59',
            ActivityType.DINNER: '17:50 - 20:00',
            ActivityType.SLEEP: '23:00 - 7:00'
        }
        self.activity = ActivityTimes(time_map)

    def testCtor_invalidKey_throwsError(self):
        with self.assertRaises(TypeError):
            ActivityTimes({'invalidKey': '8:00 - 9:00'})

    def testAtActivityType_wakeupTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 7, 10)
        self.assertTrue(self.activity.is_at_activity_time(ActivityType.WAKE_UP, time.mktime(dt.timetuple())))

    def testIsWakeupTime_wakeupTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 7, 10)
        self.assertTrue(self.activity.is_wakeup_time(time.mktime(dt.timetuple())))

    def testIsWakeupTime_notLunchTime_returnsFalse(self):
        dt = datetime.datetime(2020, 2, 8, 10, 00)
        self.assertFalse(self.activity.is_wakeup_time(time.mktime(dt.timetuple())))

    def testAtActivityType_notLunchTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 10, 00)
        self.assertFalse(self.activity.is_at_activity_time(ActivityType.LUNCH, time.mktime(dt.timetuple())))

    def testIsLunchTime_lunchTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 12, 10)
        self.assertTrue(self.activity.is_lunch_time(time.mktime(dt.timetuple())))

    def testIsLunchTime_notLunchTime_returnsFalse(self):
        dt = datetime.datetime(2020, 2, 8, 1, 00)
        self.assertFalse(self.activity.is_lunch_time(time.mktime(dt.timetuple())))

    def testIsQuietTime_rightTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 15, 00)
        self.assertTrue(self.activity.is_quiet_time(time.mktime(dt.timetuple())))

    def testAtActivityType_validQuietTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 15, 00)
        self.assertTrue(self.activity.is_at_activity_time(ActivityType.QUIET, time.mktime(dt.timetuple())))

    def testIsQuietTime_wrongTime_returnsFalse(self):
        dt = datetime.datetime(2020, 2, 8, 10, 00)
        self.assertFalse(self.activity.is_quiet_time(time.mktime(dt.timetuple())))

    def testIsDinnerTime_rightTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 19, 00)
        self.assertTrue(self.activity.is_dinner_time(time.mktime(dt.timetuple())))

    def testIsDinnerTime_wrongTime_returnsFalse(self):
        dt = datetime.datetime(2020, 2, 8, 10, 00)
        self.assertFalse(self.activity.is_dinner_time(time.mktime(dt.timetuple())))

    def testIsSleepTime_rightTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 2, 00)
        self.assertTrue(self.activity.is_sleep_time(time.mktime(dt.timetuple())))

    def testIsSleepTime_wrongTime_returnsFalse(self):
        dt = datetime.datetime(2020, 2, 8, 10, 00)
        self.assertFalse(self.activity.is_sleep_time(time.mktime(dt.timetuple())))

    def testAtActivityType_invalidType_returnsTrue(self):
        with self.assertRaises(ValueError) as cm:
            # noinspection PyTypeChecker
            self.assertTrue(self.activity.is_at_activity_time(None))
        self.assertEqual("Invalid activity type None", cm.exception.args[0])
