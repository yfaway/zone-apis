import time
from typing import List

from zone_api.alert import Alert
from zone_api import platform_encapsulator as pe
from zone_api.core.devices.activity_times import ActivityTimes
from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink

_ADMIN_EMAIL_KEY = 'admin-email-address'
_OWNER_EMAIL_KEY = 'owner-email-address'


class AlertManager:
    """
    Process an alert.
    The current implementation will send out an email. If the alert is at
    critical level, a TTS message will also be sent to all audio sinks.
    """

    def __init__(self, properties_file='/etc/openhab/transform/owner-email-addresses.map'):
        self._properties_file = properties_file

        # If set, the TTS message won't be sent to the chrome casts.
        self._testMode = False

        # Used in unit testing to make sure that the email alert function was invoked,
        # without having to sent any actual email.
        self._lastEmailedSubject = None

        # Tracks the timestamp of the last alert in a module.
        self._moduleTimestamps = {}

    def process_alert(self, alert: Alert, zone_manager=None):
        """
        Processes the provided alert.
        If the alert's level is WARNING or CRITICAL, the TTS subject will be played
        on the ChromeCasts.

        :param Alert alert: the alert to be processed
        :param ImmutableZoneManager zone_manager: used to retrieve the ActivityTimes
        :return: True if alert was processed; False otherwise.
        :raise: ValueError if alert is None
        """

        if alert is None:
            raise ValueError('Invalid alert.')

        pe.log_info(f"Processing alert\n{str(alert)}")

        if self._is_throttled(alert):
            return False

        if not alert.is_audio_alert_only():
            self._email_alert(alert, _get_owner_email_addresses(self._properties_file))

        # Play an audio message if the alert is warning or critical.
        # Determine the volume based on the current zone activity.
        volume = 0
        if alert.is_critical_level():
            volume = 60
        elif alert.is_warning_level():
            if zone_manager is None:
                volume = 60
            else:
                activities = zone_manager.get_devices_by_type(ActivityTimes)
                if len(activities) > 0:
                    activity = activities[0]
                    if activity.is_sleep_time():
                        volume = 0
                    elif activity.is_quiet_time():
                        volume = 40
                    else:
                        volume = 60
                else:
                    volume = 50

        if volume > 0:
            casts: List[ChromeCastAudioSink] = zone_manager.get_devices_by_type(ChromeCastAudioSink)
            for cast in casts:
                cast.play_message(alert.get_subject(), volume)

        return True

    def process_admin_alert(self, alert):
        """
        Processes the provided alert by sending an email to the administrator.

        :param Alert alert: the alert to be processed
        :return: True if alert was processed; False otherwise.
        :raise: ValueError if alert is None
        """

        if alert is None:
            raise ValueError('Invalid alert.')

        pe.log_info(f"Processing admin alert\n{str(alert)}")

        if self._is_throttled(alert):
            return False

        self._email_alert(alert, _get_admin_email_addresses(self._properties_file))

        return True

    def reset(self):
        """
        Reset the internal states of this class.
        """
        self._lastEmailedSubject = None
        self._moduleTimestamps = {}

    def _is_throttled(self, alert):
        if alert.get_module() is not None:
            interval_in_seconds = alert.get_interval_between_alerts_in_minutes() * 60

            if alert.get_module() in self._moduleTimestamps:
                previous_time = self._moduleTimestamps[alert.get_module()]
                if (time.time() - previous_time) < interval_in_seconds:
                    return True

            self._moduleTimestamps[alert.get_module()] = time.time()

        return False

    def _email_alert(self, alert, default_email_addresses):
        email_addresses = alert.get_email_addresses()
        if not email_addresses:
            email_addresses = default_email_addresses

        if email_addresses is None or len(email_addresses) == 0:
            raise ValueError('Missing email addresses.')

        if not self._testMode:
            body = '' if alert.get_body() is None else alert.get_body()
            pe.send_email(email_addresses, alert.get_subject(), body, alert.get_attachment_urls())

        self._lastEmailedSubject = alert.get_subject()
        self._lastEmailedBody = alert.get_body()

    def _set_test_mode(self, mode):
        """
        Switches on/off the test mode.
        @param mode boolean
        """
        self._testMode = mode


def _load_properties(filepath, sep='=', comment_char='#'):
    """
    Read the file passed as parameter as a properties file.
    @see https://stackoverflow.com/a/31852401
    """

    props = {}
    with open(filepath, "rt") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith(comment_char):
                key_value = line.split(sep)
                key = key_value[0].strip()
                value = sep.join(key_value[1:]).strip().strip('"')
                props[key] = value
    return props


def _get_owner_email_addresses(file_name: str):
    """
    :return: list of user email addresses
    """
    props = _load_properties(file_name)
    emails = props[_OWNER_EMAIL_KEY].split(';')

    return emails


def _get_admin_email_addresses(file_name: str):
    """
    :return: list of administrator email addresses
    """
    props = _load_properties(file_name)
    emails = props[_ADMIN_EMAIL_KEY].split(';')

    return emails
