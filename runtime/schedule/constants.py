class ScheduleStatus:
    DRAFT = "DRAFT"
    STARTED = "STARTED"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    EXPIRED = "EXPIRED"
    DELETED = "DELETED"

    ALL = (
        DRAFT,
        STARTED,
        PAUSED,
        STOPPED,
        EXPIRED,
        DELETED,
    )


class ScheduleRunStatus:
    PENDING = "PENDING"
    DISPATCHING = "DISPATCHING"
    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    LOST = "LOST"

    ALL = (
        PENDING,
        DISPATCHING,
        SUBMITTED,
        RUNNING,
        SUCCESS,
        FAILED,
        CANCELLED,
        LOST,
    )


class TriggerType:
    ONCE = "ONCE"
    CRON = "CRON"
    INTERVAL = "INTERVAL"

    ALL = (
        ONCE,
        CRON,
        INTERVAL,
    )


class MisfirePolicy:
    SKIP = "SKIP"
    FIRE_ONCE = "FIRE_ONCE"
    CATCH_UP = "CATCH_UP"

    ALL = (
        SKIP,
        FIRE_ONCE,
        CATCH_UP,
    )


class ConcurrencyPolicy:
    SKIP_CURRENT = "SKIP_CURRENT"
    QUEUE_CURRENT = "QUEUE_CURRENT"
    FAIL_CURRENT = "FAIL_CURRENT"

    ALL = (
        SKIP_CURRENT,
        QUEUE_CURRENT,
        FAIL_CURRENT,
    )
