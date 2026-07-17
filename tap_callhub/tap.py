"""CallHub tap class."""

from __future__ import annotations

from typing import List

from hotglue_singer_sdk import Stream, Tap
from hotglue_singer_sdk import typing as th

from tap_callhub.custom_fields import custom_field_definitions_by_id
from tap_callhub.streams import ContactsStream


class TapCallhub(Tap):
    """CallHub tap class."""

    name = "tap-callhub"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_token",
            th.StringType,
            required=True,
            description="CallHub API token shown in the account settings UI.",
        ),
        th.Property(
            "api_base_url",
            th.StringType,
            required=True,
            description="CallHub API base URL shown alongside the API token in the UI.",
        ),
    ).to_dict()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.custom_field_definitions_by_id: dict = {}

    def discover_streams(self) -> List[Stream]:
        """Return discovered streams with dynamic custom field schema properties."""
        definitions = ContactsStream.fetch_custom_field_definitions(self)
        self.custom_field_definitions_by_id = custom_field_definitions_by_id(definitions)
        return [
            ContactsStream(
                tap=self,
                schema=ContactsStream.build_schema(definitions),
            )
        ]


if __name__ == "__main__":
    TapCallhub.cli()
