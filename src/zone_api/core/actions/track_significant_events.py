from collections import deque
import datetime
import json
from threading import Timer
from typing import Any, Dict, List
from zone_api import platform_encapsulator as pe
from zone_api.core.action import action, Action
from zone_api.core.devices.network_presence import NetworkPresence
from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.event_info import EventInfo
from zone_api.core.parameters import ParameterConstraint, Parameters, no_op_validator, positive_number_validator
from zone_api.core.zone_event import ZoneEvent

EVENTS = [ZoneEvent.PARTITION_ARMED_AWAY, ZoneEvent.PARTITION_ARMED_STAY, ZoneEvent.PARTITION_DISARMED_FROM_AWAY,
                ZoneEvent.PARTITION_DISARMED_FROM_STAY, ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED,
                ZoneEvent.DOOR_OPEN, ZoneEvent.DOOR_CLOSED, ZoneEvent.WINDOW_OPEN, ZoneEvent.WINDOW_CLOSED,
                ZoneEvent.NETWORK_PRESENCE_CHANGED]

@action(events=EVENTS, devices=[], internal=True, external=True)
class TrackSignificantEvents(Action):
    """
    Track significant events such as security status changes, external door open / close, and so on (see event list
    above). Hold a fixed number of events (configurable). Each time an event is triggered, it is appended to the list
    and the whole set of data is then output to a string item (name is configurable) in JSON format.

    This action also exposes API (#add_event) for other actions to add events directly via ZoneManger.
    """

    MAX_EVENT_COUNT_KEY = 'maxEventCount'
    OUTPUT_ITEM_KEY = 'outputItem'

    DEFAULT_OUTPUT_ITEM_NAME = 'Out_SignificantEvents'

    DEFERRED_DEPARTURE_EVENT_DURATION_IN_MINUTES = 5

    def __init__(self, parameters: Parameters):
        super().__init__(parameters)

        self._max_event_count = self.parameters().get(self, TrackSignificantEvents.MAX_EVENT_COUNT_KEY, 100)
        self._output_item = self.parameters().get(self, TrackSignificantEvents.OUTPUT_ITEM_KEY,
                                                  TrackSignificantEvents.DEFAULT_OUTPUT_ITEM_NAME)
        self._events = deque(maxlen=self._max_event_count)

        self._timers: dict[NetworkPresence, Timer] = {}

    @staticmethod
    def supported_parameters() -> List[ParameterConstraint]:
        return Action.supported_parameters() + \
               [ParameterConstraint.optional(TrackSignificantEvents.MAX_EVENT_COUNT_KEY, positive_number_validator),
                ParameterConstraint.optional(TrackSignificantEvents.OUTPUT_ITEM_KEY, no_op_validator),
                ]


    def on_action(self, event_info: EventInfo):
        event_type = event_info.get_event_type()
        zone = event_info.get_zone()
        device = event_info.get_device()
        zm = event_info.get_zone_manager();

        event: Dict[str, Any] = {'event_type' : event_type.value,
                                 'timestamp': datetime.datetime.now().isoformat() }

        if event_type == ZoneEvent.PARTITION_ARMED_AWAY:
            event['message'] = "House armed away"
        elif event_type == ZoneEvent.PARTITION_ARMED_STAY:
            event['message'] = "House armed stay"
        elif event_type == ZoneEvent.PARTITION_DISARMED_FROM_AWAY:
            event['message'] = "House disarmed from away"
        elif event_type == ZoneEvent.PARTITION_DISARMED_FROM_STAY:
            event['message'] = "House disarmed from stay"
        elif event_type == ZoneEvent.PARTITION_IN_ALARM_STATE_CHANGED:
            partition: AlarmPartition = event_info.get_device() # type: ignore
            if partition.is_in_alarm():
                event['message'] = "Security system is on alarm"
            else:
                event['message'] = "Security alarm cleared"
        elif event_type == ZoneEvent.WINDOW_OPEN:
            event['message'] = "Window opened in zone " + zone.get_name()
        elif event_type == ZoneEvent.WINDOW_CLOSED:
            event['message'] = "Window closed in zone " + zone.get_name()
        elif event_type == ZoneEvent.DOOR_OPEN:
            if zone.is_external():
                event['message'] = "Door opened in zone " + zone.get_name()
            else:
                return False
        elif event_type == ZoneEvent.DOOR_CLOSED:
            if zone.is_external():
                event['message'] = "Door closed in zone " + zone.get_name()
            else:
                return False
        elif event_type == ZoneEvent.NETWORK_PRESENCE_CHANGED:
            network_presence : NetworkPresence = device # type: ignore

            # IPhone doesn't response to ping often, especially when the screen is off. We do not want to be bombarded
            # with repeated arrival / depature event. So we will only record departure event if it is still relevant
            # DEFERRED_DEPARTURE_EVENT_DURATION_IN_MINUTES later.
            timer = self._timers[network_presence] if network_presence in self._timers else None

            friendly_name = self._map_network_presence_to_friendly_name(zm, network_presence)
            if network_presence.is_present():
                if timer is not None: # Let's not record the event as the one before this must have been an arrival
                    timer.cancel()
                    del self._timers[network_presence]
                else:
                    event['message'] = f"{friendly_name} arrived home"
            else:
                def record_departure_event():
                    event['message'] = f"{friendly_name} left home"
                    self._add_and_update_output_item_value(event)

                    del self._timers[network_presence]

                timer = Timer(TrackSignificantEvents.DEFERRED_DEPARTURE_EVENT_DURATION_IN_MINUTES * 60,
                              record_departure_event)
                timer.start()
                self._timers[network_presence] = timer

        if 'message' in event:
            self._add_and_update_output_item_value(event)

        return True

    def add_event(self, event_type: ZoneEvent, message: str):
        event: Dict[str, Any] = {
            'event_type' : event_type.value,
            'message' : message,
            'timestamp' : datetime.datetime.now().isoformat()
            }

        self._add_and_update_output_item_value(event)

    def _add_and_update_output_item_value(self, new_event: Dict[str, Any]):
        self._events.append(new_event)

        json_str = json.dumps(list(reversed(self._events)))
        pe.set_string_value(self._output_item, json_str)
        # self.log_error(json_str)

    def _map_network_presence_to_friendly_name(self, zm, device : NetworkPresence):
        friendly_name = device.get_item_name()

        idx = friendly_name.find("Owner")
        if idx != -1:
            friendly_name = f"owner{friendly_name[idx + 5: idx + 6]}"
            mapped_name = zm.map_label(friendly_name)
            if mapped_name is not None:
                friendly_name = mapped_name

        return friendly_name