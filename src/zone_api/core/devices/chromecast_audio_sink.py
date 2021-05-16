import time
from typing import Union

from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device
from zone_api.music_streams import MusicStream

MAX_SAY_WAIT_TIME_IN_SECONDS = 20


class ChromeCastAudioSink(Device):
    """
    Represents a ChromeCast audio sink.
    """

    def __init__(self, sink_name, player_item, volume_item, title_item, idling_item, out_current_stream_item=None):
        """
        Ctor

        :param str sink_name: the sink name for voice and audio play. The sink
            name can be retrieved by running "openhab-cli console" and then
            "smarthome:audio sinks".
        :param PlayerItem player_item:
        :param NumberItem volume_item:
        :param StringItem title_item:
        :param SwitchItemItem idling_item:
        :param StringItem out_current_stream_item: the optional item to display the current music stream name
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, pe.create_string_item(f'Chromecast-{sink_name}'),
                        [player_item, volume_item, title_item, idling_item])

        self._sink_name = sink_name

        self._volume_item = volume_item
        self._title_item = title_item
        self._player_item = player_item
        self._idling_item = idling_item
        self._out_current_stream_item = out_current_stream_item

        self.streamUrl = None
        self.lastTtsMessage = None

        self._testMode = False
        self._testLastCommand = None

        self._lastCommandTimestamp = time.time()
        self._lastCommand = None

    def play_message(self, message, volume=50):
        """
        Play the given message on one or more ChromeCast and wait till it finishes 
        (up to MAX_SAY_WAIT_TIME_IN_SECONDS seconds). Afterward, pause the player.
        After this call, cast.isActive() will return False.

        If self._testMode is True, no message will be sent to the cast.

        :param str message: the message to tts
        :param int volume: the volume value, 0 to 100 inclusive
        :return: boolean True if success; False if stream name is invalid.
        :raise: ValueError if volume is not in the 0 - 100 inclusive range, or if\
        message is None or empty.
        """
        if volume < 0 or volume > 100:
            raise ValueError('volume must be between 0 and 100')

        if message is None or '' == message:
            raise ValueError('message must not be null or empty')

        was_active = self.is_active()
        previous_volume = pe.get_number_value(self._volume_item)

        pe.set_number_value(self._volume_item, volume)
        if not self._testMode:
            pe.play_text_to_speech_message(self.get_sink_name(), message)
        else:
            self._testLastCommand = 'playMessage'

        self.lastTtsMessage = message

        if not self._testMode:
            # Wait until the cast is available again or a specific number of seconds 
            # has passed. This is a workaround for the limitation that the OpenHab
            # 'say' method is non-blocking.
            seconds = 2
            time.sleep(seconds)

            while seconds <= MAX_SAY_WAIT_TIME_IN_SECONDS:
                if self._has_title():  # this means the announcement is still happening.
                    time.sleep(1)
                    seconds += 1
                else:  # announcement is finished.
                    seconds = MAX_SAY_WAIT_TIME_IN_SECONDS + 1

            self.pause()

        if was_active:
            pe.set_number_value(self._volume_item, previous_volume)
            self.resume()

        return True

    def play_sound_file(self, local_file, duration_in_secs, volume=None):
        """
        Plays the provided local sound file. See '/etc/openhab/sound'.

        :param volume:
        :param str local_file: a sound file located in '/etc/openhab/sound'
        :param int duration_in_secs: the duration of the sound file in seconds
        :rtype: boolean
        """

        self._lastCommandTimestamp = time.time()
        self._lastCommand = local_file

        if self._testMode:
            self._testLastCommand = 'playSoundFile'
            return True

        was_active = self.is_active()
        previous_volume = pe.get_number_value(self._volume_item)

        if volume is not None:
            pe.set_number_value(self._volume_item, volume)

        pe.play_local_audio_file(self.get_sink_name(), local_file)

        if was_active:
            time.sleep(duration_in_secs + 1)
            pe.set_number_value(self._volume_item, previous_volume)
            self.resume()

        return True

    def play_stream(self, url_or_stream: Union[str, MusicStream], volume=None):
        """
        Play the given stream url.

        :param volume:
        :param str url_or_stream: a string Url or a MusicStream object
        :return: boolean True if success; False if stream name is invalid.
        """

        if volume is not None and (volume < 0 or volume > 100):
            raise ValueError('volume must be between 0 and 100.')

        if url_or_stream is None:
            raise ValueError('url_or_stream must be specified.')

        if self._testMode:
            self._testLastCommand = 'playStream'
            return True

        if volume is not None:
            pe.set_number_value(self._volume_item, volume)

        if isinstance(url_or_stream, MusicStream):
            url = url_or_stream.url
            if self._out_current_stream_item is not None:
                pe.set_string_value(self._out_current_stream_item, url_or_stream.name)
        else:
            url = url_or_stream

        if url == self.get_stream_url():
            self.resume()
        else:
            pe.play_stream_url(self.get_sink_name(), url)
            self.streamUrl = url

        return True

    def pause(self):
        """
        Pauses the chrome cast player.
        """
        if self._testMode:
            self._testLastCommand = 'pause'
            return

        pe.change_player_state_to_pause(self._player_item)

    def resume(self):
        """
        Resumes playing.
        """

        if self._testMode:
            self._testLastCommand = 'resume'
            return

        if pe.is_in_on_state(self._idling_item):
            pe.play_stream_url(self.get_sink_name(), self.get_stream_url())
        else:
            pe.play_stream_url(self.get_sink_name(), self.get_stream_url())

        pe.change_player_state_to_play(self._player_item)

    def is_active(self):
        """
        Return true if the the chromecast is playing something.
        """
        return not pe.is_in_on_state(self._idling_item) and pe.is_player_playing(self._player_item)

    def _has_title(self):
        """
        :rtype: bool
        """
        title = pe.get_string_value(self._title_item)
        return title is not None and title != ''

    def get_stream_url(self):
        """
        Returns the current stream Uri or None if no stream set.

        :rtype: str
        """
        return self.streamUrl

    def get_last_tts_message(self):
        """
        :rtype: str
        """
        return self.lastTtsMessage

    def get_sink_name(self):
        """
        Return the sink name for Voice.say and Audio.playStream usages.

        :rtype: str
        """
        return self._sink_name

    def _set_test_mode(self):
        self._testMode = True
        self._testLastCommand = None

    def _get_last_test_command(self):
        return self._testLastCommand
