import datetime

import HABApp

from aaa_modules.alert import Alert
from aaa_modules.environment_canada import EnvCanada
from aaa_modules import platform_encapsulator as pe


class AlertRainOrSnowDuringTheDay(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.run_on_workdays(datetime.time(6, 15), self.alert)
        self.run_on_weekends(datetime.time(8), self.alert)

    # noinspection PyMethodMayBeStatic
    def alert(self):
        forecasts = EnvCanada.retrieve_hourly_forecast('Ottawa', 12)
        rain_periods = [f for f in forecasts if
                        'High' == f.getPrecipationProbability() or
                        'Medium' == f.getPrecipationProbability()]
        if len(rain_periods) > 0:
            if len(rain_periods) == 1:
                subject = u"Possible precipitation at {}".format(
                    rain_periods[0].getUserFriendlyForecastTime())
            else:
                subject = u"Possible precipitation from {} to {}".format(
                    rain_periods[0].getUserFriendlyForecastTime(),
                    rain_periods[-1].getUserFriendlyForecastTime())

            body = u'Forecasts:\n'
            body += u"{:5} {:7} {:25} {:6} {:6}\n".format('Hour: ', 'Celsius',
                                                          'Condition', 'Prob.', 'Wind')
            for f in forecasts:
                body += str(f) + '\n'

            alert_message = Alert.create_info_alert(subject, body)
            zm = pe.get_zone_manager_from_context()
            result = zm.get_alert_manager().process_alert(alert_message, zm)
            if not result:
                pe.log_info('Failed to send rain/snow alert')
        else:
            pe.log_info('There is no rain/snow today.')


AlertRainOrSnowDuringTheDay()
