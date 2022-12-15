import sys
from unittest import mock

import pytest
import redislite
import sentry_sdk

from sentry_deduplicate_integration import SentryDeduplicateIntegration


def raise_error_1(integration, expected_send):
    try:
        str.foo
    except AttributeError:
        assert_should_send(integration, expected_send)


def raise_error_2(integration, expected_send):
    try:
        1 / 0
    except ZeroDivisionError:
        assert_should_send(integration, expected_send)


def assert_should_send(integration, expected):
    should_send = integration.should_send(sys.exc_info())
    assert should_send is expected


@pytest.fixture
def integration():
    return SentryDeduplicateIntegration(
        redis_factory=redislite.Redis,
        max_events_per_minute=1,
    )


def test_max_events_per_minute_reached(integration):
    raise_error_1(integration, expected_send=True)
    raise_error_1(integration, expected_send=False)


def test_should_send_distinct_events(integration):
    raise_error_1(integration, expected_send=True)
    raise_error_2(integration, expected_send=True)


def test_processor_called(integration):
    with (
        sentry_sdk.Hub(),
        mock.patch.object(integration, "should_send", return_value=False) as should_send_mock
    ):
        client = sentry_sdk.Client(integrations=[integration], transport=mock.MagicMock())
        sentry_sdk.Hub.current.bind_client(client)
        try:
            1 / 0
        except ZeroDivisionError as e:
            sentry_sdk.capture_exception(e)

    should_send_mock.assert_called_once()
