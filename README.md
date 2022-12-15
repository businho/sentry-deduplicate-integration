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
[redislite](https://pypi.org/project/redislite/), which is an in-memory
Redis compatible implementation. It will deduplicate only errors in the same
thread.

```python
import redislite
from sentry_deduplicate_integration import SentryDeduplicateIntegration

sentry_sdk.init(
    integrations=[
        SentryDeduplicateIntegration(redis_factory=redislite.Redis),
    ],
)
```
