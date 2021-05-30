from zone_api.alert import Alert
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.environment_canada import EnvCanada
from zone_api import platform_encapsulator as pe
from zone_api.core.action import action


@action(events=[ZoneEvent.TIMER], devices=[], zone_name_pattern='.*Virtual.*')
class AlertOnRainOrSnowDuringTheDay:
    def __init__(self, city: str = 'Ottawa'):
        self._city = city

    def on_startup(self, event_info: EventInfo):

        # start timer here. Main logic remains in on_action.
        def timer_handler():
            self.on_action(self.create_timer_event_info(event_info))

        weekday_time = '06:15'
        weekend_time = '08:00'

        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every().monday.at(weekday_time).do(timer_handler)
        scheduler.every().tuesday.at(weekday_time).do(timer_handler)
        scheduler.every().wednesday.at(weekday_time).do(timer_handler)
        scheduler.every().thursday.at(weekday_time).do(timer_handler)
        scheduler.every().friday.at(weekday_time).do(timer_handler)

        scheduler.every().saturday.at(weekend_time).do(timer_handler)
        scheduler.every().sunday.at(weekend_time).do(timer_handler)

    def on_action(self, event_info: EventInfo):
        forecasts = EnvCanada.retrieve_hourly_forecast(self._city, 12)
        rain_periods = [f for f in forecasts if
                        'High' == f.get_precipitation_probability() or
                        'Medium' == f.get_precipitation_probability()]
        if len(rain_periods) > 0:
            if len(rain_periods) == 1:
                subject = u"Possible precipitation at {}".format(
                    rain_periods[0].get_user_friendly_forecast_time())
            else:
                subject = u"Possible precipitation from {} to {}".format(
                    rain_periods[0].get_user_friendly_forecast_time(),
                    rain_periods[-1].get_user_friendly_forecast_time())

            body = u'Forecasts:\n'
            body += u"{:5} {:7} {:25} {:6} {:6}\n".format('Hour: ', 'Celsius',
                                                          'Condition', 'Prob.', 'Wind')
            for f in forecasts:
                body += str(f) + '\n'

            alert_message = Alert.create_info_alert(subject, body)
            zm = event_info.get_zone_manager()
            result = zm.get_alert_manager().process_alert(alert_message, zm)
            if not result:
                pe.log_info('Failed to send rain/snow alert')

            return True
        else:
            pe.log_info('There is no rain/snow today.')
            return False
