import sys
import logging
from arxivdigest_recommenders import config


LOG_LEVELS = {
    "FATAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
}


def get_logger(name: str, prefix: str):
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(prefix)s - %(message)s"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(config.LOG_LEVEL, 20))
    logger.addHandler(handler)
    logger = logging.LoggerAdapter(logger, {"prefix": prefix})
    return logger
