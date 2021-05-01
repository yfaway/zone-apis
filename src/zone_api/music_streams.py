from enum import Enum, unique


@unique
class Genre(Enum):
    CLASSICAL = 1,
    INSTRUMENT = 2,
    JAZZ = 3,
    ROCK = 4,


class MusicStream:
    def __init__(self, name: str, genre: Genre, url: str):
        self.name = name
        self.genre = genre
        self.url = url


@unique
class MusicStreams(Enum):
    """ An enum of the MP3 music streams."""

    WWFM_CLASSICAL = MusicStream("WWFM Classical", Genre.CLASSICAL, "https://wwfm.streamguys1.com/live-mp3")
    VENICE_CLASSICAL = MusicStream("Venice Classical", Genre.CLASSICAL, "http://174.36.206.197:8000/stream")
    PORTLAND_ALL_CLASSICAL = MusicStream("Portland All Classical", Genre.CLASSICAL, "http://player.allclassical.org/streamplaylist/ac96k.pls")

    MUSIC_LAKE_INSTRUMENTAL = MusicStream("Music Lake Instrumental", Genre.INSTRUMENT, "http://104.251.118.50:8626/listen.pls?sid=1&t=.pls")

    FM113_SMOOTH_JAZZ = MusicStream("FM113 Smooth Jazz", Genre.JAZZ, "http://113fm-edge2.cdnstream.com:80/1725_128")
    CD101_9_NY_SMOOTH_JAZZ = MusicStream("CD101.9 NY Smooth Jazz", Genre.JAZZ, "http://hestia2.cdnstream.com:80/1277_192")
    JAZZ_CAFE = MusicStream("Jazz Cafe", Genre.JAZZ, "http://radio.wanderingsheep.tv:8000/jazzcafe")

    CLASSIC_ROCK_FLORIDA = MusicStream("Classic Rock Florida", Genre.ROCK, "http://198.58.98.83:8258/stream")
    RADIO_PARADISE_ROCK = MusicStream("Radio Paradise Rock", Genre.ROCK, "http://stream-dc2.radioparadise.com:80/mp3-192")

    # MEDITATION_YIMAGO_RADIO_4 = MusicStream(Genre., "http://199.195.194.94:8109/stream")
    # SANTA_RADIO = "http://149.255.59.164:8041/stream"
    # XMAS_MUSIC = "http://91.121.134.23:8380/stream"

