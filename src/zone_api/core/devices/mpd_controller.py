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

    INTERVAL_IN_MINUTES = 0.25

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

        self._play_status_job = None
        self._title_item = None

    def shuffle_and_play(self, file_name_pattern: Union[str | None] = None, item=None):
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

        # let's start a timer job to track the playing status
        if item is not None:
            def update_play_status():
                tokens = self.current_playing_status()
                if tokens:
                    pe.set_string_value(item, f"{tokens[0]} {tokens[1]}")
                else:
                    pe.set_string_value(item, "")

            scheduler = pe.get_zone_manager_from_context().get_scheduler()
            self._play_status_job = scheduler.every(MpdController.INTERVAL_IN_MINUTES).minutes.do(update_play_status)

            self._title_item = item

    def stop(self):
        """ Stop playing the music. """
        self.mpc('stop')

        # stop polling for the playing status
        if self._play_status_job:
            scheduler = pe.get_zone_manager_from_context().get_scheduler()
            scheduler.cancel_job(self._play_status_job)
            self._play_status_job = None

            if self._title_item is not None:
                pe.set_string_value(self._title_item, '')
                self._title_item = None

    def next(self):
        """ Play the next track. """
        self.mpc('next')

    def prev(self):
        """ Play the prev track. """
        self.mpc('prev')

    def clear(self):
        """ Clear the playlist. """
        self.mpc('clear')

    def current_playing_status(self) -> Union[list[str], None]:
        """
        If in playing mode, return an array of 2 items: the current file being played with the path stripped outi, and
        the position in the playlist (e.g. "2/75"). Else, return None.
        """
        status = subprocess.run(
            [f"{self._wrapped_mpc()} status"], shell=True, capture_output=True, text=True).stdout
        if "[playing]" in status:
            lines = status.split("\n")
            file_nam = os.path.split(lines[0])[1]
            position = lines[1].split(' ')[1]

            return [position, file_nam]

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
