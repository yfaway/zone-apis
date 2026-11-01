from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from .models import BaseItem, item_from_payload


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
    ) -> List[BaseItem]:
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
    url: str = 'http://ip:8080/rest/items',
    *,
    metadata: str = '.*',
    recursive: bool = False,
    parents: bool = False,
    static_data_only: bool = False,
    timeout: int = 10,
) -> List[BaseItem]:
    client = OpenHabClient(url.rsplit('/rest/items', 1)[0], timeout=timeout)
    return client.get_items(
        metadata=metadata,
        recursive=recursive,
        parents=parents,
        static_data_only=static_data_only,
    )


if __name__ == '__main__':
    items = fetch_items_from_endpoint(
        'http://ip:8080/rest/items?metadata=.%2A&recursive=false&parents=false&staticDataOnly=false'
    )
    for item in items[:5]:
        print(item)
