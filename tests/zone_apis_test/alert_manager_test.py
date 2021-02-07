from typing import List

from aaa_modules.alert import Alert
# noinspection PyProtectedMember
from aaa_modules.alert_manager import AlertManager, _get_owner_email_addresses
from aaa_modules.layout_model.devices.activity_times import ActivityTimes, ActivityType
from aaa_modules.layout_model.devices.chromecast_audio_sink import ChromeCastAudioSink
from aaa_modules.layout_model.zone import Zone
from zone_apis_test.layout_model.device_test import DeviceTest, create_zone_manager

SUBJECT = 'This is a test alert'
MODULE = 'a module'


class AlertManagerTest(DeviceTest):
    """ Unit tests for alert_manager. """

    def setUp(self):
        self._cast, items = self.create_audio_sink()
        self.set_items(items)
        super(AlertManagerTest, self).setUp()

        time_map = {
            ActivityType.WAKE_UP: '6 - 9',
            ActivityType.LUNCH: '12:00 - 13:30',
            ActivityType.QUIET: '14:00 - 16:00, 20:00 - 22:59',
            ActivityType.DINNER: '17:50 - 20:00',
            # intentionally no sleep time; otherwise some tests will fail at certain time.
        }
        self._activity_time = ActivityTimes(time_map)

        self._zone = Zone('great room', [self._cast, self._activity_time])
        self._zm = create_zone_manager([self._zone])

        self._properties_file = 'email-addresses.txt'
        self._fixture = AlertManager(self._properties_file)

        self._fixture._set_test_mode(True)

    def tearDown(self):
        super(AlertManagerTest, self).tearDown()
        self._fixture._set_test_mode(False)

    def testProcessAlert_missingAlert_throwsException(self):
        with self.assertRaises(ValueError) as cm:
            # noinspection PyTypeChecker
            self._fixture.process_alert(None)
        self.assertEqual('Invalid alert.', cm.exception.args[0])

    def testProcessAlert_warningAlert_returnsTrue(self):
        alert = Alert.create_warning_alert(SUBJECT)
        result = self._fixture.process_alert(alert, self._zm)
        self.assertTrue(result)

        casts = self._get_all_casts()
        for cast in casts:
            self.assertEqual(SUBJECT, cast.get_last_tts_message())

        self.assertEqual(alert.get_subject(), self._fixture._lastEmailedSubject)

    def testProcessAlert_audioWarningAlert_returnsTrue(self):
        alert = Alert.create_audio_warning_alert(SUBJECT)
        result = self._fixture.process_alert(alert, self._zm)
        self.assertTrue(result)

        casts = self._get_all_casts()
        for cast in casts:
            self.assertEqual(SUBJECT, cast.get_last_tts_message())

        self.assertEqual(None, self._fixture._lastEmailedSubject)

    def testProcessAlert_criticalAlert_returnsTrue(self):
        alert = Alert.create_critical_alert(SUBJECT)
        result = self._fixture.process_alert(alert, self._zm)
        self.assertTrue(result)

        casts = self._get_all_casts()
        for cast in casts:
            self.assertEqual(SUBJECT, cast.get_last_tts_message())

    def testProcessAlert_withinInterval_returnsFalse(self):
        alert = Alert.create_critical_alert(SUBJECT, None, [], MODULE, 1)
        self.assertTrue(self._fixture.process_alert(alert, self._zm))

        # send alert would be ignored due to interval threshold
        self.assertFalse(self._fixture.process_alert(alert, self._zm))

        # but another alert with module would go through
        self.assertTrue(self._fixture.process_alert(Alert.create_critical_alert(SUBJECT), self._zm))

    def testProcessAdminAlert_warningAlert_returnsTrue(self):
        alert = Alert.create_warning_alert(SUBJECT)
        result = self._fixture.process_admin_alert(alert)
        self.assertTrue(result)
        self.assertEqual(alert.get_subject(), self._fixture._lastEmailedSubject)

    def testGetEmailAddresses_noParams_returnsNonEmptyList(self):
        emails = _get_owner_email_addresses(self._properties_file)
        self.assertTrue(len(emails) > 0)

    def _get_all_casts(self) -> List[ChromeCastAudioSink]:
        return [self._cast]
