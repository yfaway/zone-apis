from typing import Union, List

from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink
from zone_api.core.immutable_zone_manager import ImmutableZoneManager
from zone_api.core.neighbor import NeighborType
from zone_api.core.zone import Zone, Level
from zone_api.music_streams import Genre, MusicStream, MusicStreams


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


def get_music_streams_by_genres(genres: List[Genre]) -> List[MusicStream]:
    streams = []
    for stream in list(MusicStreams):
        if stream.value.genre in genres:
            streams.append(stream.value)

    return streams
