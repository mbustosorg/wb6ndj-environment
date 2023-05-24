import logging
import sys

DEFAULT_LEVEL = logging.INFO
FORMATTER = logging.Formatter(
    "%(asctime)s|%(process)d|%(module)s|%(levelname)s|%(message)s"
)
LOGGER = logging.getLogger()
LOGGER.setLevel(DEFAULT_LEVEL)
LOGGER.handlers = []
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(DEFAULT_LEVEL)
handler.setFormatter(FORMATTER)
LOGGER.addHandler(handler)
