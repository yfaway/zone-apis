from typing import Union, Tuple

import feedparser
from zone_api import platform_encapsulator as pe
from zone_api.alert import Alert
from zone_api.core.devices.weather import Weather
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.environment_canada import EnvCanada
from zone_api.core.action import action


@action(events=[ZoneEvent.TIMER], devices=[Weather])
class SendWeatherAlert:
    """
    Periodically check the Alert RSS feed from Environment Canada. If the feed has changed, retrieve the details of
    the alert, and proceed with the notification.
    """

    def __init__(self, alert_rss_url: str = 'https://weather.gc.ca/rss/battleboard/on41_e.xml',
                 feed_refresh_interval_in_minutes: int = 5):
        self._alert_rss_url = alert_rss_url
        self._feed_refresh_interval_in_minutes = feed_refresh_interval_in_minutes

    def on_startup(self, event_info: EventInfo):

        def handler():
            self.on_action(self.create_timer_event_info(event_info))

        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every(self._feed_refresh_interval_in_minutes).minutes.do(handler)

    def on_action(self, event_info: EventInfo):
        zone_manager = event_info.get_zone_manager()
        weather: Weather = zone_manager.get_first_device_by_type(Weather)

        has_alert, alert_url = self._has_new_alert(weather)

        if has_alert:
            alert_message, url, _ = EnvCanada.retrieve_alert(alert_url)

            if alert_message is not None:
                subject = f"[Weather Alert] {weather.get_alert_title()}"
                body = f"{alert_message}\nLink: {url}"

                alert = Alert.create_info_alert(subject, body)
                zone_manager.get_alert_manager().process_alert(alert, zone_manager)

                return True
            else:
                self.log_debug("No weather alert exists.")
                return False
        else:
            self.log_error("Feed doesn't contain any entries.")
            return False

    def _has_new_alert(self, weather: Weather) -> Union[Tuple[bool, str], Tuple[bool, None]]:
        """
        :return: a tuple containing the boolean value indicating if there is an alert. If yes, the second value
            contains the alert URL (to fetch the details).
        """

        # retrieve the alert title from the feed
        feed = feedparser.parse(self._alert_rss_url)
        if len(feed.entries) == 0:
            self.log_error("Expect at least one weather alert entry.")
            return False, None

        # Env Canada might have multiple entries; only one of which represents the actual alert.
        for entry in feed.entries:
            if EnvCanada.is_alert_url(entry.link):
                alert_title = entry.title
                # alert_date = entry.published_parsed

                if alert_title != weather.get_alert_title():
                    # noinspection PyProtectedMember
                    weather._set_alert_title(alert_title)
                    return True, entry.link
                else:
                    return False, None

        return False, None
