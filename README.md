# sentry-deduplicate-integration

Sentry integration to rate-limit duplicated errors, using redis to sync error
count and identify duplications.

## Install

Install it from PyPI:

```bash
pip install sentry-deduplicate-integration
```

## Configure

Add the integration to your sentry_sdk initialization.

```python
import redis
from sentry_deduplicate_integration import SentryDeduplicateIntegration

sentry_sdk.init(
    integrations=[
        SentryDeduplicateIntegration(redis_factory=redis.Redis),
    ],
)
```

The `redis_factory` arg is any function returning a redis client.

For simple projects, it is possible to use it without a Redis instance, using
[fakeredis](https://pypi.org/project/fakeredis/), which is an in-memory
Redis compatible implementation. It will deduplicate only errors in the same
thread.

```python
import fakeredis
from sentry_deduplicate_integration import SentryDeduplicateIntegration

sentry_sdk.init(
    integrations=[
        SentryDeduplicateIntegration(redis_factory=fakeredis.FakeRedis),
    ],
)
```

## What about `sentry_sdk.DedupeIntegration`?

The [`DedupeIntegration`](https://docs.sentry.io/platforms/python/configuration/integrations/default-integrations/#deduplication)
is installed by default and we expected it to work, but just avoid duplications
when the same error is triggered twice, only the last error is checked for deduplication.
