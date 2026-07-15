"""Custom field discovery, schema extension, and record flattening for CallHub."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from hotglue_singer_sdk import typing as th

from tap_callhub.client import CallHubStream

PROBE_SCHEMA = {"type": "object", "properties": {}}

FIELD_TYPE_TO_TH = {
    "text": th.StringType,
    "number": th.NumberType,
    "boolean": th.BooleanType,
    "multichoice": th.StringType,
}


def field_type_to_th(field_type: Optional[str]) -> Any:
    return FIELD_TYPE_TO_TH.get((field_type or "text").lower(), th.StringType)


def custom_field_definitions_by_id(
    definitions: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    return {str(defn["id"]): defn for defn in definitions if defn.get("id") is not None}


def extend_properties_with_custom_fields(
    properties: List[Any],
    definitions: List[Dict[str, Any]],
) -> List[Any]:
    """Append custom field properties, skipping names that collide with base fields."""
    extended = list(properties)
    existing_names = {prop.name for prop in extended}
    for definition in definitions:
        name = definition.get("name")
        if not name or name in existing_names:
            continue
        extended.append(
            th.Property(name, field_type_to_th(definition.get("field_type")))
        )
        existing_names.add(name)
    return extended


def fetch_definitions(stream: CallHubStream) -> List[Dict[str, Any]]:
    """Return custom field definitions from the CallHub API."""
    url = f"{stream.url_base}/v1/custom_fields/"
    prepared_request = stream.build_prepared_request("GET", url)
    decorated_request = stream.request_decorator(stream._request)
    response = decorated_request(prepared_request, None)
    payload = response.json()
    if isinstance(payload, list):
        return payload
    return []


def _parse_custom_fields_value(raw_value: Any) -> Dict[str, Any]:
    if raw_value is None:
        return {}
    if isinstance(raw_value, dict):
        return raw_value
    if isinstance(raw_value, str):
        raw_value = raw_value.strip()
        if not raw_value:
            return {}
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _coerce_number_value(value: Any) -> Any:
    try:
        if isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str) and "." in value:
            return float(value)
        return int(value)
    except (TypeError, ValueError):
        return value


def _coerce_boolean_value(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return bool(value)


def coerce_custom_field_value(value: Any, field_type: Optional[str]) -> Any:
    normalized_type = (field_type or "text").lower()
    if value is None:
        return None
    if normalized_type == "number":
        return _coerce_number_value(value)
    if normalized_type == "boolean":
        return _coerce_boolean_value(value)
    return value


def flatten_custom_fields(
    row: Dict[str, Any],
    definitions_by_id: Dict[str, Dict[str, Any]],
    reserved_names: set[str],
) -> None:
    """Promote custom field values to top-level properties using readable names."""
    raw_values = _parse_custom_fields_value(row.pop("custom_fields", None))
    for field_id, value in raw_values.items():
        definition = definitions_by_id.get(str(field_id))
        if not definition:
            continue
        name = definition.get("name")
        if not name or name in reserved_names:
            continue
        row[name] = coerce_custom_field_value(value, definition.get("field_type"))
