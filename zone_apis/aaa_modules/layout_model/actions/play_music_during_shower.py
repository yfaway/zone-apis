from aaa_modules.layout_model.action import action
from aaa_modules.layout_model.devices.switch import Fan
from aaa_modules.layout_model.neighbor import NeighborType
from aaa_modules.layout_model.zone import ZoneEvent
from aaa_modules.layout_model.devices.activity_times import ActivityTimes
from aaa_modules.layout_model.devices.chromecast_audio_sink import ChromeCastAudioSink


@action(events=[ZoneEvent.SWITCH_TURNED_ON, ZoneEvent.SWITCH_TURNED_OFF], devices=[Fan])
class PlayMusicDuringShower:
    """
    Play the provided URL stream when the washroom fan is turned on. Pause
    when it it turned off.
    Won't play if it is sleep time. Otherwise, adjust the volume based on the
    current activity.
    """

    def __init__(self, music_url='http://hestia2.cdnstream.com:80/1277_192'):
        """
        Ctor

        :param str music_url:
        :raise ValueError: if any parameter is invalid
        """

        if music_url is None:
            raise ValueError('musicUrl must be specified')

        self.music_url = music_url

    def onAction(self, event_info):
        zone = event_info.getZone()
        zone_manager = event_info.getZoneManager()

        # Get an audio sink from the current zone or a neighbor zone
        sinks = zone.getDevicesByType(ChromeCastAudioSink)
        if len(sinks) == 0:
            neighbor_zones = zone.getNeighborZones(zone_manager,
                                                   [NeighborType.OPEN_SPACE, NeighborType.OPEN_SPACE_MASTER,
                                                    NeighborType.OPEN_SPACE_SLAVE])
            for z in neighbor_zones:
                sinks = z.getDevicesByType(ChromeCastAudioSink)
                if len(sinks) > 0:
                    break

            if len(sinks) == 0:
                return False

        activity = None
        if zone_manager is not None:
            activities = zone_manager.get_devices_by_type(ActivityTimes)
            if len(activities) > 0:
                activity = activities[0]

                if activity.isSleepTime():
                    return False

        if ZoneEvent.SWITCH_TURNED_ON == event_info.getEventType():
            volume = 25 if (activity is not None and activity.isQuietTime()) else 35
            sinks[0].play_stream(self.music_url, volume)
        elif ZoneEvent.SWITCH_TURNED_OFF == event_info.getEventType():
            sinks[0].pause()

        return True
