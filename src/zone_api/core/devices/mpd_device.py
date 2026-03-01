import json
import os.path
import subprocess
from typing import Any, Hashable, Union

from zone_api import platform_encapsulator as pe
from zone_api.core.device import Device


class MpdDevice(Device):
    """
    Control the Music Player Daemon (mpd) via the accompanied mpc command.
    @see https://www.musicpd.org/
    """

    INTERVAL_IN_MINUTES = 0.25

    def __init__(self, player_item, host: str, port: int, predefined_category_item, custom_category_item):
        Device.__init__(self, player_item)

        self._predefined_category_item = predefined_category_item
        self._custom_category_item = custom_category_item

        self._host = host
        self._port = port

        self._play_status_job = None
        self._title_item = None

    def shuffle_and_play(self, file_name_pattern: Union[str | None] = None, item=None):
        """
        The following actions are performed:
          - Clear the play list queue
          - Filter the music library using simple pattern matching (grep), then shuffle and play the music.
        """
        pe.set_string_value(self._predefined_category_item, file_name_pattern)  # update the UI
        pe.set_string_value(self._custom_category_item, '')  # update the UI

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

        pe.change_player_state_to_play(self.get_item())

        # let's start a timer job to track the playing status
        if item is not None:
            def update_play_status():
                data = self.current_playing_status()
                if data is not None:
                    json_str = json.dumps(data)
                    pe.set_string_value(item, json_str)
                else:
                    pe.set_string_value(item, "{}")

            scheduler = pe.get_zone_manager_from_context().get_scheduler()
            self._play_status_job = scheduler.every(MpdDevice.INTERVAL_IN_MINUTES).minutes.do(update_play_status)

            self._title_item = item

    def stop(self):
        """ Stop playing the music. """
        self.mpc('stop')

        pe.change_player_state_to_pause(self.get_item())

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

    def is_playing(self) -> bool:
        return self.current_playing_status() is not None

    def current_playing_status(self) -> Union[dict[Hashable, Any], None]:
        """
        If in playing mode, return a dictionary containing the keys "current_song", "next_song", "current_position",
        "playlist_size". Else, return None.
        """
        status = subprocess.run(
            [f"{self._wrapped_mpc()} status"], shell=True, capture_output=True, text=True).stdout
        if "[playing]" in status:
            lines = status.split("\n")
            file_name = os.path.split(lines[0])[1]
            position_info = lines[1].split(' ')[1]
            position_info = position_info.replace("#", "")
            position_tokens = position_info.split('/')

            data = dict()
            data["current_song"] = file_name
            data["current_position"] = int(position_tokens[0])
            data["playlist_size"] = int(position_tokens[1])

            next_song = subprocess.run(
                [f"{self._wrapped_mpc()} queued"], shell=True, capture_output=True, text=True).stdout
            data["next_song"] = os.path.split(next_song)[1]
            return data
        else:
            return None

    def stream_url(self) -> str:
        return f"http://{self._host}:8000/mpd.mp3"

    def music_category(self) -> Union[str, None]:
        """
        Returns the specified music category via the custom category or the selected pre-defined category, or None if
        nothing is specified.
        """
        custom_value = pe.get_string_value(self._custom_category_item)
        if custom_value:
            return custom_value
        elif pe.get_string_value(self._predefined_category_item):
            return pe.get_string_value(self._predefined_category_item)
        else:
            return None

    def __str__(self):
        """ @override """
        return f"{super(MpdDevice, self).__str__()}, {self._host}:{self._port}"

    def mpc(self, command: str):
        """ Invoke mpc with the specified command"""
        subprocess.run([f"{self._wrapped_mpc()} {command}"], shell=True)

    def _wrapped_mpc(self) -> str:
        return f"mpc --host={self._host} --port={self._port}"
