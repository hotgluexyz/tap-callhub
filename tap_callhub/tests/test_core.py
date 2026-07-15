"""Tests standard tap features using the built-in SDK tests library."""

import json
import os
from unittest.mock import Mock

import pytest
from hotglue_singer_sdk.testing import get_standard_tap_tests

from tap_callhub.tap import TapCallhub

_SECRETS_CONFIG = os.path.join(os.path.dirname(__file__), "../../.secrets/config.json")


@pytest.fixture
def sample_config():
    if not os.path.exists(_SECRETS_CONFIG):
        pytest.skip("Secrets file not found; skipping integration tests.")
    with open(_SECRETS_CONFIG) as config_file:
        config = json.load(config_file)
    if "api_key" in config and "api_token" not in config:
        config["api_token"] = config.pop("api_key")
    return config


@pytest.fixture
def discovered_stream(sample_config):
    return TapCallhub(config=sample_config).discover_streams()[0]


def test_standard_tap_tests(sample_config):
    tests = get_standard_tap_tests(TapCallhub, config=sample_config)
    for test in tests:
        test()


def test_get_next_page_token_parses_page_from_next_url(discovered_stream):
    response = Mock()
    response.json.return_value = {
        "next": "https://api-na1.callhub.io/v1/contacts/?page=2&page_size=2",
    }

    assert discovered_stream.get_next_page_token(response, None) == 2


def test_get_next_page_token_returns_none_when_exhausted(discovered_stream):
    response = Mock()
    response.json.return_value = {"next": None}

    assert discovered_stream.get_next_page_token(response, None) is None


def test_contacts_pagination(discovered_stream):
    discovered_stream.page_size = 2

    records = list(discovered_stream.get_records(None))
    record_ids = [record["id"] for record in records]

    assert len(records) >= 5
    assert len(record_ids) == len(set(record_ids))


def test_custom_field_name_collision_skips_reserved_names():
    from tap_callhub.custom_fields import (
        custom_field_definitions_by_id,
        extend_properties_with_custom_fields,
        flatten_custom_fields,
    )
    from tap_callhub.streams import ContactsStream

    base_properties = ContactsStream.base_properties()
    reserved_names = {prop.name for prop in base_properties}
    definitions = [
        {"id": 1, "name": "email", "field_type": "text"},
        {"id": 2, "name": "notes", "field_type": "text"},
    ]

    extended = extend_properties_with_custom_fields(base_properties, definitions)
    property_names = {prop.name for prop in extended}

    assert "email" in property_names
    assert "notes" in property_names
    assert len(property_names) == len(base_properties) + 1

    row = {
        "email": "standard-email@hotglue.test",
        "custom_fields": '{"1": "custom-email@hotglue.test", "2": "my notes"}',
    }
    flatten_custom_fields(
        row,
        custom_field_definitions_by_id(definitions),
        reserved_names,
    )

    assert row["email"] == "standard-email@hotglue.test"
    assert "cf_email" not in row
    assert row["notes"] == "my notes"
