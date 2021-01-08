"""
An utility class to retrieve the weather forecast from the Environment Canada
service.
https://www.weather.gc.ca/forecast/
"""

import re
import time
import requests


class Forecast(object):
    """
    Represent the weather forecast.
    """

    def __init__(self, forecast_time, temperature, condition,
                 precipitation_probability, wind):
        self._forecastTime = forecast_time
        self._temperature = temperature
        self._condition = condition
        self._precipitation_probability = precipitation_probability
        self._wind = wind

    def getForecastTime(self):
        """
        Return the hour in 24-hour format.

        :rtype: int
        """
        return self._forecastTime

    def getUserFriendlyForecastTime(self):
        """
        Returns the forecast hour in user friendly format (1AM, 2PM,...)

        :rtype: str
        """

        hour = self._forecastTime

        if hour == 0:
            return 'Midnight'
        elif hour < 12:
            return str(hour) + ' AM'
        elif hour == 12:
            return 'Noon'
        else:
            return str(hour - 12) + ' PM'

    def getTemperature(self):
        """
        Return the temperature in Celcius.

        :rtype: int
        """
        return self._temperature

    def getCondition(self):
        """
        Return the weather condition.

        :rtype: str
        """
        return self._condition

    def getPrecipationProbability(self):
        """
        Return the precipation probability.
        Possible values: High (70%+), Medium (60% - 70%), Low (< 40%), or Nil (0%).

        :rtype: str
        """
        return self._precipitation_probability

    def getWind(self):
        """
        Return the wind info such as "15 NW".

        :rtype: str
        """
        return self._wind

    def __str__(self):
        """
        :rtype: str
        """
        value = u"{:5}: {:7} {:25} {:6} {:6}".format(self.getForecastTime(),
                                                     self.getTemperature(), self.getCondition(),
                                                     self.getPrecipationProbability(), self.getWind())
        return value


class EnvCanada(object):
    """
    Utility class to retrieve the hourly forecast.
    """

    CITY_FORECAST_MAPPING = {'ottawa': 'on-118'}
    """
    Mapping from lowercase city name to the env canada identifier.
    """

    @staticmethod
    def retrieve_hourly_forecast(city_or_url, hour_count=12):
        """
        Retrieves the hourly forecast for the given city.

        :param str city_or_url: the city name or the Environment Canada website\
            'https://www.weather.gc.ca/forecast/hourly/on-118_metric_e.html'
        :param int hour_count: the # of forecast hour to get, starting from \
            the next hour relative to the current time.
        :rtype: list(Forecast)
        :raise: ValueError if cityOrUrl points to an invalid city, or if \
            hourCount is more than 24 and less than 1.
        """
        if hour_count > 24 or hour_count < 1:
            raise ValueError("hourCount must be between 1 and 24.")

        if city_or_url[0:6].lower() != 'https:':
            normalized_city = city_or_url.lower()
            if normalized_city not in EnvCanada.CITY_FORECAST_MAPPING:
                raise ValueError(
                    "Can't map city name to URL for {}".format(city_or_url))

            url = 'https://www.weather.gc.ca/forecast/hourly/{}_metric_e.html'.format(
                EnvCanada.CITY_FORECAST_MAPPING[normalized_city])
        else:
            url = city_or_url

        data = requests.get(url).text

        time_struct = time.localtime()
        hour_of_day = time_struct[3]

        pattern = r"""header2.*?\>(-?\d+)<           # temp 
                      .*?<p>(.*?)</p>                # condition
                      .*?header4.*?>(.+?)<           # precip probability
                      .*?abbr.*?>(.+?)</abbr> (.*?)< # wind direction and speed
            """
        forecasts = []
        index = 0
        for increment in range(1, hour_count + 1):
            hour = (hour_of_day + increment) % 24
            hour_string = ("0" + str(hour)) if hour < 10 else str(hour)
            hour_string += ":00"

            search_string = '<td headers="header1" class="text-center">{}</td>'.format(hour_string)
            index = data.find(search_string, index)

            subdata = data[index:]

            match = re.search(pattern, subdata,
                              re.MULTILINE | re.DOTALL | re.VERBOSE)
            if not match:
                raise ValueError("Invalid pattern.")

            temperature = int(match.group(1))
            condition = match.group(2)
            precipitation_probability = match.group(3)
            wind = u'' + match.group(5) + ' ' + match.group(4)

            forecasts.append(Forecast(hour, temperature, condition, precipitation_probability, wind))

        return forecasts
