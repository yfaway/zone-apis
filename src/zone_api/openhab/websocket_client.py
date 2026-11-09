from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Optional, cast
import websockets

logger = logging.getLogger('ZoneApis')


class OpenHabWebSocketClient:
    """OpenHAB event WebSocket client.

    Connects to the OpenHAB event adapter at ws://<host>:<port>/ws/events.
    It subscribes to the default event topics and forwards events to a callback, filtering out messages that originated
    from the same client name.
    An OpenHab-layer keep-alive ping message is send periodically based on the provided ping interval.
    Messages to be sent to OpenHab aer queued to ensure correct transmission in multi-threaded env, which is the case
    due to usage of the Scheduling library within zone_api.
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
    ):
        self.host = host
        self.port = port
        self.path = path
        self.client_name = client_name
        self.ignored_non_item_events = ignored_non_item_events
        self.on_event = on_event
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        self.uri = f'ws://{self.host}:{self.port}{self.path}'
        self._websocket = None
        self._listener_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._sender_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._send_queue: asyncio.Queue[tuple[str, asyncio.Future[None]]] = asyncio.Queue()

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

        self._stop_event.clear()
        self._sender_task = asyncio.create_task(self._send_queued_messages())
        self._listener_task = asyncio.create_task(self._listen_forever())
        self._heartbeat_task = asyncio.create_task(self._send_heartbeat())

    async def disconnect(self) -> None:
        self._stop_event.set()
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        if self._sender_task is not None:
            self._sender_task.cancel()
            try:
                await self._sender_task
            except asyncio.CancelledError:
                pass
            self._sender_task = None

        while not self._send_queue.empty():
            _, completion = self._send_queue.get_nowait()
            if not completion.done():
                completion.cancel()
            self._send_queue.task_done()

        if self._listener_task is not None:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None

    async def _send_queued_messages(self) -> None:
        """Serialize websocket writes through a single queue consumer."""
        while True:
            serialized_message, completion = await self._send_queue.get()
            try:
                if self._websocket is None:
                    raise RuntimeError('WebSocket is not connected.')
                await self._websocket.send(serialized_message)
            except asyncio.CancelledError:
                if not completion.done():
                    completion.cancel()
                raise
            except Exception as error:
                if not completion.done():
                    completion.set_exception(error)
            else:
                if not completion.done():
                    completion.set_result(None)
            finally:
                self._send_queue.task_done()

    async def _send_heartbeat(self) -> None:
        """Send OpenHAB heartbeat messages at the configured ping interval."""
        while not self._stop_event.is_set():
            await asyncio.sleep(self.ping_interval)
            if self._websocket is None:
                continue

            message = {
                'type': 'WebSocketEvent',
                'topic': 'openhab/websocket/heartbeat',
                'payload': 'PING',
                'source': self.client_name
            }
            try:
                await self._safe_send(message)
            except websockets.ConnectionClosed:
                logger.error("WebSocket closed while sending heartbeat")
                return

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
                    logger.error(f"Failed to decode JSON message: {raw}")

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
                #else:
                #    print(json.dumps(message, indent=2, sort_keys=True))
            except websockets.ConnectionClosed:
                # Reconnect if the connection is closed unexpectedly
                if not self._stop_event.is_set():
                    await asyncio.sleep(2)
                    try:
                        await self.connect()
                    except Exception as e:
                        logger.error(f"Failed to reconnect: {e}")
                break
            except asyncio.CancelledError as e:
                logger.error(f"Listener task cancelled: {e}")
                break
            except Exception as e:
                logger.error(f"Error in listener: {e}")
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
        #logger.info(f"{json.dumps(message)}")
        try:
            await self._safe_send(message)
        except websockets.ConnectionClosed:
            if not self._stop_event.is_set():
                await asyncio.sleep(2)
                try:
                    await self.connect()
                except Exception as e:
                    logger.error(f"Failed to reconnect: {e}")


    async def _safe_send(self, message_dict):
        """
        Queue a serialized message and wait until the websocket writer sends it.
        """

        if self._websocket is None or self._sender_task is None:
            raise RuntimeError('WebSocket is not connected. Call connect() first.')

        loop = asyncio.get_running_loop()
        completion = loop.create_future()
        await self._send_queue.put((json.dumps(message_dict), completion))
        await completion