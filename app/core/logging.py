import logging
import sys
from pythonjsonlogger import jsonlogger


def configure_logging(level: int = logging.INFO) -> None:
    logger = logging.getLogger()
    logger.setLevel(level)

    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    log_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(log_handler)
