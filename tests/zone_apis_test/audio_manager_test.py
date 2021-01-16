from aaa_modules.audio_manager import AudioManager, Genre
from zone_apis_test.layout_model.device_test import DeviceTest


class AudioManagerTest(DeviceTest):
    """ Unit tests for AudioManager. """

    def setUp(self):
        self.set_items([])
        super(AudioManagerTest, self).setUp()

    def testGet_music_streams_by_genres_oneGenre_returnNonEmptyList(self):
        genres = AudioManager.get_music_streams_by_genres([Genre.CLASSICAL])
        self.assertTrue(len(genres) > 0)

    def testGet_music_streams_by_genres_multipleGenres_returnNonEmptyList(self):
        classical_genres = AudioManager.get_music_streams_by_genres([Genre.CLASSICAL])
        mixed_genres = AudioManager.get_music_streams_by_genres([Genre.CLASSICAL, Genre.JAZZ])

        self.assertTrue(len(mixed_genres) > len(classical_genres))
