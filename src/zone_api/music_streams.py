from enum import Enum, unique
from typing import Union


@unique
class Genre(Enum):
    ALL = 1,
    BUDDHISM = 2,
    CLASSICAL = 3,
    INSTRUMENT = 10,
    JAZZ = 11,
    MEDITATION = 12,
    ROCK_BALLAD = 13,
    TECHNO = 14,
    DANCE = 15,
    FOLK = 16,

    CHINESE = 30,
    FRENCH = 31,
    ENGLISH = 32,
    JAPANESE = 33,
    ITALIAN = 34,
    RUSSIAN = 35,
    SPANISH = 36,
    VIETNAMESE = 37,


class MusicStream:
    def __init__(self, genre: Genre, name: Union[str, None] = None, url: Union[str, None] = None):
        """
        :param Union[str, None] name: the name of the stream; if not specified, derive from the genre.
        :param Union[str, None] url: the URL of the stream; if not specified, use a local stream provided by the
            underlying music controller.
        """
        self.genre = genre
        self.name = genre.name if name is None else name
        self.url = url


@unique
class MusicStreams(Enum):
    """ An enum of the MP3 music streams."""
    ALL = MusicStream(Genre.ALL, "")  # no filtering
    BUDDHISM = MusicStream(Genre.BUDDHISM)
    CLASSICAL = MusicStream(Genre.CLASSICAL)
    INSTRUMENT = MusicStream(Genre.INSTRUMENT)
    # JAZZ = MusicStream(Genre.JAZZ)
    MEDITATION = MusicStream(Genre.MEDITATION)
    ROCK_BALLAD = MusicStream(Genre.ROCK_BALLAD)
    TECHNO = MusicStream(Genre.TECHNO)
    DANCE = MusicStream(Genre.DANCE)
    FOLK = MusicStream(Genre.FOLK)

    CHINESE = MusicStream(Genre.CHINESE)
    FRENCH = MusicStream(Genre.FRENCH)
    ENGLISH = MusicStream(Genre.ENGLISH)
    JAPANESE = MusicStream(Genre.JAPANESE)
    ITALIAN = MusicStream(Genre.ITALIAN)
    RUSSIAN = MusicStream(Genre.RUSSIAN)
    SPANISH = MusicStream(Genre.SPANISH)
    VIETNAMESE = MusicStream(Genre.VIETNAMESE)

    """
    WWFM_CLASSICAL = MusicStream("WWFM Classical", Genre.CLASSICAL, "https://wwfm.streamguys1.com/live-mp3")
    VENICE_CLASSICAL = MusicStream("Venice Classical", Genre.CLASSICAL, "http://174.36.206.197:8000/stream")
    PORTLAND_ALL_CLASSICAL = MusicStream("Portland All Classical", Genre.CLASSICAL, "http://player.allclassical.org/streamplaylist/ac96k.pls")

    MUSIC_LAKE_INSTRUMENTAL = MusicStream("Music Lake Instrumental", Genre.INSTRUMENT, "http://nap.casthost.net:8626/listen.pls?sid=1")

    FM113_SMOOTH_JAZZ = MusicStream("FM113 Smooth Jazz", Genre.JAZZ, "http://113fm-edge2.cdnstream.com:80/1725_128")
    CD101_9_NY_SMOOTH_JAZZ = MusicStream("CD101.9 NY Smooth Jazz", Genre.JAZZ, "http://hestia2.cdnstream.com:80/1277_192")
    JAZZ_CAFE = MusicStream("Jazz Cafe", Genre.JAZZ, "http://radio.wanderingsheep.tv:8000/jazzcafe")

    CLASSIC_ROCK_FLORIDA = MusicStream("Classic Rock Florida", Genre.ROCK, "http://198.58.98.83:8258/stream")
    RADIO_PARADISE_ROCK = MusicStream("Radio Paradise Rock", Genre.ROCK, "http://stream-dc2.radioparadise.com:80/mp3-192")

    # MEDITATION_YIMAGO_RADIO_4 = MusicStream(Genre., "http://199.195.194.94:8109/stream")
    # SANTA_RADIO = "http://149.255.59.164:8041/stream"
    # XMAS_MUSIC = "http://91.121.134.23:8380/stream"
    """
