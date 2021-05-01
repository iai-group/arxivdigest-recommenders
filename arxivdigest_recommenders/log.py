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
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger.setLevel(LOG_LEVELS.get(config.LOG_LEVEL, 20))
