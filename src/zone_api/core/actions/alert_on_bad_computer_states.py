from zone_api.alert import Alert
from zone_api.core.devices.computer import Computer
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action


@action(events=[ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED, ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED],
        devices=[Computer], unique_instance=True)
class AlertOnBadComputerStates:
    """ Send a critical alert if a bad state is detected. """

    def __init__(self):
        self._thresholds = None
        self._names = None
        self._interval_between_alerts_in_minutes = None
        self._alerts = None

    # noinspection PyUnusedLocal
    def on_startup(self, event_info: EventInfo):
        max_cpu_temperature_in_degree = self.parameters().get(self, 'maxCpuTemperatureInDegree', 70)
        max_gpu_temperature_in_degree = self.parameters().get(self, 'maxGpuTemperatureInDegree', 70)
        interval_between_alerts_in_minutes = self.parameters().get(self, 'intervalBetweenAlertsInMinutes', 15)

        self.log_info(f"Temp: {max_cpu_temperature_in_degree}")

        if max_cpu_temperature_in_degree <= 0:
            raise ValueError('max_cpu_temperature_in_degree must be positive')
        if max_gpu_temperature_in_degree <= 0:
            raise ValueError('max_gpu_temperature_in_degree must be positive')
        if interval_between_alerts_in_minutes <= 0:
            raise ValueError('intervalBetweenAlertsInMinutes must be positive')

        self._thresholds = [max_cpu_temperature_in_degree, max_gpu_temperature_in_degree]
        self._names = ["CPU", "GPU"]
        self._interval_between_alerts_in_minutes = interval_between_alerts_in_minutes
        self._alerts = [None, None]  # CPU & GPU

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
