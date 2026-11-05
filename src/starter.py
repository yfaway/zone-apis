import asyncio
import json
import logging
import logging.config
import os
import yaml
# from importlib import reload
# from zone_api import zone_parser
# reload(zone_parser)

from openhab.websocket_client import OpenHabWebSocketClient
from zone_api import zone_parser as zp
from zone_api import platform_encapsulator as pe
from zone_api.core.immutable_zone_manager import ImmutableZoneManager


class Starter():
    def __init__(self):
        self._configure_logging()
        self._config = self._load_configuration()
        self._client: OpenHabWebSocketClient
        self._count = 0
        self._zm: ImmutableZoneManager

        self._configure_zone_manager()

    def _configure_logging(self):
        logging_config_file = '/home/yf/git/zone-apis/habapp/logging.yml'
        if not os.path.exists(logging_config_file):
            logging_config_file = './habapp/logging.yml'
            if not os.path.exists(logging_config_file):
                raise ValueError("Missing habapp/logging.yml file.")

        with open(logging_config_file, 'r') as file:
            config = yaml.safe_load(file) or {}

        if config:
            if 'version' not in config:
                config['version'] = 1
            logging.config.dictConfig(config)
            logger = logging.getLogger('ZoneApis')
            logger.info("Loaded logging configuration from '%s'", logging_config_file)

    def _load_configuration(self):
        # When running on the PI
        config_file = '/home/yf/git/zone-apis/habapp/zone-api-config.yml'
        if not os.path.exists(config_file):  # In development machine
            config_file = './habapp/zone-api-config.yml'
            if not os.path.exists(config_file):
                raise ValueError("Missing zone-api-config.yml file.")

        pe.log_info(f"Reading zone-api configuration from '{config_file}'")

        with open(config_file, 'r') as file:
            return yaml.safe_load(file)

    def _configure_zone_manager(self):
        self._zm = zp.parse(self._config)
        pe.add_zone_manager_to_context(self._zm)

        device_count = 0
        for zone in self._zm.get_zones():
            device_count += len(zone.get_devices())

        pe.log_info(f"Loaded {self._zm.get_zones().__len__()} zones and {device_count} devices.")
        pe.log_debug(str(self._zm))

    async def event_dispatcher(self, event):
        #if 'FF_Foyer_LightSwitch' in topic:
        #    print(f"Received event for FF_Foyer_LightSwitch: {event}")
        #self._count += 1
        #if self._count == 1:
        #    await self._client.send_command('FF_Foyer_LightSwitch', 'OnOff', 'ON')
        event_type = event.get('type')
        topic = event.get('topic')
        if event_type == 'ItemStateUpdatedEvent':
            tokens = topic.split('/')
            if len(tokens) == 4:
                item_name = tokens[2]
                payload = event.get('payload', None)
                if payload is not None:
                    json_obj = json.loads(payload)
                    item_state = json_obj.get('value')

                    item = self._zm.get_item(item_name)
                    if item:
                        item.update_value_from_openhab(item_state)
                        pe.log_info(f"Received state update for item '{item_name}': {item_state}")


        #print(f"event: {event}")
        
    async def establish_websocket_connection(self):
        self._client = OpenHabWebSocketClient(
            self._config['system']['openhab']['host'],
            self._config['system']['openhab']['port'],
            client_name='ZoneApi',
            on_event=self.event_dispatcher,
            ignored_non_item_events=True,)

        await self._client.connect()

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await self._client.disconnect()



    @staticmethod
    def _test_text_to_speech(msg: str):
        pe.play_text_to_speech_message('chromecast:audio:greatRoom', msg)

    @staticmethod
    def _test_invoking_action(zm: ImmutableZoneManager):
        from zone_api.core.event_info import EventInfo
        from zone_api.core.zone_event import ZoneEvent
        from zone_api.core.zone import Zone
        from zone_api.core.devices.motion_sensor import MotionSensor
        from zone_api.core.actions.announce_morning_weather_and_play_music import AnnounceMorningWeatherAndPlayMusic
        from zone_api.core.map_parameters import MapParameters

        kitchen: Zone = next((x for x in zm.get_internal_zones() if x.name == 'Kitchen'), None)
        event_info = EventInfo(ZoneEvent.MOTION, kitchen.get_first_device_by_type(MotionSensor).get_item(), kitchen,
                               pe.get_zone_manager_from_context(), pe.get_event_dispatcher())
        pe.log_info("Invoking action...")
        AnnounceMorningWeatherAndPlayMusic(MapParameters({})).on_action(event_info)


async def main() -> None:
    instance = Starter()
    await instance.establish_websocket_connection()


if __name__ == '__main__':
    asyncio.run(main())