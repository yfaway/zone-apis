from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable, Optional, cast

import websockets


class OpenHabWebSocketClient:
    """OpenHAB event WebSocket client.

    Connects to the OpenHAB event adapter at ws://<host>:<port>/ws/events.
    It subscribes to the default event topics and forwards events to a callback,
    filtering out messages that originated from the same client name.
    """

    def __init__(
        self,
        host: str,
        port: int,
        path: str = '/ws/events',
        *,
        client_name: str = 'ZoneApi',
        ignored_non_item_events: bool = True,
        on_event: Optional[Callable[[dict[str, Any]], Any]] = None,
        ping_interval: int = 5,
        ping_timeout: int = 5,
        topics: Optional[list[str]] = None,
    ):
        self.host = host
        self.port = port
        self.path = path
        self.client_name = client_name
        self.ignored_non_item_events = ignored_non_item_events
        self.on_event = on_event
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.topics = topics or ['smarthome/items/#', 'smarthome/events']

        self.uri = f'ws://{self.host}:{self.port}{self.path}'
        self._websocket = None
        self._listener_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def connect(self) -> None:
        """Connect to the server and subscribe to the selected topics."""
        if self._websocket is not None:
            return

        self._websocket = await websockets.connect(
            self.uri,
            ping_interval=self.ping_interval,
            ping_timeout=None,
            close_timeout=None,
        )

        for topic in self.topics:
            await self._websocket.send(json.dumps({
                'type': 'subscribe',
                'topic': topic,
            }))

        self._stop_event.clear()
        self._listener_task = asyncio.create_task(self._listen_forever())

    async def disconnect(self) -> None:
        self._stop_event.set()
        if self._listener_task is not None:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None

    async def _listen_forever(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self._websocket is None:
                    await self.connect()
                    continue

                raw = await self._websocket.recv()
                if not raw:
                    continue

                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    message = {'raw': raw}
                    print("Failed to decode JSON message:", raw)

                source = message.get('source') or None
                if source is not None and source.strip() == self.client_name:
                    continue

                event_type: str = cast(str, message.get('type')) or ""
                if event_type is not None and self.ignored_non_item_events \
                        and not event_type.strip().startswith('Item'):  
                    continue

                if self.on_event is not None:
                    result = self.on_event(message)
                    if asyncio.iscoroutine(result):
                        await result
                else:
                    print(json.dumps(message, indent=2, sort_keys=True))
            except websockets.ConnectionClosed:
                # Reconnect if the connection is closed unexpectedly
                if not self._stop_event.is_set():
                    await asyncio.sleep(2)
                    try:
                        await self.connect()
                    except Exception as e:
                        print("Failed to reconnect:", e)
                break
            except asyncio.CancelledError as e:
                print("Listener task cancelled:", e)
                break
            except Exception as e:
                print("Error in listener:", e)
                if not self._stop_event.is_set():
                    await asyncio.sleep(1)

    async def send_command(self, item_name: str, value_type: str, value: Any) -> None:
        """Send a command event to OpenHAB using the configured client name."""
        if self._websocket is None:
            raise RuntimeError('WebSocket is not connected. Call connect() first.')

        payload = f"{{\"value\": {json.dumps(value)}, \"type\": \"{value_type}\"}}"

        message = {
            'type': 'ItemCommandEvent',
            'source': self.client_name,
            'topic': f"openhab/items/{item_name}/command",
            'payload': payload,
        }
        try:
            await self._websocket.send(json.dumps(message))
        except websockets.ConnectionClosed:
            if not self._stop_event.is_set():
                await asyncio.sleep(2)
                try:
                    await self.connect()
                except Exception as e:
                    print("Failed to reconnect:", e)


    async def run_forever(self) -> None:
        """Convenience loop to keep the WebSocket connection alive."""
        await self.connect()
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(1)
        finally:
            await self.disconnect()


async def main() -> None:
    client = OpenHabWebSocketClient(
        host='192.168.0.1',
        port=8080,
        client_name='ZoneApi',
        on_event=lambda event: print('received:', json.dumps(event, sort_keys=True)),
    )
    await client.connect()

    # Example of sending an event to OpenHAB.
    #client.generate({'itemName': 'TestSwitch', 'value': 'ON'}, topic='smarthome/items')

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
