from zone_api.alert import Alert
from zone_api.core.devices.computer import Computer
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action
from zone_api import platform_encapsulator as pe


@action(events=[ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED, ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED],
        devices=[Computer], unique_instance=True)
class AlertOnBadComputerStates:
    """ Send a critical alert if a bad state is detected. """

    def __init__(self, max_cpu_temperature_in_degree=70, max_gpu_temperature_in_degree=70,
                 interval_between_alerts_in_minutes=15):
        """
        Ctor

        :raise ValueError: if any parameter is invalid
        """
        if max_cpu_temperature_in_degree <= 0:
            raise ValueError('max_cpu_temperature_in_degree must be positive')
        if max_gpu_temperature_in_degree <= 0:
            raise ValueError('max_gpu_temperature_in_degree must be positive')
        if interval_between_alerts_in_minutes <= 0:
            raise ValueError('intervalBetweenAlertsInMinutes must be positive')

        self._thresholds = [max_cpu_temperature_in_degree, max_gpu_temperature_in_degree]
        self._notified = [False, False]
        self._names = ["CPU", "GPU"]
        self._interval_between_alerts_in_minutes = interval_between_alerts_in_minutes

    def on_action(self, event_info: EventInfo):
        zone = event_info.get_zone()
        zone_manager = event_info.get_zone_manager()

        computer: Computer = zone.get_device_by_event(event_info)

        if event_info.get_event_type() == ZoneEvent.COMPUTER_CPU_TEMPERATURE_CHANGED:
            self._process_event(zone_manager, zone, computer, computer.get_cpu_temperature(), 0)
        elif event_info.get_event_type() == ZoneEvent.COMPUTER_GPU_TEMPERATURE_CHANGED:
            self._process_event(zone_manager, zone, computer, computer.get_gpu_temperature(), 1)
        else:
            return False

        return True

    def _process_event(self, zone_manager, zone, computer, temperature, index: int):
        if temperature > self._thresholds[index]:
            self._notified_cpu_temperature = True
            alert_message = f'{self._names[index]} temperature for {computer.get_item_name()} at {temperature} ' \
                            f'is above the threshold of {self._thresholds[index]} degree. '
            alert_module = alert_message
            alert = Alert.create_critical_alert(alert_message, None, [],
                                                alert_module, self._interval_between_alerts_in_minutes)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)
            self._notified[index] = True
        elif self._notified[index]:
            alert_message = f'{self._names[index]} temperature for {computer.get_item_name()} is back to normal'
            alert = Alert.create_info_alert(alert_message)
            zone_manager.get_alert_manager().process_alert(alert, zone_manager)
            self._notified[index] = False
