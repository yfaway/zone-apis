from typing import List

from zone_api.alert import Alert
from zone_api.core.devices.computer import Computer
from zone_api.core.event_info import EventInfo
from zone_api.core.parameters import Parameters, ParameterConstraint, positive_number_validator
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action


@action(events=[ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED, ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED],
        devices=[Computer], unique_instance=True)
class AlertOnBadComputerStates(Action):
    """ Send a critical alert if a bad state is detected. """

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        max_cpu_temperature_in_degree = self.parameters().get(self, 'maxCpuTemperatureInDegree', 70)
        max_gpu_temperature_in_degree = self.parameters().get(self, 'maxGpuTemperatureInDegree', 70)
        interval_between_alerts_in_minutes = self.parameters().get(self, 'intervalBetweenAlertsInMinutes', 15)

        self._thresholds = [max_cpu_temperature_in_degree, max_gpu_temperature_in_degree]
        self._names = ["CPU", "GPU"]
        self._interval_between_alerts_in_minutes = interval_between_alerts_in_minutes
        self._alerts = [None, None]  # CPU & GPU

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [ParameterConstraint.optional('maxCpuTemperatureInDegree', positive_number_validator),
                ParameterConstraint.optional('maxGpuTemperatureInDegree', positive_number_validator),
                ParameterConstraint.optional('intervalBetweenAlertsInMinutes', positive_number_validator)
                ]

    def on_action(self, event_info: EventInfo):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        # noinspection PyTypeChecker
        computer: Computer = zone.get_device_by_event(event_info)

        if event_info.get_event_type() == ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED:
            self._process_event(zone_manager, computer, computer.get_cpu_temperature(), 0)
        elif event_info.get_event_type() == ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED:
            self._process_event(zone_manager, computer, computer.get_gpu_temperature(), 1)
        else:
            return False

        return True

    def _process_event(self, zone_manager, computer, temperature, index: int):
        if temperature > self._thresholds[index]:
            self._notified_cpu_temperature = True
            alert_message = f'{self._names[index]} temperature for {computer.get_item_name()} at {temperature} ' \
                            f'is above the threshold of {self._thresholds[index]} degree. '
            alert_module = alert_message
            self._alerts[index] = Alert.create_critical_alert(alert_message, None, [],
                                                              alert_module, self._interval_between_alerts_in_minutes)
            zone_manager.get_alert_manager().process_alert(self._alerts[index], zone_manager)
        elif self._alerts[index] is not None:
            alert_message = f'{self._names[index]} temperature for {computer.get_item_name()} is back to normal'
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)
            # noinspection PyUnresolvedReferences
            self._alerts[index].cancel()
            self._alerts[index] = None
