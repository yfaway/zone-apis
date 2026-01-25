from zone_api.core.action import action, Action
from zone_api.core.devices.chromecast_audio_sink import ChromeCastAudioSink
from zone_api.core.devices.mpd_chromecast_audio_sink import MpdChromeCastAudioSink
from zone_api.core.devices.mpd_device import MpdDevice
from zone_api.core.event_info import EventInfo
from zone_api.core.zone_event import ZoneEvent
from zone_api.music_streams import MusicStreams


@action(events=[ZoneEvent.TIMER, ZoneEvent.PLAYER_PLAY, ZoneEvent.PLAYER_PAUSE, ZoneEvent.PLAYER_NEXT,
                ZoneEvent.PLAYER_PREVIOUS],
        devices=[MpdDevice])
class ControlMpdMusicPlayer(Action):
    """
    Handle the events of a Player item via MpdDevice. The mode of operation is like this:
      1. A speaker device such as a chromecast, is configured to listen to a music stream.
      2. The user can then manage that stream (pause, play, skip to the next / prev song) via a UI component.
      3. This action class listens to those events and control the mpd server via the MpdDevice class.

    The concept of pause is different between a speaker and the server. For a speaker, pause means stop output the
    stream to that particular speaker; stream is still there for other clients. But for a server such as mdp, it means
    stop reading the music files and thus the entire stream is offline for all clients. This class stops both the
    speaker and the mdp server.

    This action also starts a timer to check every 15 minutes if there is any active Chromecast. If there is none, it
    will stop the MPD streamer process to avoid wearing out the SSD.
    """

    def on_startup(self, event_info: EventInfo):
        scheduler = event_info.get_zone_manager().get_scheduler()
        scheduler.every(15).minutes.do(lambda: self.on_action(self.create_timer_event_info(event_info)))

    # noinspection PyMethodMayBeStatic
    def on_action(self, event_info: EventInfo):
        event_type = event_info.get_event_type()
        zone = event_info.get_zone()

        # There could events from a different player (e.g. the Chromecast player).
        if event_type != ZoneEvent.TIMER and not isinstance(event_info.get_device(), MpdDevice):
            return False

        if event_type == ZoneEvent.TIMER:
            controller: MpdDevice = zone.get_first_device_by_type(MpdDevice)
        else:
            controller: MpdDevice = event_info.get_device()

        if controller is None:
            self.log_error("No MDP controller found.")
            return False

        if event_type == ZoneEvent.TIMER:
            chrome_casts = event_info.get_zone_manager().get_devices_by_type(ChromeCastAudioSink)
            if not any(c.is_active() for c in chrome_casts):
                if controller.is_playing():
                    controller.stop()
                    self.log_info("Stopped MPD streamer service.")

        elif event_type == ZoneEvent.PLAYER_NEXT:
            controller.next()
        elif event_type == ZoneEvent.PLAYER_PREVIOUS:
            controller.prev()
        elif event_type == ZoneEvent.PLAYER_PLAY:
            chromecast_player: MpdChromeCastAudioSink = zone.get_first_device_by_type(MpdChromeCastAudioSink)
            chromecast_player.play_stream(controller.stream_url(), None, controller.music_category())
        elif event_type == ZoneEvent.PLAYER_PAUSE:
            controller.stop()

            chromecast_player: ChromeCastAudioSink = zone.get_first_device_by_type(MpdChromeCastAudioSink)
            chromecast_player.pause()

        return True
