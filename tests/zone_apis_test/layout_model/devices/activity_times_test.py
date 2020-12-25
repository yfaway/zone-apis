import time
import datetime

from zone_apis_test.layout_model.device_test import DeviceTest
from aaa_modules.layout_model.devices.activity_times import ActivityTimes


class ActivityTimesTest(DeviceTest):
    """ Unit tests for ActivityTimes. """

    def setUp(self):
        self.set_items([])
        super(ActivityTimesTest, self).setUp()

        time_map = {
            'wakeup': '6 - 9',
            'lunch': '12:00 - 13:30',
            'quiet': '14:00 - 16:00, 20:00 - 22:59',
            'dinner': '17:50 - 20:00',
            'sleep': '23:00 - 7:00'
        }
        self.activity = ActivityTimes(time_map)

    def testCtor_invalidKey_throwsError(self):
        with self.assertRaises(ValueError) as cm:
            ActivityTimes({'invalidKey': '8:00 - 9:00'})

        self.assertEqual('Invalid time range key invalidKey', cm.exception.args[0])

    def testIsWakeupTime_lunchTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 7, 10)
        self.assertTrue(self.activity.isWakeupTime(time.mktime(dt.timetuple())))

    def testIsWakeupTime_notLunchTime_returnsFalse(self):
        dt = datetime.datetime(2020, 2, 8, 10, 00)
        self.assertFalse(self.activity.isWakeupTime(time.mktime(dt.timetuple())))

    def testIsLunchTime_lunchTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 12, 10)
        self.assertTrue(self.activity.isLunchTime(time.mktime(dt.timetuple())))

    def testIsLunchTime_notLunchTime_returnsFalse(self):
        dt = datetime.datetime(2020, 2, 8, 1, 00)
        self.assertFalse(self.activity.isLunchTime(time.mktime(dt.timetuple())))

    def testIsQuietTime_rightTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 15, 00)
        self.assertTrue(self.activity.isQuietTime(time.mktime(dt.timetuple())))

    def testIsQuietTime_wrongTime_returnsFalse(self):
        dt = datetime.datetime(2020, 2, 8, 10, 00)
        self.assertFalse(self.activity.isQuietTime(time.mktime(dt.timetuple())))

    def testIsDinnerTime_rightTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 19, 00)
        self.assertTrue(self.activity.isDinnerTime(time.mktime(dt.timetuple())))

    def testIsDinnerTime_wrongTime_returnsFalse(self):
        dt = datetime.datetime(2020, 2, 8, 10, 00)
        self.assertFalse(self.activity.isDinnerTime(time.mktime(dt.timetuple())))

    def testIsSleepTime_rightTime_returnsTrue(self):
        dt = datetime.datetime(2020, 2, 8, 2, 00)
        self.assertTrue(self.activity.isSleepTime(time.mktime(dt.timetuple())))

    def testIsSleepTime_wrongTime_returnsFalse(self):
        dt = datetime.datetime(2020, 2, 8, 10, 00)
        self.assertFalse(self.activity.isSleepTime(time.mktime(dt.timetuple())))
