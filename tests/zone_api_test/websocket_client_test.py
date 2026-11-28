import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from zone_api.openhab.websocket_client import OpenHabWebSocketClient


class OpenHabWebSocketClientTest(unittest.TestCase):
    def test_submit_event_handler_warnsOnceAtEightyPercentWorkerUtilization(self):
        client = OpenHabWebSocketClient('localhost', 8080)
        client._event_executor = ThreadPoolExecutor(
            max_workers=client._event_worker_count,
            thread_name_prefix='test-openhab-event',
        )
        handler_count = 0
        handler_count_lock = threading.Lock()
        threshold_reached = threading.Event()
        release_handlers = threading.Event()

        def blocking_handler(_event):
            nonlocal handler_count
            with handler_count_lock:
                handler_count += 1
                if handler_count >= client._event_worker_warning_count:
                    threshold_reached.set()
            release_handlers.wait()

        try:
            with self.assertLogs('ZoneApis', level='WARNING') as logs:
                for _ in range(client._event_worker_count):
                    client.submit_event_handler(blocking_handler, None)

                self.assertTrue(threshold_reached.wait(timeout=5))
                release_handlers.set()
                client._event_executor.shutdown(wait=True)
                client._event_executor = None

            warnings = [message for message in logs.output if 'near saturation' in message]
            self.assertEqual(1, len(warnings))
            self.assertIn('8/10 workers active', warnings[0])
        finally:
            release_handlers.set()
            if client._event_executor is not None:
                client._event_executor.shutdown(wait=True)


if __name__ == '__main__':
    unittest.main()
