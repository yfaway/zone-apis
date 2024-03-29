import time
from threading import Timer
from typing import List, Any, Hashable

from zone_api.alert import Alert
from zone_api import platform_encapsulator as pe
from zone_api.core.devices.activity_times import ActivityTimes
from zone_api.core.devices.astro_sensor import AstroSensor
from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink
from zone_api.core.devices.switch import Light


class AlertManager:
    """
    Process an alert.
    The current implementation will send out an email. If the alert is at
    critical level, a TTS message will also be sent to all audio sinks.
    """

    def __init__(self, config: dict[Hashable, Any], test_mode=False):
        """
        Creates a new instance

        :param dict[Hashable, Any] config: the value read from a yaml file via `yaml.safe_load(file)`.
        :param bool test_mode: indicates of this object is in test mode.
        """
        self._owner_email_addresses = None
        self._admin_email_addresses = None

        if config is not None:
            email_config = config['system']['alerts']['email']
            self._owner_email_addresses = email_config['owner-email-addresses']
            self._admin_email_addresses = email_config['admin-email-addresses']

            pe.log_info(f"Owner email addresses " + ", ".join(self._owner_email_addresses))
            pe.log_info(f"Admin email addresses " + ", ".join(self._admin_email_addresses))

        # If set, the TTS message won't be sent to the chrome casts.
        self._testMode = test_mode

        # Used in unit testing to make sure that the email alert function was invoked,
        # without having to sent any actual email.
        self._lastEmailedSubject = None

        # Tracks the timestamp of the last alert in a module.
        self._moduleTimestamps = {}

    @staticmethod
    def new_instance(config: dict[Hashable, Any]):
        """
        Constructs a regular instance.

        :param dict[Hashable, Any] config: the value read from a yaml file via `yaml.safe_load(file)`.
        """

        return AlertManager(config)

    @staticmethod
    def test_instance(config: dict[Hashable, Any]):
        """
        Constructs a test instance whereby no actual email is sent and no sound is played.
        See ``_lastEmailedSubject`` and ``_lastEmailedBody``.

        :param dict[Hashable, Any] config: the value read from a yaml file via `yaml.safe_load(file)`.
        """

        return AlertManager(config, True)

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
            self._email_alert(alert, self._owner_email_addresses)

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

        if alert.is_critical_level():
            self._process_further_actions_for_critical_alert(alert, zone_manager, volume)

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

        self._email_alert(alert, self._admin_email_addresses)

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

    def _email_alert(self, alert, default_email_addresses: List[str]):
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

    # noinspection PyMethodMayBeStatic
    def _process_further_actions_for_critical_alert(self, alert: Alert, zone_manager, volume: int):
        """ Plays the alert message on the speaker two more times in a 30 seconds interval. """
        self._replay_tts_message(alert, zone_manager, volume)
        self._turn_on_lights(alert, zone_manager)

    @staticmethod
    def _replay_tts_message(alert: Alert, zone_manager, volume: int):
        def send_alert():
            if not alert.is_canceled():
                casts: List[ChromeCastAudioSink] = zone_manager.get_devices_by_type(ChromeCastAudioSink)
                for cast in casts:
                    cast.play_message(alert.get_subject(), volume)

        timer1 = Timer(30, send_alert)
        timer1.start()

        timer2 = Timer(60, send_alert)
        timer2.start()

    @staticmethod
    def _turn_on_lights(alert: Alert, zone_manager):
        """
        Turns on all the lights, and register an alert cancellation hook to turn off those lights when the alert is
        canceled.
        """
        astro_sensor: AstroSensor = zone_manager.get_first_device_by_type(AstroSensor)

        if astro_sensor.is_light_on_time():
            lights = [light for light in zone_manager.get_devices_by_type(Light) if not light.is_on()]
            for light in lights:
                light.turn_on(pe.get_event_dispatcher())

            def turn_off_light():
                for light in lights:
                    light.turn_off(pe.get_event_dispatcher())

            alert.add_cancel_hook(turn_off_light)
