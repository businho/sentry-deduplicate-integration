# sentry-deduplicate-integration

Sentry integration to rate-limit duplicated errors, using redis to sync error
count and identify duplications.

Add the integration to your sentry_sdk initialization.

```python
import redis
from sentry_deduplicate_integration import SentryDeduplicateIntegration


sentry_sdk.init(
    integrations=[
        SentryDeduplicateIntegration(
            redis_factory=redis.Redis,
            max_events_per_minute=10,
        ),
    ],
)
```

The `redis_factory` arg is any function returning a redis client.
