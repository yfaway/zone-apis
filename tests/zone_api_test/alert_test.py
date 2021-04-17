import unittest

from zone_api.alert import Alert

SUBJECT = "a subject"
BODY = 'a body\n line2'
MODULE = 'a module'
INTERVAL_BETWEEN_ALERTS_IN_MINUTES = 5
EMAIL_ADDRESSES = 'asdf@here.com'


class AlertTest(unittest.TestCase):
    def testCreateInfoAlert_withSubject_returnsNewObject(self):
        alert = Alert.create_info_alert(SUBJECT)
        self.assertEqual(SUBJECT, alert.get_subject())
        self.assertEqual(None, alert.get_body())
        self.assertEqual(0, len(alert.get_attachment_urls()))
        self.assertEqual(None, alert.get_module())
        self.assertEqual([], alert.get_email_addresses())
        self.assertEqual(-1, alert.get_interval_between_alerts_in_minutes())
        self.assertTrue(alert.is_info_level())

    def testCreateWarningAlert_withSubject_returnsNewObject(self):
        alert = Alert.create_warning_alert(SUBJECT)
        self.assertEqual(SUBJECT, alert.get_subject())
        self.assertEqual(None, alert.get_body())
        self.assertEqual(0, len(alert.get_attachment_urls()))
        self.assertEqual(None, alert.get_module())
        self.assertEqual(-1, alert.get_interval_between_alerts_in_minutes())
        self.assertTrue(alert.is_warning_level())

    def testCreateCriticalAlert_withSubjectAndBody_returnsNewObject(self):
        alert = Alert.create_critical_alert(SUBJECT, BODY)
        self.assertEqual(SUBJECT, alert.get_subject())
        self.assertEqual(BODY, alert.get_body())
        self.assertEqual(0, len(alert.get_attachment_urls()))
        self.assertTrue(alert.is_critical_level())

    def testFromJson_missingSubject_raiseException(self):
        json = '{' + '"body":"{}","level":"blah"'.format(SUBJECT, BODY) + '}'
        with self.assertRaises(ValueError) as cm:
            Alert.from_json(json)
        self.assertEqual('Missing subject value.', cm.exception.args[0])

    def testFromJson_withSubject_returnsNewObject(self):
        json = '{"subject":"' + SUBJECT + '"}'
        alert = Alert.from_json(json)

        self.assertEqual(SUBJECT, alert.get_subject())
        self.assertEqual(None, alert.get_body())
        self.assertTrue(alert.is_info_level())

    def testFromJson_withSubjectAndEmailAddresses_returnsNewObject(self):
        json = '{' + '"subject":"{}","emailAddresses":"{}"'.format(
            SUBJECT, EMAIL_ADDRESSES) + '}'
        alert = Alert.from_json(json)

        self.assertEqual(SUBJECT, alert.get_subject())
        self.assertEqual(1, len(alert.get_email_addresses()))
        self.assertEqual(EMAIL_ADDRESSES, alert.get_email_addresses()[0])
        self.assertEqual(None, alert.get_body())
        self.assertTrue(alert.is_info_level())

    def testFromJson_withSubjectAndBody_returnsNewObject(self):
        json = '{' + '"subject":"{}","body":"{}"'.format(SUBJECT, BODY) + '}'
        alert = Alert.from_json(json)

        self.assertEqual(SUBJECT, alert.get_subject())
        self.assertEqual(BODY, alert.get_body())
        self.assertTrue(alert.is_info_level())

    def testFromJson_withSubjectBodyAndLevel_returnsNewObject(self):
        json = '{' + '"subject":"{}","body":"{}","level":"warning"'.format(SUBJECT, BODY) + '}'
        alert = Alert.from_json(json)

        self.assertEqual(SUBJECT, alert.get_subject())
        self.assertEqual(BODY, alert.get_body())
        self.assertTrue(alert.is_warning_level())

    def testFromJson_invalidLevel_raiseException(self):
        json = '{' + '"subject":"{}","body":"{}","level":"blah"'.format(SUBJECT, BODY) + '}'
        with self.assertRaises(ValueError):
            Alert.from_json(json)

    def testFromJson_withSubjectBodyAndModule_returnsNewObject(self):
        json = '{' + '"subject":"{}","body":"{}","module":"{}","intervalBetweenAlertsInMinutes":{}'.format(
            SUBJECT, BODY, MODULE, INTERVAL_BETWEEN_ALERTS_IN_MINUTES) + '}'
        alert = Alert.from_json(json)

        self.assertEqual(SUBJECT, alert.get_subject())
        self.assertEqual(BODY, alert.get_body())
        self.assertEqual(MODULE, alert.get_module())
        self.assertEqual(INTERVAL_BETWEEN_ALERTS_IN_MINUTES, alert.get_interval_between_alerts_in_minutes())
        self.assertTrue(alert.is_info_level())

    def testFromJson_missingIntervalBetweenAlertsInMinutes_returnsNewObject(self):
        json = '{' + '"subject":"{}","body":"{}","module":"{}"'.format(
            SUBJECT, BODY, MODULE) + '}'
        with self.assertRaises(ValueError) as cm:
            Alert.from_json(json)
        self.assertEqual('Invalid interval_between_alerts_in_minutes value: -1', cm.exception.args[0])
