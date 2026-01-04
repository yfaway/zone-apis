from zone_api.audio_manager import Genre, get_music_streams_by_genres, get_main_audio_sink
from zone_api.core.zone import Zone, Level
from zone_api_test.core.device_test import DeviceTest, create_zone_manager


class AudioManagerTest(DeviceTest):
    """ Unit tests for AudioManager. """

    def setUp(self):
        self.sink1, item_set1 = self.create_audio_sink('1')
        self.sink2, item_set2 = self.create_audio_sink('2')

        self.set_items(item_set1 + item_set2)
        super(AudioManagerTest, self).setUp()

        self.floor1_zone = Zone('foyer', [self.sink1], Level.FIRST_FLOOR)
        self.floor2_zone = Zone('toilet', [self.sink2], Level.SECOND_FLOOR)
        self.floor3_zone = Zone('bedroom', [self.sink2], Level.THIRD_FLOOR)
        self.floor0_zone = Zone('utility', [self.sink2], Level.BASEMENT)

    def testGetMainAudioSink_noSink_returnNone(self):
        zm = create_zone_manager([Zone('foyer')])
        self.assertEqual(None, get_main_audio_sink(zm))

    def testGetMainAudioSink_multipleFloorHasSinks_returnFirstFloor(self):
        zm = create_zone_manager([self.floor1_zone, self.floor2_zone])
        self.assertEqual(self.sink1, get_main_audio_sink(zm))

    def testGetMainAudioSink_sinkOn2ndFloor_returnFirstFloor(self):
        zm = create_zone_manager([Zone('foyer'), self.floor2_zone])
        self.assertEqual(self.sink2, get_main_audio_sink(zm))

    def testGetMainAudioSink_sinkOn3rdFloor_returnFirstFloor(self):
        zm = create_zone_manager([Zone('foyer'), self.floor3_zone])
        self.assertEqual(self.sink2, get_main_audio_sink(zm))

    def testGetMainAudioSink_sinkOnBasement_returnFirstFloor(self):
        zm = create_zone_manager([Zone('foyer'), self.floor0_zone])
        self.assertEqual(self.sink2, get_main_audio_sink(zm))

    def testGetMusicStreamsByGenres_oneGenre_returnNonEmptyList(self):
        genres = get_music_streams_by_genres([Genre.CLASSICAL])
        self.assertTrue(len(genres) > 0)

    def testGetMusicStreamsByGenres_multipleGenres_returnNonEmptyList(self):
        classical_genres = get_music_streams_by_genres([Genre.CLASSICAL])
        mixed_genres = get_music_streams_by_genres([Genre.CLASSICAL, Genre.INSTRUMENT])

        self.assertTrue(len(mixed_genres) > len(classical_genres))
