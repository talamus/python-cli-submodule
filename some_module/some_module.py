import logging
from . import *


def some_code(cfg: dict = None) -> list[str]:
    if cfg is None:
        cfg = dict(DEFAULT_CONFIG)

    log = logging.getLogger(__name__)

    log.debug("Configuration: %s", cfg)
    log.info("Running some code...")

    with open("Something that does not exist") as file:
        lines = file.readlines()

    log.info("All done!")
    return lines
