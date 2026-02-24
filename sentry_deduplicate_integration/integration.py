import time
from contextvars import ContextVar

import sentry_sdk
from sentry_sdk import VERSION as SENTRY_VERSION
from sentry_sdk.integrations import Integration

_sentry_v2 = int(SENTRY_VERSION.split(".")[0]) >= 2


class SentryDeduplicateIntegration(Integration):
    identifier = "sentry-deduplicate-integration"

    def __init__(self, redis_factory, *, max_events_per_minute=10):
        self.redis_factory = redis_factory
        self._ctx = ContextVar("redis-client")
        self.max_events_per_minute = max_events_per_minute

    @property
    def redis_client(self):
        client = self._ctx.get(None)
        if client is None:
            client = self.redis_factory()
            self._ctx.set(client)
        return client

    @staticmethod
    def setup_once():
        if _sentry_v2:
            sentry_sdk.get_global_scope().add_event_processor(
                SentryDeduplicateIntegration._processor
            )
        else:
            from sentry_sdk.scope import add_global_event_processor

            add_global_event_processor(SentryDeduplicateIntegration._processor)

    @staticmethod
    def _processor(event, hint):
        if hint is None:
            return event

        exc_info = hint.get("exc_info")
        if exc_info is None:
            return event

        if _sentry_v2:
            integration = sentry_sdk.get_client().get_integration(
                SentryDeduplicateIntegration
            )
        else:
            integration = sentry_sdk.Hub.current.get_integration(
                SentryDeduplicateIntegration
            )

        if integration is None or integration.should_send(exc_info):
            return event

        return None

    processor = _processor

    def should_send(self, exc_info):
        key = self._build_key(exc_info)
        try:
            pipeline = self.redis_client.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, 60)
            count, _ = pipeline.execute()
            return int(count) <= self.max_events_per_minute
        except Exception:
            return True

    def _build_key(self, exc_info):
        lines = self._get_exc_filenames_and_lines(exc_info)
        key = "|".join(f"{fname}:{lineno}" for fname, lineno in lines)
        key = f"{key}:{int(time.time() // 60)}"
        return key

    def _get_exc_filenames_and_lines(self, exc_info):
        _, _, exc_tb = exc_info
        while exc_tb is not None:
            yield (exc_tb.tb_frame.f_code.co_filename, exc_tb.tb_lineno)
            exc_tb = exc_tb.tb_next
