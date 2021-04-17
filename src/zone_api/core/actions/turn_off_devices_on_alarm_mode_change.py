from zone_api.core.devices.alarm_partition import AlarmPartition
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action
from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink


@action(events=[ZoneEvent.PARTITION_ARMED_AWAY, ZoneEvent.PARTITION_DISARMED_FROM_AWAY],
        devices=[AlarmPartition])
class TurnOffDevicesOnAlarmModeChange:
    """
    Turn off all the lights and audio devices if the house is armed-away or
    if the house is disarm (from armed-away mode). The later is needed as
    there are some rules that simulate presences using a combination of 
    lights/audio sinks.
    """

    def __init__(self):
        pass

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info):
        events = event_info.get_event_dispatcher()
        zone_manager = event_info.get_zone_manager()

        if event_info.get_event_type() == ZoneEvent.PARTITION_DISARMED_FROM_AWAY:
            for z in zone_manager.get_zones():
                if z is not event_info.get_zone():
                    z.turn_off_lights(events)
        else:
            for z in zone_manager.get_zones():
                z.turn_off_lights(events)

        audio_sinks = zone_manager.get_devices_by_type(ChromeCastAudioSink)
        for s in audio_sinks:
            s.pause()

        return True
