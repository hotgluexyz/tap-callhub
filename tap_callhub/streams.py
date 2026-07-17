"""Stream type classes for tap-callhub."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hotglue_singer_sdk import Tap, typing as th

from tap_callhub.client import CallHubStream
from tap_callhub.custom_fields import (
    PROBE_SCHEMA,
    extend_properties_with_custom_fields,
    fetch_definitions,
    flatten_custom_fields,
)


class ContactsStream(CallHubStream):
    """Contacts stream with dynamically discovered custom field properties."""

    name = "contacts"
    path = "contacts"

    @classmethod
    def base_properties(cls) -> List[Any]:
        return [
            th.Property("url", th.StringType),
            th.Property("id", th.IntegerType),
            th.Property("pk_str", th.StringType),
            th.Property("owner", th.StringType),
            th.Property("phonebooks", th.ArrayType(th.StringType)),
            th.Property("contact", th.StringType),
            th.Property("mobile", th.StringType),
            th.Property("last_name", th.StringType),
            th.Property("agent", th.StringType),
            th.Property("first_name", th.StringType),
            th.Property("country_code", th.StringType),
            th.Property("email", th.StringType),
            th.Property("created_date", th.DateTimeType),
            th.Property("address", th.StringType),
            th.Property("city", th.StringType),
            th.Property("tags", th.ArrayType(th.StringType)),
            th.Property("street_address_line1", th.StringType),
            th.Property("state", th.StringType),
            th.Property("zipcode", th.StringType),
            th.Property("company_name", th.StringType),
            th.Property("company_website", th.StringType),
            th.Property("job_title", th.StringType),
            th.Property("language", th.StringType),
        ]

    @classmethod
    def fetch_custom_field_definitions(cls, tap: Tap) -> List[Dict[str, Any]]:
        return fetch_definitions(cls(tap=tap, schema=PROBE_SCHEMA))

    @classmethod
    def build_schema(cls, definitions: List[Dict[str, Any]]) -> dict:
        properties = extend_properties_with_custom_fields(
            cls.base_properties(),
            definitions,
        )
        return th.PropertiesList(*properties).to_dict()

    def post_process(self, row: Dict[str, Any], context: Optional[dict]) -> Optional[dict]:
        row = super().post_process(row, context)
        if row is None:
            return None
        reserved_names = {prop.name for prop in self.base_properties()}
        flatten_custom_fields(
            row,
            self._tap.custom_field_definitions_by_id,
            reserved_names,
        )
        return row
