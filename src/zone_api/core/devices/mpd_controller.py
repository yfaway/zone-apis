import os.path
import subprocess
from typing import Union

from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device


class MpdController(Device):
    """
    Control the Music Player Daemon (mpd) via the accompanied mpc command.
    @see https://www.musicpd.org/
    """

    def __init__(self, item):
        """
        Ctor

        :param item: an item with the name of the format .MpdController_host_port. If the host contains ".", it has to
            be replaced with 'zz'.
        """
        Device.__init__(self, item)

        tokens = pe.get_item_name(item).split('_')
        self._host = tokens[-2].replace('zz', '.')
        self._port = int(tokens[-1])

    def shuffle_and_play(self, file_name_pattern: Union[str | None] = None):
        """
        The following actions are performed:
          - Clear the play list queue
          - Filter the music library using simple pattern matching (grep), then shuffle and play the music.
        """
        self.clear()

        self.mpc('repeat on')

        if not file_name_pattern:
            subprocess.run(f"{self._wrapped_mpc()} listall | {self._wrapped_mpc()} add", shell=True)
        else:
            # grep ignore case
            subprocess.run(f"{self._wrapped_mpc()} listall | grep -i '{file_name_pattern}' | {self._wrapped_mpc()} add",
                           shell=True)

        self.mpc('shuffle')
        self.mpc('play')

    def stop(self):
        """ Stop playing the music. """
        self.mpc('stop')

    def next(self):
        """ Play the next track. """
        self.mpc('next')

    def prev(self):
        """ Play the prev track. """
        self.mpc('prev')

    def clear(self):
        """ Clear the playlist. """
        self.mpc('clear')

    def current_playing_filename(self) -> str:
        """ Return the current file being played with the path stripped out. """
        file_name = subprocess.run(
            [f"{self._wrapped_mpc()} current"], shell=True, capture_output=True, text=True).stdout
        return os.path.split(file_name)[1]

    def stream_url(self) -> str:
        return f"http://{self._host}:8000/mpd.mp3"

    def __str__(self):
        """ @override """
        return f"{super(MpdController, self).__str__()}, {self._host}:{self._port}"

    def mpc(self, command: str):
        """ Invoke mpc with the specified command"""
        subprocess.run([f"{self._wrapped_mpc()} {command}"], shell=True)

    def _wrapped_mpc(self) -> str:
        return f"mpc --host={self._host} --port={self._port}"
