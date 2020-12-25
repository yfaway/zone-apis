from enum import Enum, unique
import json


@unique
class AlertLevel(Enum):
    """
    The alert levels.
    """

    INFO = 1
    """ INFO """

    WARNING = 2
    """ WARNING """

    CRITICAL = 3
    """ CRITICAL """


class Alert:
    """
    Contains information about the alert.
    """

    @classmethod
    def create_info_alert(cls, subject, body=None, attachment_urls=None,
                          module=None, interval_between_alerts_in_minutes=-1):
        """
        Creates an INFO alert.

        :param body: 
        :param string subject:
        :param list(str) attachment_urls: list of URL attachment strings:
        :param string module: (optional)
        :param int interval_between_alerts_in_minutes: (optional)
        """
        if attachment_urls is None:
            attachment_urls = []
        return cls(AlertLevel.INFO, subject, body, attachment_urls, module,
                   interval_between_alerts_in_minutes)

    @classmethod
    def create_warning_alert(cls, subject, body=None, attachment_urls=None,
                             module=None, interval_between_alerts_in_minutes=-1):
        """
        Creates a WARNING alert.

        :param body:
        :param string subject:
        :param list(str) attachment_urls: list of URL attachment strings:
        :param string module: (optional)
        :param int interval_between_alerts_in_minutes: (optional)
        """
        if attachment_urls is None:
            attachment_urls = []
        return cls(AlertLevel.WARNING, subject, body, attachment_urls, module,
                   interval_between_alerts_in_minutes)

    @classmethod
    def create_audio_warning_alert(cls, subject, body=None, attachment_urls=None,
                                   module=None, interval_between_alerts_in_minutes=-1):
        """
        Creates an audio-only WARNING alert.

        :param body:
        :param string subject:
        :param list(str) attachment_urls: list of URL attachment strings:
        :param string module: (optional)
        :param int interval_between_alerts_in_minutes: (optional)
        """
        if attachment_urls is None:
            attachment_urls = []
        return cls(AlertLevel.WARNING, subject, body, attachment_urls, module,
                   interval_between_alerts_in_minutes, [], True)

    @classmethod
    def create_critical_alert(cls, subject, body=None, attachment_urls=None,
                              module=None, interval_between_alerts_in_minutes=-1):
        """
        Creates a CRITICAL alert.

        :param body:
        :param string subject:
        :param list(str) attachment_urls: list of URL attachment strings:
        :param string module: (optional)
        :param int interval_between_alerts_in_minutes: (optional)
        """
        if attachment_urls is None:
            attachment_urls = []
        return cls(AlertLevel.CRITICAL, subject, body, attachment_urls, module,
                   interval_between_alerts_in_minutes)

    @classmethod
    def from_json(cls, json_string):
        """
        Creates a new object from information in the json string. This method
        is used for alerts coming in from outside the jsr223 framework; they 
        will be in JSON format.
        Accepted keys: subject, body, level ('info', 'warning', or 'critical').

        :param str json_string:
        :raise: ValueError if jsonString contains invalid values
        """

        # set strict to false to allow control characters in the json string
        obj = json.loads(json_string, strict=False)

        subject = obj.get('subject', None)
        if subject is None or '' == subject:
            raise ValueError('Missing subject value.')

        body = obj.get('body', None)

        level_mappings = {
            'info': AlertLevel.INFO,
            'warning': AlertLevel.WARNING,
            'critical': AlertLevel.CRITICAL
        }
        level = AlertLevel.INFO
        if 'level' in obj:
            level = level_mappings.get(obj['level'], None)

        if level is None:
            raise ValueError('Invalid alert level.')

        module = obj.get('module', None)
        if '' == module:
            module = None

        interval_between_alerts_in_minutes = obj.get(
            'intervalBetweenAlertsInMinutes', -1)
        if module is not None and interval_between_alerts_in_minutes <= 0:
            raise ValueError(f'Invalid interval_between_alerts_in_minutes value: {interval_between_alerts_in_minutes}')

        attachment_urls = []

        email_addresses = obj.get('emailAddresses', None)
        return cls(level, subject, body, attachment_urls, module,
                   interval_between_alerts_in_minutes, email_addresses)

    def __init__(self, level, subject, body=None, attachment_urls=None,
                 module=None, interval_between_alerts_in_minutes=-1,
                 email_addresses=None,
                 audio_alert_only=False):
        if attachment_urls is None:
            attachment_urls = []
        self.level = level
        self.subject = subject
        self.body = body
        self.attachment_urls = attachment_urls
        self.module = module
        self.interval_between_alerts_in_minutes = interval_between_alerts_in_minutes
        self.emailAddresses = email_addresses
        self.audioAlertOnly = audio_alert_only

    def get_subject(self):
        """
        :rtype: str
        """
        return self.subject

    def get_body(self):
        """
        :rtype: str
        """
        return self.body

    def get_attachment_urls(self):
        """
        :rtype: list(str)
        """
        return self.attachment_urls

    def get_module(self):
        """
        Returns the alert module

        :rtype: str
        """
        return self.module

    def get_email_addresses(self):
        """
        Returns the overriding email addresses to be used instead of the default
        email addresses.

        :return: a list of email addresses; empty list if not specified
        :rtype: list(str)
        """

        return [] if self.emailAddresses is None else self.emailAddresses.split(';')

    def get_interval_between_alerts_in_minutes(self):
        """
        :rtype: int
        """
        return self.interval_between_alerts_in_minutes

    def is_info_level(self):
        """
        :rtype: bool
        """
        return AlertLevel.INFO == self.level

    def is_warning_level(self):
        """
        :rtype: bool
        """
        return AlertLevel.WARNING == self.level

    def is_critical_level(self):
        """
        :rtype: bool
        """
        return AlertLevel.CRITICAL == self.level

    def is_audio_alert_only(self):
        """
        :rtype: bool
        """
        return self.audioAlertOnly

    def __str__(self):
        """
        :return: a user readable string containing this object's info.
        """

        return f'[{self.level.name}] {self.get_subject()}\n{self.get_body()}\n{str(self.get_attachment_urls())}'
