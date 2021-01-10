from enum import Enum, unique
from typing import Union

from aaa_modules.layout_model.devices.chromecast_audio_sink import ChromeCastAudioSink
from aaa_modules.layout_model.immutable_zone_manager import ImmutableZoneManager
from aaa_modules.layout_model.neighbor import NeighborType
from aaa_modules.layout_model.zone import Zone


@unique
class MusicStream(Enum):
    """ An enum of the MP3 music streams."""

    WWFM_CLASSICAL = "https://wwfm.streamguys1.com/live-mp3"
    VENICE_CLASSICAL = "http://174.36.206.197:8000/stream"
    PORTLAND_ALL_CLASSICAL = "http://player.allclassical.org/streamplaylist/ac96k.pls"
    AUDIOPHILE_CLASSICAL = "http://8.38.78.173:8093/stream"
    FM113_SMOOTH_JAZZ = "http://113fm-edge2.cdnstream.com:80/1725_128"
    CD101_9_NY_SMOOTH_JAZZ = "http://hestia2.cdnstream.com:80/1277_192"
    JAZZ_CAFE = "http://radio.wanderingsheep.tv:8000/jazzcafe"
    MEDITATION_YIMAGO_RADIO_4 = "http://199.195.194.94:8109/stream"
    SANTA_RADIO = "http://149.255.59.164:8041/stream"
    XMAS_MUSIC = "http://91.121.134.23:8380/stream"
    CBC_RADIO_2 = "http://cbcr2tor.akacast.akamaistream.net/7/364/451661/v1/rc.akacast.akamaistream.net/cbc_r2_tor"
    CLASSIC_ROCK_FLORIDA = "http://198.58.98.83:8258/stream"
    RADIO_PARADISE_ROCK = 'http://stream-dc2.radioparadise.com:80/mp3-192'


class AudioManager:
    @classmethod
    def get_nearby_audio_sink(cls, zone: Zone, zm: ImmutableZoneManager) -> Union[ChromeCastAudioSink, None]:
        """
        Returns the first found audio sink in the current zone or in nearby open space neighbors.
        """
        sinks = zone.getDevicesByType(ChromeCastAudioSink)
        if len(sinks) == 0:
            neighbor_zones = zone.getNeighborZones(
                zm, [NeighborType.OPEN_SPACE, NeighborType.OPEN_SPACE_MASTER,
                     NeighborType.OPEN_SPACE_SLAVE])

            for z in neighbor_zones:
                sinks = z.getDevicesByType(ChromeCastAudioSink)
                if len(sinks) > 0:
                    break

        return sinks[0] if len(sinks) > 0 else None
