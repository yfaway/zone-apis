from enum import Enum, unique
from typing import Union, List

from aaa_modules.layout_model.devices.chromecast_audio_sink import ChromeCastAudioSink
from aaa_modules.layout_model.immutable_zone_manager import ImmutableZoneManager
from aaa_modules.layout_model.neighbor import NeighborType
from aaa_modules.layout_model.zone import Zone, Level


@unique
class Genre(Enum):
    CLASSICAL = 1,
    INSTRUMENT = 2,
    JAZZ = 3,
    ROCK = 4,


class MusicStream:
    def __init__(self, genre: Genre, url: str):
        self.genre = genre
        self.url = url


@unique
class MusicStreams(Enum):
    """ An enum of the MP3 music streams."""

    WWFM_CLASSICAL = MusicStream(Genre.CLASSICAL, "https://wwfm.streamguys1.com/live-mp3")
    VENICE_CLASSICAL = MusicStream(Genre.CLASSICAL, "http://174.36.206.197:8000/stream")
    PORTLAND_ALL_CLASSICAL = MusicStream(Genre.CLASSICAL, "http://player.allclassical.org/streamplaylist/ac96k.pls")

    MUSIC_LAKE_INSTRUMENTAL = MusicStream(Genre.INSTRUMENT, "http://104.251.118.50:8626/listen.pls?sid=1&t=.pls")

    FM113_SMOOTH_JAZZ = MusicStream(Genre.JAZZ, "http://113fm-edge2.cdnstream.com:80/1725_128")
    CD101_9_NY_SMOOTH_JAZZ = MusicStream(Genre.JAZZ, "http://hestia2.cdnstream.com:80/1277_192")
    JAZZ_CAFE = MusicStream(Genre.JAZZ, "http://radio.wanderingsheep.tv:8000/jazzcafe")

    CLASSIC_ROCK_FLORIDA = MusicStream(Genre.ROCK, "http://198.58.98.83:8258/stream")
    RADIO_PARADISE_ROCK = MusicStream(Genre.ROCK, "http://stream-dc2.radioparadise.com:80/mp3-192")

    # MEDITATION_YIMAGO_RADIO_4 = MusicStream(Genre., "http://199.195.194.94:8109/stream")
    # SANTA_RADIO = "http://149.255.59.164:8041/stream"
    # XMAS_MUSIC = "http://91.121.134.23:8380/stream"


def get_main_audio_sink(zm: ImmutableZoneManager) -> Union[ChromeCastAudioSink, None]:
    """ Returns the first sink on the the following floor order: 1st, 2nd, 3rd and basement. """
    levels = [Level.FIRST_FLOOR, Level.SECOND_FLOOR, Level.THIRD_FLOOR, Level.BASEMENT]

    for level in levels:
        zones = [z for z in zm.get_zones() if z.get_level() == level]

        for z in zones:
            sinks = z.get_devices_by_type(ChromeCastAudioSink)
            if len(sinks) > 0:
                return sinks[0]

    return None


def get_nearby_audio_sink(zone: Zone, zm: ImmutableZoneManager) -> Union[ChromeCastAudioSink, None]:
    """
    Returns the first found audio sink in the current zone or in nearby open space neighbors.
    """
    sinks = zone.get_devices_by_type(ChromeCastAudioSink)
    if len(sinks) == 0:
        neighbor_zones = zone.get_neighbor_zones(
            zm, [NeighborType.OPEN_SPACE, NeighborType.OPEN_SPACE_MASTER,
                 NeighborType.OPEN_SPACE_SLAVE])

        for z in neighbor_zones:
            sinks = z.get_devices_by_type(ChromeCastAudioSink)
            if len(sinks) > 0:
                break

    return sinks[0] if len(sinks) > 0 else None


def get_music_streams_by_genres(genres: List[Genre]) -> List[str]:
    urls = []
    for stream in list(MusicStreams):
        if stream.value.genre in genres:
            urls.append(stream.value.url)

    return urls
