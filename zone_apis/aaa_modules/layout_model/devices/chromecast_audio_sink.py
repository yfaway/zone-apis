import time

from aaa_modules import platform_encapsulator as pe
from aaa_modules.layout_model.device import Device

MAX_SAY_WAIT_TIME_IN_SECONDS = 20

# Constant to fix a bug in OpenHab. For some reasons, OH might invoke the script twice.
COMMAND_INTERVAL_THRESHOLD_IN_SECONDS = 30


class ChromeCastAudioSink(Device):
    """
    Represents a ChromeCast audio sink.
    """

    def __init__(self, sink_name, player_item, volume_item, title_item, idling_item):
        """
        Ctor

        :param str sink_name: the sink name for voice and audio play. The sink
            name can be retrieved by running "openhab-cli console" and then
            "smarthome:audio sinks".
        :raise ValueError: if any parameter is invalid
        """
        Device.__init__(self, pe.create_string_item(f'Chromecast-{sink_name}'))

        self._sink_name = sink_name

        self._volume_item = volume_item
        self._title_item = title_item
        self._player_item = player_item
        self._idling_item = idling_item

        self.streamUrl = None
        self.lastTtsMessage = None

        self._testMode = False
        self._testLastCommand = None

        self._lastCommandTimestamp = time.time()
        self._lastCommand = None

    def playMessage(self, message, volume=50):
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

        pe.set_number_value(self._volume_item, volume)
        if not self._testMode:
            #Voice.say(message, None, self.getSinkName())
            pass
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

        return True

    def playSoundFile(self, local_file, duration_in_secs, volume=None):
        """
        Plays the provided local sound file. See '/etc/openhab2/sound'.
        Returns immediately if the same command was recently executed (see
        COMMAND_INTERVAL_THRESHOLD_IN_SECONDS).

        :param volume:
        :param str local_file: a sound file located in '/etc/openhab2/sound'
        :param int duration_in_secs: the duration of the sound file in seconds
        :rtype: boolean
        """

        if local_file == self._lastCommand:
            if (time.time() - self._lastCommandTimestamp) <= COMMAND_INTERVAL_THRESHOLD_IN_SECONDS:
                return

        self._lastCommandTimestamp = time.time()
        self._lastCommand = local_file

        if self._testMode:
            self._testLastCommand = 'playSoundFile'
            return True

        was_active = self.isActive()
        previous_volume = pe.get_number_value(self._volume_item)

        if volume is not None:
            pe.set_number_value(self._volume_item, volume)

        #Audio.playSound(self.getSinkName(), local_file)

        if was_active:
            time.sleep(duration_in_secs + 1)
            pe.set_number_value(self._volume_item, previous_volume)
            self.resume()

        return True

    def playStream(self, url, volume=None):
        """
        Play the given stream url.

        :param volume:
        :param str url:
        :return: boolean True if success; False if stream name is invalid.
        """

        if volume is not None and (volume < 0 or volume > 100):
            raise ValueError('volume must be between 0 and 100.')

        if url is None:
            raise ValueError('url must be specified.')

        if self._testMode:
            self._testLastCommand = 'playStream'
            return True

        if volume is not None:
            pe.set_number_value(self._volume_item, volume)

        if url == self.getStreamUrl():
            self.resume()
        else:
            #Audio.playStream(self.getSinkName(), url)
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
            #Audio.playStream(self.getSinkName(), self.getStreamUrl())
            pass
        else:
            #Audio.playStream(self.getSinkName(), self.getStreamUrl())
            pe.change_player_state_to_play(self._player_item)

    def isActive(self):
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

    def getStreamUrl(self):
        """
        Returns the current stream Uri or None if no stream set.

        :rtype: str
        """
        return self.streamUrl

    def getLastTtsMessage(self):
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

    def _setTestMode(self):
        self._testMode = True
        self._testLastCommand = None

    def _getLastTestCommand(self):
        return self._testLastCommand

# s = ChromeCastAudioSink('FF_GreatRoom_ChromeCast', "chromecast:audio:greatRoom")
# s.playMessage('the sink name for voice and audio play. The sink \
#            name can be retrieved by running', 30)
# s.playSoundFile('bell-outside.wav', 15, 30)
# s.playStream("https://wwfm.streamguys1.com/live-mp3", 30)
# s.pause()
