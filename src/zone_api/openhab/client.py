from __future__ import annotations
from typing import Any, Dict, List
import requests
from .oh_models import OpenHabBaseItem, item_from_payload


class OpenHabClient:
    """Minimal client for the OpenHAB REST item API."""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def get_items(
        self,
        *,
        metadata: str = '.*',
        recursive: bool = False,
        parents: bool = False,
        static_data_only: bool = False,
    ) -> List[OpenHabBaseItem]:
        url = f"{self.base_url}/rest/items"
        params: Dict[str, Any] = {
            'metadata': metadata,
            'recursive': 'true' if recursive else 'false',
            'parents': 'true' if parents else 'false',
            'staticDataOnly': 'true' if static_data_only else 'false',
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, list):
            raise ValueError(f"Unexpected response from OpenHAB REST API: {payload!r}")

        return [item_from_payload(item) for item in payload]


def fetch_items_from_endpoint(
    host: str,
    port: int,
    *,
    metadata: str = '.*',
    recursive: bool = False,
    parents: bool = False,
    static_data_only: bool = False,
    timeout: int = 10,
) -> List[OpenHabBaseItem]:
    client = OpenHabClient(f"http://{host}:{port}", timeout=timeout)
    return client.get_items(
        metadata=metadata,
        recursive=recursive,
        parents=parents,
        static_data_only=static_data_only,
    )