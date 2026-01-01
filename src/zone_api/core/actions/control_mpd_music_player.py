from zone_api.core.action import action, Action
from zone_api.core.devices.mpd_chromecast_audio_sink import MpdChromeCastAudioSink
from zone_api.core.devices.mpd_controller import MpdController
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent


@action(events=[ZoneEvent.PLAYER_PLAY, ZoneEvent.PLAYER_PAUSE, ZoneEvent.PLAYER_NEXT, ZoneEvent.PLAYER_PREVIOUS],
        devices=[MpdChromeCastAudioSink])
class ControlMpdMusicPlayer(Action):
    """
    Handle the events of a Player item via the MpdController device. The mode of operation is like this:
      1. A speaker device such as a chromecast, is configured to listen to a music stream.
      2. The user can then manage that stream (pause, play, skip to the next / prev song) via a UI component.
      3. This action class listens to those events and control the mpd server via the MpdController class.

    The concept of pause is different between a speaker and the server. For a speaker, pause means stop output the
    stream to that particular speaker; stream is still there for other clients. But for a server such as mdp, it means
    stop reading the music files and thus the entire stream is offline for all clients. This class stops both the
    speaker and the mdp server.
    """

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info: EventInfo):
        device: MpdChromeCastAudioSink = event_info.get_device()
        event_type = event_info.get_event_type()

        controller: MpdController = event_info.get_zone_manager().get_first_device_by_type(MpdController)
        if controller is None:
            self.log_error("No MDP controller found.")
            return False

        if event_type == ZoneEvent.PLAYER_NEXT:
            controller.next()
        elif event_type == ZoneEvent.PLAYER_PREVIOUS:
            controller.prev()
        elif event_type == ZoneEvent.PLAYER_PLAY:
            device.play_stream(controller.stream_url(), category=device.music_category())
        elif event_type == ZoneEvent.PLAYER_PAUSE:
            controller.stop()

        return True
