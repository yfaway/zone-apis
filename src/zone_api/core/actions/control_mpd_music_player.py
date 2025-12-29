from zone_api.core.action import action, Action
from zone_api.core.devices.mpd_chromecast_audio_sink import MpdChromeCastAudioSink
from zone_api.core.devices.mpd_controller import MpdController
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent


@action(events=[ZoneEvent.PLAYER_PLAY, ZoneEvent.PLAYER_PAUSE, ZoneEvent.PLAYER_NEXT, ZoneEvent.PLAYER_PREVIOUS],
        devices=[MpdChromeCastAudioSink])
class ControlMpdMusicPlayer(Action):
    """
    The next, prev, play and pause events invoke the equivalent mpc command.
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
            device.play_stream(controller.stream_url())
        elif event_type == ZoneEvent.PLAYER_PAUSE:
            controller.stop()

        return True
