from typing import List

from zone_api import platform_encapsulator as pe
from zone_api.core.event_info import EventInfo
from zone_api.core.parameters import Parameters, ParameterConstraint, positive_number_validator
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action


@action(events=[ZoneEvent.TIMER], devices=[], zone_name_pattern='.*Virtual.*')
class GenerateWeatherForecastHtml(Action):
    """
    Generate the weather forecast HTML page similar to what is on the Ecobee thermostat view, and save it in OpenHab's
    html folder. This will be displayed via a Webview. The content in the html folder is considered static; however, as
    this action generates a new file after an event, the content of the Webview will be refreshed automatically after
    a configured interval (specified in the generated html content).
    The motivation is to get around sitemap's limitations such as the inability to dynamically update a label.
    This action is triggered by a recurring timer.
    """
    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [ParameterConstraint.optional(
                   'itemPrefix', positive_number_validator, ""),
                   ParameterConstraint.optional('htmlContentRefreshIntervalInSeconds', positive_number_validator,
                                                "must be positive"),
                   ParameterConstraint.optional('htmlContentGenerationIntervalInMinutes', positive_number_validator,
                                                "must be positive")]

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._item_prefix = self.parameters().get(self, 'itemPrefix', 'FF_Virtual_Weather_Temperature_')
        self._html_content_refresh_interval_in_seconds = self.parameters().get(
            self, 'htmlContentRefreshIntervalInSeconds', 5)
        self._html_content_generation_interval_in_minutes = self.parameters().get(
            self, 'htmlContentGenerationIntervalInMinutes', 5)

    def on_startup(self, event_info: EventInfo):
        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every(self._html_content_generation_interval_in_minutes).minutes.do(
            lambda: self.on_action(self.create_timer_event_info(event_info)))

        # generate the initial content immediately
        self._generate_html(event_info)

    def on_action(self, event_info):
        self._generate_html(event_info)

    def _generate_html(self, event_info):
        prefix = self._item_prefix
        items_html = ""
        item_div_templates = """
            <div class="mdl-form__row mdl-cell mdl-cell--4-col mdl-cell--4-col-tablet ">
                <span class="mdl-form__label">{}</span>
                <div class="mdl-form__control mdl-form__text">{}</div>
            </div>           
        """

        def map_to_icon_html(a_weather_symbol: int) -> str | None:
            # @see https://developer.ecobee.com/home/developer/api/documentation/v1/objects/WeatherForecast.shtml
            if a_weather_symbol == 0:
                icon = 'sun'
            elif a_weather_symbol in range(1, 4):
                icon = 'sun_clouds'
            elif a_weather_symbol in range(5, 9):
                icon = 'rain'
            elif a_weather_symbol in range(10, 14):
                icon = 'snow'
            elif a_weather_symbol in [16]:
                icon = 'wind'
            else:
                icon = None

            if icon is not None:
                associated_html = f"""
            <span class="mdl-form__icon">
                <img src="../icon/{icon}?format=svg" />
            </span>
            """
            else:
                associated_html = ""

            return associated_html

        for segment in ['Quarter1', 'Quarter2', 'Quarter3', 'Quarter4']:
            date_time = pe.get_datetime_value(prefix + segment + "_Datetime")
            temperature = round(pe.get_number_value(prefix + segment))
            weather_symbol = int(pe.get_number_value(prefix + segment + "_WeatherSymbol"))

            if date_time.time().hour == 0:
                day_segment = 'Night'
            elif date_time.time().hour == 6:
                day_segment = 'Morning'
            elif date_time.time().hour == 12:
                day_segment = 'Afternoon'
            else:
                day_segment = 'Evening'

            icon_html = map_to_icon_html(weather_symbol)
            items_html += item_div_templates.format(day_segment, icon_html + str(temperature) + " &deg;C")

        for segment in ['Tomorrow', 'In2Days', 'In3Days', 'In4Days']:
            date_time = pe.get_datetime_value(prefix + segment + "_Datetime")
            temperature_high = round(pe.get_number_value(prefix + segment + "_TempHigh"))
            temperature_low = round(pe.get_number_value(prefix + segment + "_TempLow"))
            weather_symbol = int(pe.get_number_value(prefix + segment + "_WeatherSymbol"))

            day_of_week = date_time.strftime("%A")
            icon_html = map_to_icon_html(weather_symbol)
            items_html += item_div_templates.format(
                day_of_week, icon_html + str(temperature_high) + " &deg;C &#8594; " + str(temperature_low) + " &deg;C")

        html = f"""
        <!doctype html>
<html>
  <head>
    <!-- need this to get Android app to refresh the content. -->
    <meta http-equiv="refresh" CONTENT="{self._html_content_refresh_interval_in_seconds}">

    <link rel="stylesheet" type="text/css" href="../basicui/mdl/material.min.css" />
    <link rel="stylesheet" type="text/css" href="../basicui/material-icons.css" />
    <link rel="stylesheet" type="text/css" href="../basicui/framework7-icons.css" />
    <link rel="stylesheet" type="text/css" href="../basicui/smarthome.css?v=202501122027" />

    <script src="../basicui/smarthome.js?v=202501122027"></script>
    <script src="../basicui/mdl/material.min.js"></script>
  </head>

  <body class="mdl-color-text--grey-700">
    <div class="mdl-layout mdl-js-layout">
      <div class="mdl-layout__header mdl-layout__header--scroll navigation navigation-home">
        <div class="mdl-layout__header-row">
          <div class="mdl-layout__header-button navigation__button-back"></div>
          <div class="mdl-layout__header-button navigation__button-settings"></div>
          <div class="mdl-layout-spacer"></div>
        </div>
      </div>

      <main class="mdl-layout__content">
        <div class="page-content mdl-grid">
          <div class="mdl-form  mdl-color--white mdl-shadow--2dp mdl-cell mdl-grid mdl-cell--12-col">
            {items_html}
          </div>
        </div>
      </main>
    </div>
  </body>                                         
</html>
        """

        try:
            with open('/etc/openhab/html/weather-forecast.html', 'w') as file:
                file.write(html)
        except FileNotFoundError:
            pe.log_error("Cannot write weather forecast to file.")

        return True
