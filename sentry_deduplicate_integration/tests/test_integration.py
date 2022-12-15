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


@pytest.fixture
def hub(integration):
    client = sentry_sdk.Client(integrations=[integration], transport=mock.MagicMock())
    sentry_sdk.Hub.current.bind_client(client)
    yield


def test_max_events_per_minute_reached(integration):
    raise_error_1(integration, expected_send=True)
    raise_error_1(integration, expected_send=False)


def test_should_send_distinct_events(integration):
    raise_error_1(integration, expected_send=True)
    raise_error_2(integration, expected_send=True)


def test_redis_raise_exception(mocker, integration):
    mocker.patch.object(integration.redis_client, "pipeline", side_effect=ValueError)
    raise_error_1(integration, expected_send=True)
    raise_error_1(integration, expected_send=True)


def test_processor_called(mocker, hub, integration):
    should_send_mock = mocker.patch.object(
        integration, "should_send", return_value=True
    )
    try:
        1 / 0
    except ZeroDivisionError as e:
        sentry_sdk.capture_exception(e)
    should_send_mock.assert_called_once()


def test_processor_called_and_should_not_send(mocker, hub, integration):
    should_not_send_mock = mocker.patch.object(
        integration, "should_send", return_value=False
    )
    try:
        1 / 0
    except ZeroDivisionError as e:
        sentry_sdk.capture_exception(e)
    should_not_send_mock.assert_called_once()


def test_processor_without_hint():
    event = mock.sentinel
    assert SentryDeduplicateIntegration.processor(event, hint=None) == event


def test_processor_with_hint_without_exc_info():
    event = mock.sentinel
    assert SentryDeduplicateIntegration.processor(event, hint={}) == event
