import sentry_sdk


def init(dsn):
    global _error_tracking_init

    sentry_sdk.init(dsn)
    _error_tracking_init = True


def capture(exception, labels={}):
    global _error_tracking_init

    if _error_tracking_init:
        with sentry_sdk.push_scope() as scope:
            for k, v in labels.items():
                scope.set_extra(k, v)
            sentry_sdk.capture_exception(exception)
