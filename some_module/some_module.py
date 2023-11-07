import logging
from . import *


def some_code(filename = "Some filename", cfg: dict = None) -> list[str]:
    if cfg is None:
        cfg = dict(DEFAULT_CONFIG)

    log = logging.getLogger(__name__)

    log.info("Running some code...")

    log.debug("Configuration: %s", cfg)  # Old style
    log.debug("Configuration", extra={"cfg": cfg})  # Better for log integration
    log.debug("Configuration for %s", __name__, extra={"cfg": cfg})  # Combined

    with open(filename) as file:  # Will raise an exception...
        lines = file.readlines()

    log.info("All done!")
    return lines
