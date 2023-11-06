from collections.abc import Callable
from .config import *
from .logging import *


def main(
    program: Callable,
    args: dict,
    cfg: dict,
    start_message: str = "Starting...",
) -> int:
    """CLI program."""
    # Start a screen logger that can handle error messages
    set_up_loggers()
    log = logging.getLogger(__name__)

    try:
        # Make sure that verbosity is within range and convert it into a string
        verbosity_names = tuple(VERBOSITY.keys())
        args["verbosity"] = verbosity_names[
            len(verbosity_names) - 1
            if args["verbosity"] + 2 > len(verbosity_names)
            else args["verbosity"] + 1
        ]

        # If an alternative configuration file is provided, use it instead of the standard one
        if args["alterative_config_file"]:
            args["config_file"] = args["alterative_config_file"]
        del args["alterative_config_file"]

        # Set up application settings and loggers
        cfg = set_up_config(cfg, args)
        set_up_loggers(cfg)

        # Run the application
        log.info(start_message)
        log.debug("Command line arguments: %s", sys.argv)
        program(cfg)

    except Exception as error:
        log.exception("An error occurred: %s", str(error))

        # Raise the exception to the terminal when debugging
        if cfg["verbosity"] == "DEBUG" or args["verbosity"] == "DEBUG":
            raise
        return 1

    log.info("All Ok!")
    return 0
