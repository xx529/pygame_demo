import sys
from loguru import logger

SHORT_FORMAT = ('<green>[{time:HH:mm:ss.SSS}]</green> '
                '<red>[{extra[name]}]</red> '
                '{message}')


def init_log():
    logger.remove()
    log_format = SHORT_FORMAT
    logger.configure(handlers=[dict(sink=sys.stdout, enqueue=True, format=log_format, colorize=True, level='DEBUG')])


def get_logger(name='default'):
    return logger.bind(name=name)


def log_retry_attempt(retry_state):
    retry_logger = get_logger('retry')
    exception = retry_state.outcome.exception()
    if exception:
        retry_logger.error(f"Error occurred: {str(exception)} Retrying({retry_state.attempt_number})...")


def raise_last_exception(retry_state):
    if retry_state.outcome.failed:
        raise retry_state.outcome.exception()
    return retry_state.outcome.result()


logger = get_logger()
init_log()
