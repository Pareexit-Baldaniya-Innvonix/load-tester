import logging
from typing import Union
from .config import config
from pythonjsonlogger import jsonlogger

# Disabling uvicorn logging
uvicorn_error = logging.getLogger("uvicorn.error")
uvicorn_error.disabled = True
uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_access.disabled = True


def get_log_level(log_level: str) -> int:
    log_level = log_level.upper()
    if log_level == "CRITICAL":
        return logging.CRITICAL
    elif log_level == "ERROR":
        return logging.ERROR
    elif log_level == "WARNING":
        return logging.WARN
    elif log_level == "DEBUG":
        return logging.DEBUG
    return logging.INFO


def get_logger(
    logger_name: str = "", log_level: Union[str, None] = None
) -> logging.Logger:
    log_level = get_log_level(config.LOG_LEVEL)

    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    existing_handlers_in_logger = [x.name for x in logger.handlers]

    # Only enable json logging in non-dev environments
    if config.ENV != "DEV" and "json_handler" not in existing_handlers_in_logger:
        log_json = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(funcName)s"
        )
        log_json.set_name("json_handler")
        log_json.setFormatter(formatter)
        logger.addHandler(log_json)
    elif "stream_handler" not in existing_handlers_in_logger:
        # Check if stream_handler already exists or not
        log_stream = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        log_stream.set_name("stream_handler")
        log_stream.setFormatter(formatter)
        logger.addHandler(log_stream)

    return logger
