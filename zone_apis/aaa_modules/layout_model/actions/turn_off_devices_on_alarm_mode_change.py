from aaa_modules.layout_model.devices.alarm_partition import AlarmPartition
from aaa_modules.layout_model.zone import ZoneEvent
from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.chromecast_audio_sink import ChromeCastAudioSink


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

    def onAction(self, event_info):
        events = event_info.getEventDispatcher()
        zone_manager = event_info.getZoneManager()

        for z in zone_manager.get_zones():
            z.turnOffLights(events)

        audio_sinks = zone_manager.get_devices_by_type(ChromeCastAudioSink)
        for s in audio_sinks:
            s.pause()

        return True
