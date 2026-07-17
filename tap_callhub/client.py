"""REST client handling, including CallHubStream base class."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

import requests
from hotglue_singer_sdk.authenticators import APIKeyAuthenticator
from hotglue_singer_sdk.streams import RESTStream
from memoization import cached


class CallHubStream(RESTStream):
    """CallHub stream class (base)."""

    records_jsonpath = "$.results[*]"
    primary_keys = ["id"]
    replication_key = None
    page_size = 1000

    @property
    def url_base(self) -> str:
        return self.config["api_base_url"].rstrip("/")

    @property
    @cached
    def authenticator(self) -> APIKeyAuthenticator:
        return APIKeyAuthenticator(
            stream=self,
            key="Authorization",
            value=f"Token {self.config['api_token']}",
            location="header",
        )

    def get_url(self, context: Optional[dict]) -> str:
        return f"{self.url_base}/v1/{self.path}/"

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page_size": self.page_size}
        if next_page_token is not None:
            params["page"] = next_page_token
        return params

    def get_next_page_token(
        self,
        response: requests.Response,
        previous_token: Optional[Any],
    ) -> Optional[Any]:
        next_url = response.json().get("next")
        if not next_url:
            return None
        page_values = parse_qs(urlparse(next_url).query).get("page")
        if not page_values:
            return None
        try:
            return int(page_values[0])
        except (TypeError, ValueError):
            return None
